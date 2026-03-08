"""
Tests for TaskPlanner service
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.task_planner import TaskPlanner, StepStatus, PlanStatus


@pytest.fixture
def planner():
    return TaskPlanner()


SESSION_ID = "test-session-123"


def test_planner_has_default_templates(planner):
    assert len(planner.templates) > 0


def test_get_templates_returns_all(planner):
    templates = planner.get_templates()
    assert len(templates) == len(planner.templates)


def test_get_templates_filtered_by_category(planner):
    templates = planner.get_templates(category="Printer")
    assert all(t["category"] == "Printer" for t in templates)


def test_detect_template_matches_printer(planner):
    result = planner.detect_template("my printer is offline and not printing")
    assert result is not None
    assert "printer" in result["name"].lower() or "printer" in [k.lower() for k in result["keywords"]]


def test_detect_template_matches_internet(planner):
    result = planner.detect_template("I have no internet connection")
    assert result is not None
    assert result["match_score"] >= 3


def test_detect_template_no_match(planner):
    result = planner.detect_template("xyzzy gibberish nothing")
    assert result is None


def test_create_plan(planner):
    steps = [
        {"title": "Step 1", "description": "Do this first"},
        {"title": "Step 2", "description": "Do this second"},
    ]
    plan = planner.create_plan(SESSION_ID, "Test Plan", "A test plan", steps)

    assert plan.id in planner.plans
    assert plan.session_id == SESSION_ID
    assert plan.title == "Test Plan"
    assert len(plan.steps) == 2
    assert plan.status == PlanStatus.CREATED


def test_create_from_template(planner):
    template_id = list(planner.templates.keys())[0]
    plan = planner.create_from_template(SESSION_ID, template_id)

    assert plan is not None
    assert plan.template_id == template_id
    assert len(plan.steps) > 0


def test_create_from_template_invalid_id(planner):
    result = planner.create_from_template(SESSION_ID, "nonexistent-template")
    assert result is None


def test_create_from_message_known_issue(planner):
    result = planner.create_from_message(SESSION_ID, "printer is offline")
    assert result is not None
    assert "plan" in result
    assert "template" in result


def test_create_from_message_no_match(planner):
    result = planner.create_from_message(SESSION_ID, "xyzzy gibberish no match")
    assert result is None


def test_start_plan(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [
        {"title": "S1", "description": "D1"},
        {"title": "S2", "description": "D2"},
    ])
    result = planner.start_plan(plan.id)

    assert result is not None
    assert result["status"] == PlanStatus.IN_PROGRESS.value
    assert result["current_step"]["status"] == StepStatus.IN_PROGRESS.value


def test_start_plan_not_found(planner):
    result = planner.start_plan("nonexistent-plan")
    assert result is None


def test_start_already_started_plan(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [{"title": "S1", "description": "D1"}])
    planner.start_plan(plan.id)
    # Starting again should return None
    result = planner.start_plan(plan.id)
    assert result is None


def test_complete_step_advances_to_next(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [
        {"title": "S1", "description": "D1"},
        {"title": "S2", "description": "D2"},
    ])
    planner.start_plan(plan.id)
    step_id = plan.steps[0].id

    result = planner.complete_step(plan.id, step_id)

    assert result is not None
    assert result["completed_step"]["status"] == StepStatus.COMPLETED.value
    assert result["next_step"] is not None
    assert result["next_step"]["status"] == StepStatus.IN_PROGRESS.value
    assert result["is_complete"] is False


def test_complete_last_step_finishes_plan(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [
        {"title": "S1", "description": "D1"},
    ])
    planner.start_plan(plan.id)
    step_id = plan.steps[0].id

    result = planner.complete_step(plan.id, step_id)

    assert result["is_complete"] is True
    assert result["next_step"] is None
    assert result["plan"]["status"] == PlanStatus.COMPLETED.value


def test_skip_step_advances_to_next(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [
        {"title": "S1", "description": "D1"},
        {"title": "S2", "description": "D2"},
    ])
    planner.start_plan(plan.id)
    step_id = plan.steps[0].id

    result = planner.skip_step(plan.id, step_id)

    assert result is not None
    assert result["skipped_step"]["status"] == StepStatus.SKIPPED.value
    assert result["next_step"]["status"] == StepStatus.IN_PROGRESS.value


def test_fail_step_marks_plan_failed(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [
        {"title": "S1", "description": "D1"},
    ])
    planner.start_plan(plan.id)
    step_id = plan.steps[0].id

    result = planner.fail_step(plan.id, step_id, "Something went wrong")

    assert result is not None
    assert result["failed_step"]["status"] == StepStatus.FAILED.value
    assert result["plan"]["status"] == PlanStatus.FAILED.value


def test_get_active_plan(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [{"title": "S1", "description": "D1"}])
    planner.start_plan(plan.id)

    active = planner.get_active_plan(SESSION_ID)
    assert active is not None
    assert active["id"] == plan.id


def test_get_active_plan_none_when_not_started(planner):
    planner.create_plan(SESSION_ID, "T", "D", [{"title": "S1", "description": "D1"}])
    active = planner.get_active_plan(SESSION_ID)
    assert active is None


def test_progress_tracking(planner):
    plan = planner.create_plan(SESSION_ID, "T", "D", [
        {"title": "S1", "description": "D1"},
        {"title": "S2", "description": "D2"},
        {"title": "S3", "description": "D3"},
    ])
    planner.start_plan(plan.id)
    planner.complete_step(plan.id, plan.steps[0].id)

    progress = plan.progress
    assert progress["total"] == 3
    assert progress["completed"] == 1
    assert progress["percent"] == 33
