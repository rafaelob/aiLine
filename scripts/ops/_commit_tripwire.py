#!/usr/bin/env python3
# FLEET-TEMPLATE v2026.07.67 — instalado por fleet_install.py; fonte: ~/.claude/fleet-template/
"""TRIPWIRE DE MOCK — mecanismo 3 da rampa anti-entrega-mockada (SPEC v67).

O QUE ELE MEDE, E O QUE ELE NÃO MEDE. Ele lê as linhas ADICIONADAS de um commit e
aponta as que têm APARÊNCIA de entrega simulada — retorno cravado, `NotImplementedError`
solto, tarefa que promete trocar o mock depois, latência fingida, dado fabricado, teste
desligado sem motivo. Isso é um SINAL, no mesmo sentido do `MACHINE_SIGNAL` do v63: não
prova que a entrega é mock (uma fixture chamada `fake_`+algo é legítima), e sobretudo NÃO prova
que uma entrega sem achado é real. Chamar isto de prova seria o antipadrão-mestre da casa
— controle cuja falha é indistinguível de saúde — dentro do controle criado contra ele.

DOIS SÍTIOS, PELA MESMA RAZÃO DO PORTÃO DE COMMIT:
  * `fleet_commit.py` — o chokepoint. Recusa CEDO, com a mensagem boa, antes de a ref
    andar. É onde o autor ainda tem o contexto na cabeça;
  * `commit_gate.py hook-reference-transaction` — a barreira. Pega o `git commit` cru e
    o `git commit --no-verify` (que pula o `pre-commit` e NÃO pula o
    `reference-transaction`). Sem ela o tripwire seria opcional, e o algoritmo certo
    opcional perde para o errado default (41-84% de bypass medido em 2026-07-27).
  Commit que já passou pelo chokepoint NÃO é varrido duas vezes: o nonce do
  `fleet_commit` identifica a origem, e aviso repetido é aviso que o parque aprende a
  ignorar.

RAMPA: `FLEET_TRIPWIRE_MOCK=aviso` (default) `|bloqueio|off`. Valor desconhecido cai em
`aviso` AVISANDO — nunca em desligado silencioso, que é o único desfecho que transforma
erro de digitação em controle morto sem ninguém saber. O flip para `bloqueio` é decisão
futura, com a medição de campo na mão.

ESCAPE FAIL-CLOSED: `# FLEET-STUB: <motivo> · <row-id> · <prazo AAAA-MM-DD>` na própria
linha ou na imediatamente anterior (`//` e `<!--` também servem — o marcador é o texto,
não o comentário). Os TRÊS campos são obrigatórios: marcador incompleto é tratado como
AUSENTE e o porquê é dito. Um escape que aceita "quase certo" é um escape que qualquer
linha consegue, e aí o tripwire vira enfeite. Prazo VENCIDO acusa na mesma passada — a
dívida declarada com data é a única que alguém consegue cobrar.

ORÇAMENTO DA CLASSE CERTA: O(diff), nunca O(árvore). Teto DECLARADO de 4.000 linhas
adicionadas por commit; acima disso a varredura para, a contagem sai com `4000+` e os
arquivos que ficaram de fora são NOMEADOS. Lição paga em campo: orçamento da classe
errada é fail-open silencioso (o `T_QUICK` O(1) sobre um `git add` O(árvore) pulou a
varredura de segredos inteira).

INDISPONIBILIDADE NUNCA VIRA VERDE: git ausente, diff ilegível ou estouro de orçamento
saem como `indisponivel=<motivo>`, e quem consome imprime isso em vez de silêncio.
"""
from __future__ import annotations

import datetime as _dt
import os
import re
import subprocess
import sys
from collections import deque

ENV = "FLEET_TRIPWIRE_MOCK"
MODOS = ("aviso", "bloqueio", "off")
PADRAO_DE_MODO = "aviso"

