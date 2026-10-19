import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from ui.history_drawer import HistoryDrawer


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.get_sessions.return_value = [
        {
            "id": "sess-1",
            "transcript": "Malayalam language switch test",
            "generated_text": "Switched to Malayalam language persona.",
            "mode": 3,
            "created_at": "2026-10-18T18:05:00Z"
        },
        {
            "id": "sess-2",
            "transcript": "Confirming user name Nived",
            "generated_text": "Your name has been confirmed as Nived.",
            "mode": 3,
            "created_at": "2026-10-18T18:05:00Z"
        },
        {
            "id": "sess-3",
            "transcript": "Hello good day",
            "generated_text": "Hello! How can I assist you today?",
            "mode": 3,
            "created_at": "2026-10-18T14:56:00Z"
        },
        {
            "id": "sess-4",
            "transcript": "What is the weather in Kasaragod?",
            "generated_text": "Current temperature in Kasaragod is 25°C, Overcast.",
            "mode": 3,
            "created_at": "2026-10-18T14:56:00Z"
        }
    ]
    return db


def test_history_drawer_initialization(qapp_session, mock_db):
    drawer = HistoryDrawer(db_manager=mock_db)
    assert drawer.PANEL_WIDTH == 232
    assert drawer.PANEL_HEIGHT == 516
    assert drawer.TOP_OFFSET == 58
    assert drawer.CORNER_RADIUS == 26

    assert drawer.search_input is not None
    assert drawer.search_input.placeholderText() == "Search"
    assert drawer.lock_btn is not None
    assert not drawer.is_pinned()
    drawer.close()


def test_history_drawer_pin_toggle(qapp_session, mock_db):
    drawer = HistoryDrawer(db_manager=mock_db)
    assert not drawer.is_pinned()

    drawer.toggle_pin()
    assert drawer.is_pinned()

    drawer.toggle_pin()
    assert not drawer.is_pinned()
    drawer.close()


def test_history_drawer_title_generation(qapp_session, mock_db):
    drawer = HistoryDrawer(db_manager=mock_db)

    # Weather title
    w_title = drawer._generate_readable_title({"transcript": "what is the weather in Kasaragod"})
    assert "Weather" in w_title
    assert "Kasaragod" in w_title

    # Greeting title
    g_title = drawer._generate_readable_title({"transcript": "Hello there"})
    assert "Greeting" in g_title

    # Malayalam title
    m_title = drawer._generate_readable_title({"transcript": "malayalam voice test"})
    assert "Malayalam" in m_title

    # Long query title with ellipsis
    l_title = drawer._generate_readable_title({"transcript": "Can you summarize the entire history of quantum mechanics and relativity in three sentences?"})
    assert l_title.endswith("...")
    drawer.close()


def test_history_drawer_date_grouping(qapp_session, mock_db):
    drawer = HistoryDrawer(db_manager=mock_db)
    sessions = [
        {"id": "1", "transcript": "Query 1", "created_at": "2026-10-18T18:05:00Z"},
        {"id": "2", "transcript": "Query 2", "created_at": "2026-10-18T14:56:00Z"}
    ]
    groups = drawer._group_sessions(sessions)
    assert len(groups) >= 1
    # Check that headings start with Today, Yesterday, Oct or Recent
    for heading in groups.keys():
        assert "Today" in heading or "Yesterday" in heading or "Oct" in heading or "Recent" in heading
    drawer.close()


def test_history_drawer_search_filtering(qapp_session, mock_db):
    drawer = HistoryDrawer(db_manager=mock_db)
    drawer.reload()

    # Search for Kasaragod
    drawer.search_input.setText("Kasaragod")
    assert len(drawer._filtered_sessions) == 1
    assert "Kasaragod" in drawer._filtered_sessions[0]["transcript"]

    # Search for non-existent term
    drawer.search_input.setText("nonexistentterm123")
    assert len(drawer._filtered_sessions) == 0

    # Clear search
    drawer.search_input.setText("")
    assert len(drawer._filtered_sessions) == 4
    drawer.close()


def test_history_drawer_session_selection(qapp_session, mock_db):
    drawer = HistoryDrawer(db_manager=mock_db)
    drawer.reload()

    received = []
    drawer.session_selected.connect(lambda s: received.append(s))

    target = mock_db.get_sessions.return_value[0]
    drawer._on_item_clicked(target)

    assert len(received) == 1
    assert received[0]["id"] == target["id"]
    assert drawer._selected_session_id == target["id"]
    drawer.close()
