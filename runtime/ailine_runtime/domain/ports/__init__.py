"""Domain ports -- protocol interfaces for infrastructure adapters."""

from .curriculum import CurriculumProvider
from .db import Repository, UnitOfWork
from .embeddings import Embeddings
from .events import EventBus
from .llm import ChatLLM
from .media import STT, TTS, ImageDescriber, SignRecognition
from .storage import ObjectStorage
from .vectorstore import VectorSearchResult, VectorStore

__all__ = [
    "STT",
    "TTS",
    "ChatLLM",
    "CurriculumProvider",
    "Embeddings",
    "EventBus",
    "ImageDescriber",
    "ObjectStorage",
    "Repository",
    "SignRecognition",
    "UnitOfWork",
    "VectorSearchResult",
    "VectorStore",
]
