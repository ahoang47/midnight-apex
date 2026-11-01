from __future__ import annotations
"""Structured execution trace logger.

Collects timestamped log entries during combat resolution for
post-match analysis, debugging, and replay.
"""


class TraceLogger:
    """Append-only log of named values organised by category."""

    def __init__(self) -> None:
        self.entries: list[dict] = []

    def log(self, category: str, label: str, value: object, formula: str = "") -> None:
        """Record a single log entry.

        Args:
            category: Grouping key (e.g. 'damage', 'clash')
            label: Human-readable name for this value
            value: The computed value (int, float, str, etc.)
            formula: Optional formula string showing how value was derived
        """
        self.entries.append({
            "category": category,
            "label": label,
            "value": value,
            "formula": formula,
        })

    def clear(self) -> None:
        """Remove all entries from the log."""
        self.entries.clear()

    def get_by_category(self, category: str) -> list[dict]:
        """Return all entries matching *category*."""
        return [e for e in self.entries if e["category"] == category]

    def all(self) -> list[dict]:
        """Return a copy of every entry."""
        return list(self.entries)
