"""Unit tests for parliament.guards.TokenBudget (INFRA-06 interface contract)."""

import pytest

from parliament.guards import TokenBudget, TokenBudgetExceeded


def test_import_works():
    """Test 1: module is importable."""
    assert TokenBudget is not None
    assert TokenBudgetExceeded is not None


def test_under_budget_returns_true():
    """Test 2: add() under cap returns True."""
    b = TokenBudget(max_tokens=100)
    assert b.add(50) is True


def test_over_budget_raises():
    """Test 3: add() that exceeds cap raises TokenBudgetExceeded."""
    b = TokenBudget(max_tokens=100)
    with pytest.raises(TokenBudgetExceeded):
        b.add(150)


def test_remaining_decrements():
    """Test 4: remaining property reflects added tokens."""
    b = TokenBudget(max_tokens=100)
    b.add(30)
    assert b.remaining == 70


def test_total_accumulates():
    """Test 5: total property accumulates across multiple add() calls."""
    b = TokenBudget(max_tokens=100)
    b.add(30)
    b.add(20)
    assert b.total == 50


def test_negative_tokens_rejected():
    """Defensive: negative tokens raise ValueError, not silently accepted."""
    b = TokenBudget(max_tokens=100)
    with pytest.raises(ValueError):
        b.add(-1)
