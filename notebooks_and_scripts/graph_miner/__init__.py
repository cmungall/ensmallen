"""Submodule to automatically generated graph methods for graph retrieval."""
from .repositories import (JAXGraphRepository, KGHubGraphRepository,
                           KGOBOGraphRepository, LINQSGraphRepository,
                           MonarchInitiativeGraphRepository,
                           NetworkRepositoryGraphRepository,
                           PheKnowLatorKGGraphrepository,
                           StringGraphRepository, YueGraphRepository,
                           FreebaseGraphRepository,
                           ZenodoGraphRepository, WikiDataGraphRepository,
                           WikipediaGraphRepository, CTDGraphRepository)

__all__ = [
    "StringGraphRepository",
    "NetworkRepositoryGraphRepository",
    "KGHubGraphRepository",
    "YueGraphRepository",
    "LINQSGraphRepository",
    "MonarchInitiativeGraphRepository",
    "ZenodoGraphRepository",
    "PheKnowLatorKGGraphrepository",
    "JAXGraphRepository",
    "KGOBOGraphRepository",
    "WikiDataGraphRepository",
    "FreebaseGraphRepository",
    "WikipediaGraphRepository",
    "CTDGraphRepository"
]
