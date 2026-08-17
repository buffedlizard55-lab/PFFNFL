"""
pff_data

Typed, provenance-aware data models and helpers for PFF data
intended as a reliable source for NFL prediction backtesting.
"""

from .models import (
    PFFProvenance,
    PFFPlayerRoster,
    PFFLineupSnapshot,
    PFFCollectionRun,
)

__all__ = [
    "PFFProvenance",
    "PFFPlayerRoster",
    "PFFLineupSnapshot",
    "PFFCollectionRun",
]