# Teto DECLARADO da varredura (SPEC v67). 4.000 linhas adicionadas cobrem com folga o
# commit humano/agente típico; o que passa disso é quase sempre import de vendor, dump ou
# geração — exatamente o caso em que varrer padrão de mock não diz nada e custa caro.
TETO_ADICIONADAS = 4000
# Teto ABSOLUTO de leitura do diff. Depois do teto de varredura o parser continua CONTANDO
# (barato: sem regex), mas contar 40 milhões de linhas de um dump também é um orçamento —
# e um orçamento que não existe é o que vira travamento anunciado como saúde.
TETO_LINHAS_DE_DIFF = 400_000
TIMEOUT_GIT_S = 30.0

# --- padrões (lista DECLARADA; cada um tem teste que o exercita sozinho) -------
#
# ESCOPO por padrão, e a assimetria é a decisão de desenho. Mock em TESTE é legítimo —
# é onde ele deve morar. Acusar um `fake_`+algo dentro de `tests/` faria isto disparar
# em todo commit de teste do parque, e aviso que dispara sempre deixa de ser aviso: some
# no ruído levando junto os que importam. Já um `skip` de pytest sem motivo é o oposto —
# só existe em teste, e é exatamente ali que ele esconde entrega não feita.
ESCOPO_PRODUCAO = "producao"   # pula caminho de teste
ESCOPO_TODOS = "todos"

# Vocabulário de mock, isolado numa constante DE PROPÓSITO: junto com a marca de tarefa
# na mesma linha física, o arquivo casaria o próprio padrão e o tripwire acusaria a si
# mesmo. Gate que reprova a própria fonte é gate que ensina o parque a ignorá-lo.
_PALAVRA_DE_MOCK = r"(?:mock\w*|stubs?|fakes?|placeholder|dummy|lorem)"
# MAIÚSCULA obrigatória, e isto não é estilo: este parque escreve em português, onde
# "todo" é palavra comum ("todo commit", "todo agente"). Um `TODO` case-insensitive
# casaria prosa portuguesa a 120 caracteres de distância de qualquer "mock" e o padrão
# viraria gerador de ruído.
_MARCA_DE_TAREFA = r"\b(?:TODO|FIXME|HACK|XXX)\b"
_COMENTARIO = r"(?:#|//|/\*|<!--|--)"
# Comentário que confessa que o retorno é provisório. O padrão exige o retorno E a
# confissão: `return True` sozinho é código legítimo na esmagadora maioria das vezes, e
# um padrão que o acusasse seria desligado no primeiro dia.
_CONFISSAO = (r"(?:sempre|always|mock\w*|stub|fake|placeholder|dummy|hard-?cod\w*|"
              r"cravad\w+|chumbad\w+|tempor[aá]ri\w*|por enquanto|provis[oó]ri\w*|fixo)")
# Valor LITERAL — o que faz um retorno ser "cravado". Uma expressão sobre variáveis é
# decisão de runtime, por mais que o comentário ao lado fale de placeholder.
_LITERAL = (r"(?:true|false|none|null|nil|undefined|nan|\[\s*\]|\{\s*\}|\"\"|''|"
            r"-?\d+(?:\.\d+)?|\"[^\"\r\n]*\"|'[^'\r\n]*')")


class Padrao:
    """Um padrão da lista v1. ``excecao`` recebe (linha, contexto) e devolve True quando
    aquele caso NÃO é achado — o lugar onde mora a diferença entre `NotImplementedError`
    de método abstrato (legítimo, é contrato) e o mesmo raise solto no meio de um serviço."""

    __slots__ = ("nome", "regex", "escopo", "conserto", "excecao")

    def __init__(self, nome, regex, escopo, conserto, excecao=None):
        self.nome, self.regex, self.escopo = nome, regex, escopo
        self.conserto, self.excecao = conserto, excecao


_ABSTRATO_RE = re.compile(
    r"@(?:abc\.)?abstractmethod|@(?:typing\.)?overload|\bABC\b|\bABCMeta\b|\bProtocol\b|"
    r"@abstractproperty|\braise NotImplementedError\b.*# *contrato",
    re.IGNORECASE,
)


