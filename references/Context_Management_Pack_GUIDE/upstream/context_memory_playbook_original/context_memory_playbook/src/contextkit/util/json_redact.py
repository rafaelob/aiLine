from __future__ import annotations

import re
from typing import Any


# Padrões mínimos (não exaustivos). Ajuste conforme seu domínio e compliance.
DEFAULT_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                 # OpenAI-style
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),             # Google API key-style
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-\._~\+\/]+=*"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?"),
]

DEFAULT_PII_PATTERNS = [
    re.compile(r"(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"),  # email
    re.compile(r"\+?\d[\d\s\-().]{8,}\d"),                # phone-ish
]


def redact(obj: Any, patterns: list[re.Pattern] | None = None) -> Any:
    """Redige segredos/PII em estruturas (dict/list/str).

    - Intencionalmente simples (sem depender de libs externas).
    - Não substitui um classificador de PII de verdade.
    """
    pats = patterns or (DEFAULT_SECRET_PATTERNS + DEFAULT_PII_PATTERNS)

    if isinstance(obj, str):
        s = obj
        for p in pats:
            s = p.sub("[REDACTED]", s)
        return s
    if isinstance(obj, list):
        return [redact(x, pats) for x in obj]
    if isinstance(obj, dict):
        return {k: redact(v, pats) for k, v in obj.items()}
    return obj
