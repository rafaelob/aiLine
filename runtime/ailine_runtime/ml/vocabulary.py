"""Libras sign language vocabulary for MVP recognition.

Contains ~30 common Libras glosses suitable for classroom interaction,
plus CTC special tokens (blank and transition).
"""

from __future__ import annotations

# CTC special tokens
BLANK_TOKEN: int = 0
TRANSITION_TOKEN: int = 1

# Vocabulary: gloss_id -> gloss_label
# IDs start at 2 (0=blank, 1=transition)
LIBRAS_VOCABULARY: dict[int, str] = {
    2: "OI",
    3: "TUDO-BEM",
    4: "OBRIGADO",
    5: "POR-FAVOR",
    6: "SIM",
    7: "NAO",
    8: "EU",
    9: "VOCE",
    10: "CASA",
    11: "ESCOLA",
    12: "PROFESSOR",
    13: "ALUNO",
    14: "ESTUDAR",
    15: "APRENDER",
    16: "AJUDA",
    17: "ENTENDER",
    18: "GOSTAR",
    19: "QUERER",
    20: "PRECISAR",
    21: "DESCULPA",
    22: "BOM",
    23: "MAU",
    24: "GRANDE",
    25: "PEQUENO",
    26: "HOJE",
    27: "AMANHA",
    28: "ONTEM",
    29: "NUMERO",
    30: "NOME",
    31: "AGUA",
}

# Reverse mapping: gloss_label -> gloss_id
LABEL_TO_ID: dict[str, int] = {v: k for k, v in LIBRAS_VOCABULARY.items()}

# Total vocabulary size including special tokens
VOCAB_SIZE: int = len(LIBRAS_VOCABULARY) + 2  # +blank +transition