def _tem_motivo(linha: str, _ctx: str) -> bool:
    """Isenta quando o `reason=` está na linha — e TAMBÉM quando a linha só ABRE a
    chamada. Medido no parque em 2026-08-01: um `skipif` aberto numa linha, com o
    `reason` na SEGUINTE, era acusado de skip sem motivo. Julgar uma decisão pela metade
    da frase é como um controle honesto produz achado falso."""
    if re.search(r"\breason\s*=", linha):
        return True
    return linha.rstrip().endswith(("(", ","))


def _perto_de_abstrato(_linha: str, contexto: str) -> bool:
    return _ABSTRATO_RE.search(contexto) is not None


_GUARDA_COM_MOTIVO_RE = re.compile(r"\.skip\s*\([^\r\n]*,\s*['\"`][^'\"`\r\n]{3,}['\"`]\s*\)")
_CALLBACK_RE = re.compile(r"=>|\bfunction\b")


def _skip_js_e_guarda_declarada(linha: str, _ctx: str) -> bool:
    """Isenta a GUARDA condicional — `test.skip(!baseURL, 'BASE_URL not set')` — e a linha
    que só abre a chamada. MEDIDO no parque (2026-08-01): 128 dos 134 achados da amostra
    eram exatamente essa guarda, o equivalente JS do `skipif(cond, reason=...)`: ela declara
    a condição E o motivo, some do relatório como SKIPPED e não esconde entrega nenhuma. O
    que o padrão persegue é o teste DESLIGADO — o `skip` com callback e o `todo` —, que
    sai do verde sem sair do relatório de sucesso."""
    t = (linha or "").rstrip()
    if t.endswith(("(", ",")):
        return True
    return bool(_GUARDA_COM_MOTIVO_RE.search(t) and not _CALLBACK_RE.search(t))


