import shutil
import tempfile
from pathlib import Path
import pytest
from core.database import DatabaseManager

@pytest.fixture
def temp_db():
    temp_dir = Path(tempfile.mkdtemp())
    db = DatabaseManager(temp_dir / "test.db")
    yield db
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_session_lifecycle(temp_db):
    s_id = temp_db.create_session(
        transcript="Hello VoiceOS",
        generated_text="Hello user! How can I assist you?",
        app_name="Code.exe",
        window_title="main.py - Visual Studio Code",
        duration_seconds=2.5,
        mode=3
    )
    assert s_id is not None

    sessions = temp_db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["transcript"] == "Hello VoiceOS"
    assert sessions[0]["mode"] == 3
    assert sessions[0]["word_count"] == 2

    # Verify insights
    insights = temp_db.get_total_insights()
    assert insights["total_sessions"] == 1
    assert insights["total_words"] == 2

def test_turn_and_tool_call(temp_db):
    s_id = temp_db.create_session(transcript="Weather query", mode=3)
    turn_id = temp_db.record_turn(
        session_id=s_id,
        user_message="What is the weather?",
        assistant_response="It is sunny and 25C.",
        duration_ms=1200,
        tool_calls=[{"tool_name": "weather_forecast", "status": "completed"}]
    )
    assert turn_id is not None
    insights = temp_db.get_total_insights()
    assert insights["total_tools"] == 1

def test_custom_dictionary(temp_db):
    assert temp_db.add_dictionary_word("Nived", "User name")
    assert not temp_db.add_dictionary_word("Nived") # Duplicate should fail
    assert temp_db.add_dictionary_word("Kubernetes", "DevOps container engine")

    words = temp_db.get_dictionary_words()
    assert len(words) == 2
    word_texts = [w["text"] for w in words]
    assert "Nived" in word_texts
    assert "Kubernetes" in word_texts

    # Delete
    w_id = words[0]["id"]
    temp_db.delete_dictionary_word(w_id)
    assert len(temp_db.get_dictionary_words()) == 1
