"""Token budget kill switch (INFRA-06).

Phase 1 establishes only the *interface* — Phase 3 wires this into the
orchestrator's LLM call path. All later code must import TokenBudget from
this module.
"""

from __future__ import annotations

from dataclasses import dataclass

class TokenBudgetExceeded(Exception):
    """Raised when a token addition would push cumulative usage past the cap."""

@dataclass
class TokenBudget:
    """Tracks cumulative LLM token usage against a configurable cap.

    Phase 1: interface stub. Phase 3: wired into every LLM call so a
    runaway session is aborted before billing damage.
    """

    max_tokens: int
    _total: int = 0

    def add(self, tokens: int) -> bool:
        """Record `tokens` of usage. Raises TokenBudgetExceeded if cap would be passed.

        Returns True on success (call may proceed).
        """
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        if self._total + tokens > self.max_tokens:
            raise TokenBudgetExceeded(
                f"Token budget exceeded: {self._total + tokens} > {self.max_tokens}"
            )
        self._total += tokens
        return True

    @property
    def total(self) -> int:
        return self._total

    @property
    def remaining(self) -> int:
        return self.max_tokens - self._total