PADROES = (
    Padrao(
        "retorno-cravado",
        # CRAVADO = valor LITERAL. Medido no parque (2026-08-01): a versão que aceitava
        # qualquer expressão acusava
        # `return (v && v !== "__FLEET_TOKEN__") ? v : null;  // placeholder => sem token`
        # — que é o PRÓPRIO payload deste template, condicional de verdade sobre um valor
        # de verdade, com um comentário que só explica o que o placeholder significa. Um
        # gate que acusa o próprio payload dispara em todo rollout do parque, e aviso que
        # dispara sempre deixa de ser aviso.
        re.compile(r"^\s*(?:return|yield)\b\s*(?i:" + _LITERAL + r")?\s*[;,]?\s*"
                   + _COMENTARIO + r"[^\r\n]*?(?i:" + _CONFISSAO + r")"),
        ESCOPO_PRODUCAO,
        "implemente o retorno ou marque a linha com FLEET-STUB (motivo · row · prazo)",
    ),
    Padrao(
        "nao-implementado",
        re.compile(r"\braise\s+NotImplementedError\b"),
        ESCOPO_PRODUCAO,
        "método abstrato é contrato e passa batido; raise solto em caminho vivo é entrega "
        "faltando — implemente ou declare FLEET-STUB",
        excecao=_perto_de_abstrato,
    ),
    Padrao(
        "tarefa-de-mock",
        re.compile(_MARCA_DE_TAREFA + r"[^\r\n]{0,120}?(?i:" + _PALAVRA_DE_MOCK + r")"),
        ESCOPO_TODOS,
        "a linha declara que o mock fica para depois — troque agora, ou converta a "
        "promessa em FLEET-STUB com row e prazo (que é cobrável)",
    ),
    Padrao(
        "latencia-fingida",
        # ATRASO LITERAL é o que separa latência fingida de espera legítima, e isto foi
        # MEDIDO no parque (2026-08-01): a versão que casava qualquer `setTimeout` dentro
        # de promessa acusava `setTimeout(r, pollIntervalFor(attempt))` e
        # `setTimeout(resolve, ms)` — polling com backoff e helper de sleep, código são,
        # 7 dos 20 achados da amostra. Espera calculada é decisão de runtime; espera com
        # número cravado é o idioma de fingir que uma integração demorou.
        re.compile(r"setTimeout\s*\(\s*(?:resolve|resolver|res|r|_|done)\s*,\s*\d+\s*\)|"
                   r"new Promise\s*\([^\r\n]{0,60}setTimeout\s*\([^\r\n]{0,30}?,\s*\d+\s*\)|"
                   r"(?:time|asyncio)\.sleep\([^\r\n]{0,40}\)[^\r\n]{0,60}?" + _COMENTARIO
                   + r"[^\r\n]{0,60}?(?i:" + _PALAVRA_DE_MOCK + r"|simula\w*)"),
        ESCOPO_PRODUCAO,
        "latência simulada esconde integração que não existe — ligue a integração real",
    ),
    Padrao(
        "dado-fabricado",
        # LIGAR um nome fabricado, não MENCIONAR um. Medido no parque (2026-08-01): a
        # versão que casava o identificador em qualquer posição acusou 6 linhas de
        # `audit_l3_distill_fidelity.py` — um script cujo ASSUNTO é citação fabricada
        # (`fake_quotes: int`, `f.fake_quotes > 0`, `"fabricadas": f.fake_quotes`).
        # Ler um campo chamado `fake_*` é vocabulário de domínio; o idioma da entrega
        # fingida é CHAMAR o fabricador ou LIGAR o nome a um valor. (Os dois exemplos
        # moram no teste de campo, não aqui: escritos nesta linha, este próprio comentário
        # viraria achado.) O olhar-para-trás recusa o acesso a atributo
        # (`f.fake_quotes`) e a vírgula final recusa o argumento nomeado em chamada
        # quebrada em linhas (`fake_quotes=fake,`) — passagem de valor, não fabricação.
        re.compile(r"(?<![.\w])(?:fake_[A-Za-z0-9_]+|dummy_[A-Za-z0-9_]+)\s*\(|"
                   r"^\s*(?:(?:const|let|var|val|final)\s+)?(?:self\.|this\.)?"
                   r"(?:fake_[A-Za-z0-9_]+|dummy_[A-Za-z0-9_]+)\s*=(?!=)[^\r\n]*"
                   r"(?<!,)\s*$|lorem[\s_-]?ipsum",
                   re.IGNORECASE),
        ESCOPO_PRODUCAO,
        "dado fabricado fora de teste vira demo que parece produto — busque o dado real",
    ),
    Padrao(
        "teste-pulado-sem-motivo",
        re.compile(r"@?pytest\.mark\.skip(?:if)?\b"),
        ESCOPO_TODOS,
        "teste pulado sem `reason=` é cobertura que sumiu em silêncio — declare o motivo "
        "(o `reason` aparece no relatório) ou reative o teste",
        excecao=_tem_motivo,
    ),
    Padrao(
        "teste-desligado-js",
        re.compile(r"\b(?:it|test|describe|context)\.(?:skip|todo)\s*\(|"
                   r"\bx(?:it|describe)\s*\("),
        ESCOPO_TODOS,
        "`it.skip`/`xit`/`test.todo` some do verde sem sumir do relatório de sucesso — "
        "reative ou declare FLEET-STUB com prazo",
        excecao=_skip_js_e_guarda_declarada,
    ),
)

# --- caminho de teste ---------------------------------------------------------
# Lista DECLARADA, casada por COMPONENTE de caminho (nunca por substring: `contests/`
# não é `tests/`, e um prefixo apodrece no primeiro rename).
_PARTES_DE_TESTE = frozenset((
    "test", "tests", "__tests__", "spec", "specs", "e2e", "testdata", "fixtures",
    "__mocks__", "cypress",
))
_BASENAME_DE_TESTE = re.compile(
    r"^(?:test_.*|conftest)\.py$|_test\.[a-z]+$|\.(?:test|spec)\.[a-z]+$", re.IGNORECASE)


