"""
Tests for KnowledgeBase service
"""
import pytest
import sys
import os

# Add the backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.knowledge_base import KnowledgeBase


@pytest.fixture
def kb():
    return KnowledgeBase()


def test_kb_has_default_problems(kb):
    assert len(kb.problems) > 0


def test_kb_has_default_solutions(kb):
    assert len(kb.solutions) > 0


def test_kb_get_categories(kb):
    categories = kb.get_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert "Printer" in categories


def test_search_returns_results_for_known_problem(kb):
    results = kb.search("printer offline")
    assert len(results) > 0
    first = results[0]
    assert "title" in first
    assert "solutions" in first


def test_search_ranks_title_match_higher(kb):
    results = kb.search("no internet")
    assert len(results) > 0
    # The most relevant result should score highest
    scores = [r.get("score", 0) for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_with_category_filter(kb):
    results = kb.search("driver", category="Printer")
    for r in results:
        assert r["category"] == "Printer"


def test_search_no_results_for_gibberish(kb):
    results = kb.search("xyzzy_no_match_abc123")
    assert results == []


def test_get_problem_by_id(kb):
    # Get any problem id
    problem_id = list(kb.problems.keys())[0]
    problem = kb.get_problem(problem_id)
    assert problem is not None
    assert problem["id"] == problem_id


def test_get_problem_not_found(kb):
    result = kb.get_problem("nonexistent-id")
    assert result is None


def test_get_solution_by_id(kb):
    solution_id = list(kb.solutions.keys())[0]
    solution = kb.get_solution(solution_id)
    assert solution is not None
    assert solution["id"] == solution_id


def test_get_solution_not_found(kb):
    result = kb.get_solution("nonexistent-id")
    assert result is None


def test_record_feedback_success(kb):
    solution_id = list(kb.solutions.keys())[0]
    solution = kb.solutions[solution_id]
    initial_success = solution.success_count

    kb.record_feedback(solution_id, success=True)
    assert solution.success_count == initial_success + 1


def test_record_feedback_failure(kb):
    solution_id = list(kb.solutions.keys())[0]
    solution = kb.solutions[solution_id]
    initial_failure = solution.failure_count

    kb.record_feedback(solution_id, success=False)
    assert solution.failure_count == initial_failure + 1


def test_record_feedback_invalid_id(kb):
    # Should return False gracefully, not raise
    result = kb.record_feedback("nonexistent-id", success=True)
    assert result is False


def test_success_rate_calculation(kb):
    solution_id = list(kb.solutions.keys())[0]
    solution = kb.solutions[solution_id]

    solution.success_count = 3
    solution.failure_count = 1
    assert solution.success_rate == pytest.approx(0.75)


def test_success_rate_zero_when_no_uses(kb):
    solution_id = list(kb.solutions.keys())[0]
    solution = kb.solutions[solution_id]
    solution.success_count = 0
    solution.failure_count = 0
    assert solution.success_rate == 0.0


def test_get_context_for_query_with_match(kb):
    context = kb.get_context_for_query("printer not working")
    assert context["has_matches"] is True
    assert len(context["problems"]) > 0


def test_get_context_for_query_no_match(kb):
    context = kb.get_context_for_query("xyzzy_gibberish_abc")
    assert context["has_matches"] is False
