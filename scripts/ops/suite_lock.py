#!/usr/bin/env python3
# FLEET-TEMPLATE v2026.07.67 — instalado por fleet_install.py; fonte: ~/.claude/fleet-template/
"""TRAVA DE SUÍTE COM DONO DECLARADO — mkdir-lock que diz de QUEM ele é.

POR QUE EXISTE (campo, 2026-08-01; LESSONS.md §2). A suíte da frota roda EXCLUSIVA: duas
suítes concorrentes sobem servidores e escrevem arquivos uma por cima da outra, e o
vermelho resultante é falso. A trava de sempre é um `mkdir` — atômico, portátil, sem
dependência. O que faltava era o DONO: um `mkdir` vazio não distingue

    "a suíte de alguém está rodando há 25 minutos, legitimamente"
        de
    "alguém morreu e deixou o diretório para trás",

e as duas leituras pedem AÇÕES OPOSTAS. Hoje um hold LEGÍTIMO de 25 min foi lido como
órfão e removido por baixo de quem o segurava. Trava cuja falha é indistinguível de saúde
é o padrão-mestre desta casa; aqui ele custou uma suíte.

VEREDITO TRINO, e o terceiro estado é o ponto:

    LIVRE     o diretório não existe                      -> pode adquirir
    VIVO      owner.json legível e PID vivo               -> ESPERE
    ORFAO     owner.json legível e PID morto              -> takeover DOCUMENTADO
    SUSPEITO  diretório sem owner.json legível            -> COORDENE, não aja

`SUSPEITO` nunca vira `LIVRE`. É o estado que existe justamente para que a incerteza não
seja resolvida sozinha na direção conveniente — que é como o incidente aconteceu. Ele
cobre também a janela real de milissegundos entre vencer o `mkdir` e escrever o
`owner.json`: quem inspecionar no meio dela vê `SUSPEITO`, e `SUSPEITO` não autoriza nada.

SONDA DE PID: NUNCA `os.kill(pid, 0)` no Windows — lá o CPython mapeia o sinal para
``TerminateProcess`` e a sonda MATA o processo sondado (lição da casa, medida). A sonda
canônica é `OpenProcess` + estado do objeto, e ela tem UMA casa nesta árvore
(`_fleet_lock._pid_alive`); aqui ela é IMPORTADA, nunca recopiada — duas cópias de uma
regra divergem no dia em que alguém corrige uma delas.

ARMADILHA MEDIDA (Git Bash): `$$` NÃO é um PID do Windows — é o PID MSYS do shell, e a
sonda o lê como morto, corretamente. Um hold declarado com `--pid $$` nasce ÓRFÃO. Em
Git Bash use o PID Windows real (`python -c "import os;print(os.getpid())"` do processo
que fica de pé), ou prefira `rodar`, que segura a trava com o próprio processo.

USO:
  suite_lock.py adquirir  --lock <dir> [--agent X] [--pid N] [--espera 1200] [--intervalo 30]
  suite_lock.py inspecionar --lock <dir> [--json]
  suite_lock.py liberar   --lock <dir> [--force]
  suite_lock.py rodar     --lock <dir> [--espera 1200] -- <comando...>

Em Python:
  from suite_lock import TravaDeSuite, inspecionar
  with TravaDeSuite(dir, agente="A", espera=1200):
      ...
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fleet_lock import _pid_alive  # noqa: E402  — a sonda tem UMA casa

LIVRE = "LIVRE"
VIVO = "VIVO"
ORFAO = "ORFAO"
SUSPEITO = "SUSPEITO"

OWNER = "owner.json"
TAKEOVERS = "takeovers.log"
# Claim de takeover: serializa disputantes do MESMO órfão (O_EXCL, um vencedor só).
CLAIM = "takeover.claim"

# rc do CLI. Números DISTINTOS de propósito: "não consegui a trava" e "o comando que rodei
# sob a trava falhou" pedem ações opostas, e colapsá-los num rc 1 é como um wrapper mente.
RC_NAO_ADQUIRIU = 3
RC_SUSPEITO = 4


def _agora() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _agente_padrao(explicito: str | None = None) -> str:
    return (explicito or os.environ.get("FLEET_AGENT_ID") or "?").strip() or "?"


class Veredito:
    __slots__ = ("estado", "dono", "motivo", "lock")

    def __init__(self, estado: str, lock: Path, dono: dict | None = None, motivo: str = ""):
        self.estado, self.lock, self.dono, self.motivo = estado, Path(lock), dono, motivo

    @property
    def pode_adquirir(self) -> bool:
        """Só dois estados autorizam agir. `SUSPEITO` fica de fora POR DESENHO: é o
        estado inteiro da lição — incerteza não se resolve sozinha para o lado cômodo."""
        return self.estado in (LIVRE, ORFAO)

    def como_dict(self) -> dict:
        return {"estado": self.estado, "lock": str(self.lock), "dono": self.dono,
                "motivo": self.motivo}

    def __str__(self) -> str:
        d = self.dono or {}
        quem = (f" dono={d.get('agent', '?')} pid={d.get('pid', '?')} "
                f"desde={d.get('timestamp', '?')}") if d else ""
        return f"{self.estado} {self.lock}{quem}" + (f" — {self.motivo}" if self.motivo else "")


def _ler_dono(lock: Path) -> tuple[dict | None, str]:
    """``(dono, motivo)``. ``dono is None`` SEMPRE vem com motivo: dono ilegível que não
    explica por que é indistinguível de dono ausente por bug."""
    alvo = lock / OWNER
    try:
        bruto = alvo.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, (f"{OWNER} ausente — trava criada por outra ferramenta, ou alguém "
                      f"vencendo o mkdir neste instante")
    except OSError as exc:
        return None, f"{OWNER} ilegível ({exc.__class__.__name__})"
    try:
        dono = json.loads(bruto)
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"{OWNER} não é JSON válido ({exc})"
    if not isinstance(dono, dict) or not isinstance(dono.get("pid"), int):
        return None, f"{OWNER} sem campo `pid` inteiro"
    return dono, ""


def inspecionar(lock) -> Veredito:
    """O veredito trino. NÃO muta nada — inspecionar uma trava jamais pode alterá-la."""
    lock = Path(lock)
    if not lock.exists():
        return Veredito(LIVRE, lock)
    if not lock.is_dir():
        return Veredito(SUSPEITO, lock, motivo="o caminho existe e NÃO é diretório")
    dono, motivo = _ler_dono(lock)
    if dono is None:
        return Veredito(SUSPEITO, lock, motivo=motivo)
    if _pid_alive(int(dono["pid"])):
        return Veredito(VIVO, lock, dono, "PID vivo — hold legítimo, ESPERE (uma suíte "
                                          "longa é normal; 25 min já aconteceu em campo)")
    return Veredito(ORFAO, lock, dono, f"PID {dono['pid']} morto — takeover permitido, e "
                                       f"ele fica registrado em {TAKEOVERS}")


def _escrever_dono(lock: Path, agente: str, substituido: dict | None, pid: int) -> dict:
    dono = {"agent": _agente_padrao(agente), "pid": int(pid), "timestamp": _agora(),
            "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "?"}
    if substituido:
        dono["substituiu"] = {k: substituido.get(k) for k in ("agent", "pid", "timestamp")}
    tmp = lock / (OWNER + ".tmp")
    tmp.write_text(json.dumps(dono, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, lock / OWNER)
    return dono


class NaoAdquirida(RuntimeError):
    """Não deu para pegar a trava dentro do prazo. Carrega o VEREDITO — quem chama precisa
    saber se esperou um vivo (normal) ou empacou num suspeito (pede coordenação humana)."""

    def __init__(self, veredito: Veredito, espera: float):
        super().__init__(f"trava não adquirida em {espera:g}s: {veredito}")
        self.veredito = veredito


class TravaDeSuite:
    """Context manager. ``adquirir`` só toma a trava por `LIVRE` ou por takeover de
    `ORFAO`; em `VIVO` e `SUSPEITO` ele ESPERA até o prazo e desiste dizendo qual dos dois
    era — porque as ações seguintes são diferentes (voltar depois vs. chamar alguém)."""

    def __init__(self, lock, agente: str | None = None, espera: float = 1200.0,
                 intervalo: float = 30.0, verboso: bool = True, pid: int | None = None):
        self.lock = Path(lock)
        self.agente = _agente_padrao(agente)
        self.espera, self.intervalo, self.verboso = float(espera), float(intervalo), verboso
        # PID DECLARADO, e o default é o óbvio. Existe porque um hold que atravessa VÁRIOS
        # comandos (o caso do agente: adquire, roda a suíte, libera — três chamadas) não
        # pode ser assinado pelo processo que só escreveu o arquivo e morreu: a inspeção
        # seguinte leria ÓRFÃO com razão, e o takeover seria correto sobre um hold vivo.
        # Quem segura por fora declara o PID que fica de pé.
        self.pid = int(pid or os.getpid())
        self.dono: dict | None = None
        self._ultimo = ""

    def _diz(self, msg: str) -> None:
        if self.verboso and msg != self._ultimo:
            self._ultimo = msg
            print(f"suite_lock: {msg}", file=sys.stderr)

    def _tentar(self) -> Veredito | None:
        """``None`` = adquirida. Caso contrário, o veredito que impediu."""
        v = inspecionar(self.lock)
        if v.estado == ORFAO:
            return self._takeover(v)
        if v.estado != LIVRE:
            return v
        try:
            self.lock.mkdir(parents=True)
        except FileExistsError:
            return inspecionar(self.lock)     # perdeu a corrida entre o teste e o mkdir
        except OSError as exc:
            return Veredito(SUSPEITO, self.lock, motivo=f"mkdir falhou ({exc})")
        # IMEDIATAMENTE após vencer o mkdir. Todo instante entre um e outro é janela em que
        # a trava existe sem dono — e é essa janela que o incidente transformou em "órfão".
        self.dono = _escrever_dono(self.lock, self.agente, None, self.pid)
        return None

    def _takeover(self, v: Veredito) -> Veredito | None:
        """Assume uma trava ÓRFÃ. ``None`` = assumida; senão, o veredito que impediu.

        SERIALIZADO por um arquivo de claim criado com ``O_EXCL`` — atômico, exatamente um
        vencedor. A versão anterior só sobrescrevia o ``owner.json``, e dois processos que
        vissem o MESMO órfão saíam AMBOS achando que seguravam a trava: trava que pode ser
        segurada duas vezes é pior que trava nenhuma, porque some o vermelho falso da suíte
        concorrente e fica a certeza infundada de exclusividade. (Aposentar o diretório com
        ``os.rename`` também não serve, e isto foi MEDIDO: o rename é atômico mas não é
        CONDICIONAL, então o segundo disputante levava embora a trava VIVA que o primeiro
        acabara de criar no mesmo caminho.)

        Vencido o claim, o estado é RECONFERIDO antes de escrever: só se ainda for o MESMO
        morto o takeover acontece. Claim órfão (processo que morreu no meio) faz as
        tentativas seguintes ESPERAREM até o prazo e recusarem — falha para o lado fechado.
        """
        claim = self.lock / CLAIM
        try:
            fd = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return Veredito(SUSPEITO, self.lock,
                            motivo="takeover de outro disputante em curso (claim aberto)")
        except OSError as exc:
            return Veredito(SUSPEITO, self.lock, motivo=f"claim de takeover falhou ({exc})")
        try:
            with contextlib.suppress(OSError):
                os.write(fd, f"{self.agente} pid={self.pid} {_agora()}\n".encode())
            os.close(fd)
            atual = inspecionar(self.lock)
            if atual.estado != ORFAO or atual.dono != v.dono:
                return atual        # virou outra trava entre o veredito e o claim
            with contextlib.suppress(OSError):
                with (self.lock / TAKEOVERS).open("a", encoding="utf-8") as fh:
                    fh.write(f"{_agora()} {self.agente} pid={self.pid} assumiu de "
                             f"{(v.dono or {}).get('agent', '?')} "
                             f"pid={(v.dono or {}).get('pid', '?')} "
                             f"(desde {(v.dono or {}).get('timestamp', '?')})\n")
            self.dono = _escrever_dono(self.lock, self.agente, v.dono, self.pid)
            self._diz(f"takeover de trava ÓRFÃ ({v.motivo}) — registrado em {TAKEOVERS}")
            return None
        finally:
            with contextlib.suppress(OSError):
                claim.unlink()

    def adquirir(self) -> "TravaDeSuite":
        limite = time.monotonic() + self.espera
        while True:
            impedimento = self._tentar()
            if impedimento is None:
                return self
            if time.monotonic() >= limite:
                raise NaoAdquirida(impedimento, self.espera)
            self._diz(f"{impedimento} — aguardando (até {self.espera:g}s)")
            time.sleep(min(self.intervalo, max(0.05, limite - time.monotonic())))

    def liberar(self) -> None:
        """Solta SÓ a própria trava: confere o PID no owner.json antes de remover. Sem essa
        conferência, um `liberar` atrasado apagaria a trava de quem veio depois."""
        dono, _ = _ler_dono(self.lock)
        if dono is not None and dono.get("pid") != self.pid:
            self._diz(f"NÃO liberei: a trava agora é de pid={dono.get('pid')} "
                      f"({dono.get('agent')}) — nada tocado")
            return
        with contextlib.suppress(OSError):
            (self.lock / OWNER).unlink()
        with contextlib.suppress(OSError):
            (self.lock / (OWNER + ".tmp")).unlink()
        try:
            self.lock.rmdir()
        except OSError as exc:
            # Diretório não-vazio (takeovers.log) é o caso normal do takeover: some o dono,
            # e a próxima inspeção lê SUSPEITO — nunca LIVRE. Dizer isso é o mínimo.
            self._diz(f"trava não removida por completo ({exc}) — a próxima inspeção lerá "
                      f"{SUSPEITO} até alguém limpar {self.lock}")

    def __enter__(self) -> "TravaDeSuite":
        return self.adquirir()

    def __exit__(self, *_exc: object) -> None:
        self.liberar()


# --- CLI ----------------------------------------------------------------------

def main(argv=None) -> int:
    # Diagnóstico acentuado num cano cp1252 (o padrão desta máquina) sai mutilado — e
    # mensagem mutilada é mensagem que o operador não lê. `errors="replace"` é EXPLÍCITO:
    # `reconfigure(encoding=...)` sem ele reseta o handler para `strict` (lição da casa),
    # e aí a linha de aviso vira UnicodeEncodeError dentro de uma trava.
    for fluxo in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for nome in ("adquirir", "inspecionar", "liberar", "rodar"):
        s = sub.add_parser(nome)
        s.add_argument("--lock", required=True)
        s.add_argument("--json", action="store_true")
        if nome in ("adquirir", "rodar"):
            s.add_argument("--agent", default=None)
            s.add_argument("--espera", type=float, default=1200.0)
            s.add_argument("--intervalo", type=float, default=30.0)
        if nome in ("adquirir", "liberar"):
            s.add_argument("--pid", type=int, default=None,
                           help="PID que SEGURA a trava enquanto ela existir. Num hold que "
                                "atravessa vários comandos, declare o PID da sessão que "
                                "fica de pé — senão a próxima inspeção lê ÓRFÃO com razão.")
        if nome == "liberar":
            s.add_argument("--force", action="store_true",
                           help="remove a trava mesmo sem ser o dono (ato MANUAL e declarado)")
        if nome == "rodar":
            s.add_argument("comando", nargs=argparse.REMAINDER)
    a = p.parse_args(argv)
    lock = Path(a.lock)

    if a.cmd == "inspecionar":
        v = inspecionar(lock)
        print(json.dumps(v.como_dict(), ensure_ascii=False) if a.json else str(v))
        return 0 if v.estado in (LIVRE, VIVO, ORFAO) else RC_SUSPEITO

    if a.cmd == "liberar":
        if a.force:
            import shutil
            shutil.rmtree(lock, ignore_errors=True)
            print(f"suite_lock: trava REMOVIDA à força: {lock}", file=sys.stderr)
            return 0
        t = TravaDeSuite(lock, pid=a.pid)
        t.liberar()
        return 0

    t = TravaDeSuite(lock, a.agent, a.espera, a.intervalo,
                     pid=getattr(a, "pid", None))
    if a.cmd == "adquirir" and not getattr(a, "pid", None):
        print(f"suite_lock: sem --pid, o dono é ESTE processo ({os.getpid()}), que morre ao "
              f"fim deste comando — a próxima inspeção lerá ÓRFÃO. Para um hold que "
              f"atravessa comandos, passe --pid <sessão viva>; para um hold de um comando "
              f"só, use `rodar`.", file=sys.stderr)
    try:
        t.adquirir()
    except NaoAdquirida as exc:
        print(f"suite_lock: {exc}", file=sys.stderr)
        return RC_SUSPEITO if exc.veredito.estado == SUSPEITO else RC_NAO_ADQUIRIU
    if a.cmd == "adquirir":
        print(json.dumps(t.dono, ensure_ascii=False) if a.json
              else f"suite_lock: adquirida {lock} por {t.dono}")
        return 0
    cmd = [c for c in (a.comando or []) if c != "--"]
    if not cmd:
        t.liberar()
        print("suite_lock: `rodar` sem comando — nada a fazer.", file=sys.stderr)
        return 2
    try:
        return subprocess.run(cmd).returncode
    finally:
        t.liberar()


if __name__ == "__main__":
    raise SystemExit(main())