# PROSA não é entrega. Documento que FALA de mock — esta spec, o AGENT_PROTOCOL, um
# relatório de pesquisa — não é entrega simulada, e varrê-lo faria o próprio manual do
# tripwire acusar o tripwire (medido: um `.md` de pesquisa do parque entrou na amostra por
# citar dado fabricado em prosa). Lista DECLARADA, não heurística: o preço é que um mock
# escondido dentro de um `.md` passa, e um mock que só existe num `.md` não roda.
_EXTENSOES_DE_PROSA = frozenset((".md", ".markdown", ".rst", ".txt", ".adoc", ".org"))


def _sufixo(path: str) -> str:
    base = (path or "").replace("\\", "/").rsplit("/", 1)[-1].lower()
    return base[base.rfind("."):] if "." in base else ""


def caminho_de_prosa(path: str) -> bool:
    return _sufixo(path) in _EXTENSOES_DE_PROSA


def caminho_de_teste(path: str) -> bool:
    partes = (path or "").replace("\\", "/").lower().split("/")
    if not _PARTES_DE_TESTE.isdisjoint(partes[:-1]):
        return True
    return bool(partes and _BASENAME_DE_TESTE.search(partes[-1]))


# --- escape FLEET-STUB (fail-closed) ------------------------------------------
# Separadores aceitos: `·` (canônico, é o que o protocolo documenta) e `|` (fallback
# ASCII, porque o console do Windows em cp1252 transforma digitar `·` em cerimônia — e
# cerimônia é o que faz um agente pular o escape e commitar sem marcador nenhum).
_MARCADOR_RE = re.compile(r"FLEET-STUB\s*:\s*(?P<corpo>[^\r\n]+)")
_SEPARADOR_RE = re.compile(r"\s*[·|]\s*")
_DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LIXO_DE_FIM = " \t*/-<!>#"
# MODELO, não promessa: a linha que ENSINA o marcador (no protocolo, no docstring, na
# mensagem de erro deste próprio arquivo) tem os campos em `<placeholder>`. Sem esta regra,
# documentar o escape acusaria "escape inválido" em toda linha de documentação — o gate
# reprovando o próprio manual. Não abre buraco: modelo NÃO isenta nada (é tratado como
# marcador AUSENTE), então uma linha suspeita "escapada" com placeholders segue acusada.
_PLACEHOLDER_RE = re.compile(r"^<[^<>]*>$")


def _dentro_de_literal(linha: str, pos: int) -> bool:
    """A ocorrência em ``pos`` está dentro de uma string/citação da linha?

    CITAR não é FAZER. Medido no próprio dogfood (2026-08-01): o primeiro commit do
    tripwire acusaria 6 linhas do seu PRÓPRIO teste — as constantes que DEFINEM os
    marcadores de exemplo (`_STUB = "# FLEET-STUB: …"`) e um docstring que fala de
    `pytest.mark.skip` entre crases. Gate que reprova a própria semente dispara em
    todo commit e é desligado na primeira semana.

    Heurística declarada e seu limite: conta aspas e crases ANTES da posição; número
    ímpar = dentro. Ela não entende string multilinha nem apóstrofo de prosa em inglês
    (`don't`), então pode calar um achado que venha DEPOIS de um apóstrofo na mesma
    linha. Cala pouco e por engano legível; o inverso — acusar toda documentação do
    próprio mecanismo — quebra o mecanismo.
    """
    trecho = linha[:pos]
    return any(trecho.count(q) % 2 for q in ('"', "'", "`"))


class Marcador:
    """Resultado da leitura de um marcador. ``valido`` é fail-closed: qualquer campo
    faltando devolve False COM ``motivo`` — o escape que não explica por que não valeu é
    indistinguível de escape ignorado por bug."""

    __slots__ = ("presente", "valido", "motivo", "row", "prazo", "vencido")

    def __init__(self, presente=False, valido=False, motivo="", row="", prazo=None,
                 vencido=False):
        self.presente, self.valido, self.motivo = presente, valido, motivo
        self.row, self.prazo, self.vencido = row, prazo, vencido


