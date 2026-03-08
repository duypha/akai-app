"""
Tests for SessionManager service
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch the database before importing SessionManager to avoid SQLite side effects
mock_db = MagicMock()
mock_db.get_session.return_value = None
mock_db.get_session_by_code.return_value = None
mock_db.save_session.return_value = None
mock_db.update_session_messages.return_value = None


@pytest.fixture
def manager():
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        from app.services.session_manager import SessionManager
        return SessionManager()


def test_create_session_returns_session(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
    assert "id" in session
    assert "code" in session
    assert len(session["code"]) == 4
    assert session["code"].isdigit()


def test_create_session_stores_in_memory(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
    assert session["id"] in manager.sessions


def test_create_session_unique_codes(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session1 = manager.create_session()
        session2 = manager.create_session()
    assert session1["code"] != session2["code"] or session1["id"] != session2["id"]


def test_get_session_returns_existing(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        retrieved = manager.get_session(session["id"])
    assert retrieved is not None
    assert retrieved["id"] == session["id"]


def test_get_session_not_found_returns_none(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        result = manager.get_session("nonexistent-id")
    assert result is None


def test_get_session_by_code(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        retrieved = manager.get_session_by_code(session["code"])
    assert retrieved is not None
    assert retrieved["id"] == session["id"]


def test_get_session_by_invalid_code(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        result = manager.get_session_by_code("9999")
    assert result is None


def test_add_message(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        success = manager.add_message(session["id"], "user", "Hello")
    assert success is True
    assert len(manager.sessions[session["id"]]["messages"]) == 1
    assert manager.sessions[session["id"]]["messages"][0]["content"] == "Hello"


def test_add_message_invalid_session(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        result = manager.add_message("nonexistent", "user", "Hello")
    assert result is False


def test_add_message_preserves_role(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        manager.add_message(session["id"], "assistant", "Hi there")
    msg = manager.sessions[session["id"]]["messages"][0]
    assert msg["role"] == "assistant"


def test_delete_session(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        session_id = session["id"]
        result = manager.delete_session(session_id)
    assert result is True
    assert session_id not in manager.sessions


def test_delete_session_not_found(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        result = manager.delete_session("nonexistent")
    assert result is False


def test_set_status_valid(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        result = manager.set_status(session["id"], "resolved")
    assert result is True
    assert manager.sessions[session["id"]]["status"] == "resolved"


def test_set_status_invalid(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        result = manager.set_status(session["id"], "nonexistent_status")
    assert result is False


def test_session_has_empty_messages_on_create(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
    assert session["messages"] == []


def test_multiple_messages_accumulate(manager):
    with patch("app.services.session_manager.get_db", return_value=mock_db):
        session = manager.create_session()
        manager.add_message(session["id"], "user", "Message 1")
        manager.add_message(session["id"], "assistant", "Reply 1")
        manager.add_message(session["id"], "user", "Message 2")
    assert len(manager.sessions[session["id"]]["messages"]) == 3