def ler_marcador(linha: str, hoje: _dt.date | None = None) -> Marcador:
    m = _MARCADOR_RE.search(linha or "")
    if not m:
        return Marcador()
    if _dentro_de_literal(linha, m.start()):
        return Marcador()                      # marcador CITADO dentro de string: exemplo
    corpo = m.group("corpo").rstrip(_LIXO_DE_FIM)
    campos = [c.strip() for c in _SEPARADOR_RE.split(corpo)]
    if any(_PLACEHOLDER_RE.match(c) for c in campos):
        return Marcador()                      # é o MODELO do marcador, não um marcador
    if len(campos) < 3:
        return Marcador(True, False,
                        f"marcador com {len(campos)} campo(s); exige 3 "
                        f"(<motivo> · <row-id> · <prazo AAAA-MM-DD>)")
    motivo, row, prazo_txt = campos[0], campos[1], campos[2]
    if not motivo:
        return Marcador(True, False, "marcador sem motivo")
    if not row:
        return Marcador(True, False, "marcador sem row-id")
    if not _DATA_RE.match(prazo_txt):
        return Marcador(True, False,
                        f"prazo {prazo_txt!r} não é AAAA-MM-DD", row=row)
    try:
        prazo = _dt.date.fromisoformat(prazo_txt)
    except ValueError:
        return Marcador(True, False, f"prazo {prazo_txt!r} não é data válida", row=row)
    hoje = hoje or _dt.date.today()
    return Marcador(True, True, "", row=row, prazo=prazo, vencido=prazo < hoje)


# --- leitura do diff ----------------------------------------------------------

class Achado:
    __slots__ = ("arquivo", "linha_no", "padrao", "texto", "nota")

    def __init__(self, arquivo, linha_no, padrao, texto, nota=""):
        self.arquivo, self.linha_no, self.padrao = arquivo, linha_no, padrao
        self.texto, self.nota = texto, nota

    def __str__(self) -> str:
        nota = f" [{self.nota}]" if self.nota else ""
        return f"{self.arquivo}:{self.linha_no} [{self.padrao}]{nota} {self.texto.strip()[:140]}"


class Resultado:
    __slots__ = ("achados", "adicionadas", "cortado", "nao_varridos", "indisponivel")

    def __init__(self, achados=None, adicionadas=0, cortado=False, nao_varridos=None,
                 indisponivel=""):
        self.achados = achados or []
        self.adicionadas = adicionadas
        self.cortado = cortado
        self.nao_varridos = nao_varridos or []
        self.indisponivel = indisponivel

    @property
    def total_txt(self) -> str:
        return f"{self.adicionadas}{'+' if self.cortado else ''}"


_CABECALHO_ARQUIVO_RE = re.compile(r"^\+\+\+ (?:b/)?(.+)$")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def avaliar_diff(texto: str, *, hoje: _dt.date | None = None,
                 teto: int = TETO_ADICIONADAS) -> Resultado:
    """Varre as linhas ADICIONADAS de um diff unificado. Puro: nada de git aqui, para que
    o teste possa exercitar cada padrão sem repo — e para que o parser seja o MESMO nos
    dois sítios (chokepoint e barreira), em vez de duas leituras que divergem com o tempo."""
    achados: list[Achado] = []
    adicionadas = 0
    cortado = False
    nao_varridos: list[str] = []
    arquivo = "?"
    prosa = False
    linha_no = 0
    contexto: deque[str] = deque(maxlen=6)
    anterior = ""
    for i, bruta in enumerate((texto or "").splitlines()):
        if i >= TETO_LINHAS_DE_DIFF:
            cortado = True
            if "<diff truncado>" not in nao_varridos:
                nao_varridos.append("<diff truncado>")
            break
        if bruta.startswith("+++"):
            m = _CABECALHO_ARQUIVO_RE.match(bruta)
            if m:
                arquivo = m.group(1).strip()
                if arquivo == "/dev/null":
                    arquivo = "?"
                prosa = caminho_de_prosa(arquivo)
                contexto.clear()
                anterior = ""
            continue
        if bruta.startswith("@@"):
            m = _HUNK_RE.match(bruta)
            if m:
                linha_no = int(m.group(1))
            contexto.clear()
            anterior = ""
            continue
        if bruta.startswith(("---", "diff --git", "index ", "old mode", "new mode",
                             "similarity index", "rename ", "Binary files", "\\ ")):
            continue
        if bruta.startswith("-"):
            continue
        if bruta.startswith(" "):
            texto_linha = bruta[1:]
            contexto.append(texto_linha)
            anterior = texto_linha
            linha_no += 1
            continue
        if not bruta.startswith("+"):
            continue
        texto_linha = bruta[1:]
        adicionadas += 1
        if adicionadas > teto:
            cortado = True
            if arquivo not in nao_varridos:
                nao_varridos.append(arquivo)
            linha_no += 1
            continue
        if not prosa:
            _julgar_linha(arquivo, linha_no, texto_linha, anterior, "\n".join(contexto),
                          hoje, achados)
        contexto.append(texto_linha)
        anterior = texto_linha
        linha_no += 1
    return Resultado(achados, adicionadas, cortado, nao_varridos)


def _julgar_linha(arquivo, linha_no, linha, anterior, contexto, hoje, achados) -> None:
    """A ordem importa e é declarada: primeiro lê-se o marcador, depois casa-se o padrão.
    Marcador VÁLIDO e no prazo cala o achado; marcador vencido ou quebrado NUNCA cala —
    só muda a mensagem.

    DOIS marcadores, e a distinção não é preciosismo: o da PRÓPRIA linha é o que responde
    por si (vencido/quebrado acusa AQUI, mesmo sem padrão casado); o da linha anterior só
    serve para ISENTAR um padrão casado. Sem essa separação, um marcador vencido acusava a
    linha seguinte também — e a linha seguinte podia ser um `@abstractmethod` inocente,
    que é o achado que não existe apontando para o lugar errado."""
    marc = ler_marcador(linha, hoje)
    isencao = marc if marc.presente else ler_marcador(anterior, hoje)
    de_teste = caminho_de_teste(arquivo)
    casou = None
    for p in PADROES:
        if p.escopo == ESCOPO_PRODUCAO and de_teste:
            continue
        m = p.regex.search(linha)
        if not m:
            continue
        if _dentro_de_literal(linha, m.start()):
            continue                           # o padrão foi CITADO (docstring, exemplo)
        if p.excecao is not None and p.excecao(linha, contexto + "\n" + linha):
            continue
        casou = p
        break
    if marc.presente and marc.valido and marc.vencido:
        achados.append(Achado(
            arquivo, linha_no, casou.nome if casou else "stub-vencido", linha,
            f"stub vencido desde {marc.prazo.isoformat()}, row {marc.row}"))
        return
    if marc.presente and not marc.valido:
        # O marcador quebrado é acusado MESMO sem padrão casado: um escape que não vale e
        # não avisa é um escape que o autor acha que tem. Fail-closed do escape só é
        # fail-closed se for audível.
        achados.append(Achado(
            arquivo, linha_no, casou.nome if casou else "escape-invalido", linha,
            f"escape ignorado ({marc.motivo})"))
        return
    if casou is None:
        return
    if isencao.presente and isencao.valido and not isencao.vencido:
        return
    nota = ("escape da linha anterior vencido em "
            f"{isencao.prazo.isoformat()}") if (isencao.presente and isencao.valido
                                                and isencao.vencido) else ""
    achados.append(Achado(arquivo, linha_no, casou.nome, linha, nota))


# --- produção do diff (os dois sítios) ----------------------------------------

def _git(cwd, *args, env=None):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=TIMEOUT_GIT_S,
                          env=env)


_ARGS_DIFF = ("-c", "core.quotepath=false", "diff", "--unified=3", "--no-color",
              "--no-ext-diff", "--no-renames", "--diff-filter=AM")


def diff_de_publicacao(cwd, antigo: str, novo: str) -> tuple[str, str]:
    """``(texto, indisponivel)`` para a barreira de ref: o commit JÁ existe, então o diff
    é o do par de commits. ``indisponivel`` não-vazio nunca pode ser lido como 'limpo'."""
    try:
        r = _git(cwd, *_ARGS_DIFF, antigo, novo)
    except (OSError, subprocess.SubprocessError) as exc:
        return "", f"git indisponível ({type(exc).__name__}: {str(exc)[:120]})"
    if r.returncode != 0:
        return "", f"git diff falhou (rc {r.returncode}): {(r.stderr or '').strip()[:160]}"
    return r.stdout, ""


def diff_do_indice(cwd, head: str, env=None) -> tuple[str, str]:
    """``(texto, indisponivel)`` para o chokepoint: o commit ainda NÃO existe, e o
    conteúdo verdadeiro é o do índice de freeze (onde arquivo NOVO já está estagiado —
    `git diff HEAD` cru não enxerga untracked e deixaria passar justamente o arquivo
    inteiro de mock recém-criado)."""
    try:
        r = _git(cwd, *_ARGS_DIFF, "--cached", head, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        return "", f"git indisponível ({type(exc).__name__}: {str(exc)[:120]})"
    if r.returncode != 0:
        return "", f"git diff --cached falhou (rc {r.returncode}): {(r.stderr or '').strip()[:160]}"
    return r.stdout, ""


# --- rampa e relato -----------------------------------------------------------

def modo(rotulo: str = "tripwire") -> str:
    bruto = (os.environ.get(ENV) or PADRAO_DE_MODO).strip().lower() or PADRAO_DE_MODO
    if bruto not in MODOS:
        print(f"AVISO {rotulo}: {ENV}={bruto!r} desconhecido (aceitos: "
              f"{', '.join(MODOS)}) — tratando como {PADRAO_DE_MODO!r}.", file=sys.stderr)
        return PADRAO_DE_MODO
    return bruto


MAX_LINHAS_NO_RELATO = 12


def relatar(res: Resultado, rotulo: str) -> str:
    """Uma linha por achado, arquivo:linha + padrão + o texto — o suficiente para o autor
    ir direto ao lugar. O carimbo sai SEMPRE que há o que dizer (achado, corte ou
    indisponibilidade); gate que só fala quando reclama é invisível quando saudável e
    ninguém nota quando ele morre."""
    partes = []
    if res.indisponivel:
        partes.append(f"{rotulo}: varredura de mock NÃO rodou ({res.indisponivel}) — "
                      f"indisponibilidade não é 'sem achado'.")
    if res.achados:
        cabeca = res.achados[:MAX_LINHAS_NO_RELATO]
        resto = len(res.achados) - len(cabeca)
        linhas = "\n".join(f"  {a}" for a in cabeca)
        consertos = sorted({p.conserto for p in PADROES
                            if p.nome in {a.padrao for a in cabeca}})
        partes.append(
            f"{rotulo}: {len(res.achados)} linha(s) adicionada(s) com cara de entrega "
            f"simulada (de {res.total_txt} adicionada(s)):\n{linhas}"
            + (f"\n  ... +{resto}" if resto > 0 else "")
            + ("\n  conserto: " + "; ".join(consertos) if consertos else "")
            + "\n  escape declarado: `# FLEET-STUB: <motivo> · <row-id> · <prazo AAAA-MM-DD>` "
              "na linha ou na anterior (os TRÊS campos, senão não vale).")
    if res.cortado:
        partes.append(
            f"{rotulo}: teto de {TETO_ADICIONADAS} linhas adicionadas atingido "
            f"({res.total_txt}) — NÃO varri: {', '.join(res.nao_varridos[:8])}"
            + (" ..." if len(res.nao_varridos) > 8 else ""))
    return "\n".join(partes)
