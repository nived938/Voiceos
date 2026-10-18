import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from ui.notch_widget import NotchWidget


def test_notch_widget_initialization(qapp_session):
    notch = NotchWidget()
    assert notch._state == NotchWidget.STATE_HIDDEN
    assert notch._current_mode == 0
    assert notch.type_input is not None
    assert notch.status_label is not None
    notch.close()

def test_notch_widget_state_transitions(qapp_session):
    notch = NotchWidget()
    # Transition to peeking
    notch.transition_to_peeking(animated=False)
    assert notch._state == NotchWidget.STATE_PEEKING
    assert notch.geometry().height() == NotchWidget.PEEKING_H

    # Transition to expanded
    notch.transition_to_expanded(animated=False)
    assert notch._state == NotchWidget.STATE_EXPANDED
    assert notch.geometry().height() == NotchWidget.EXPANDED_H

    # Collapse back to hidden
    notch.collapse_to_hidden(animated=False)
    assert notch._state == NotchWidget.STATE_HIDDEN
    assert notch.geometry().height() == NotchWidget.HIDDEN_H
    notch.close()

def test_notch_widget_modes_and_persona(qapp_session):
    notch = NotchWidget()
    # Test setting persona
    notch.set_persona("Friday")
    assert notch._persona_name == "Friday"
    assert "FRIDAY" in notch.badge_label.text()

    # Test mode switching via set_mode and toggle_mode
    notch.set_mode(3)
    assert notch._current_mode == 3
    assert "[AGENT]" in notch.mode_tag.text()

    notch.toggle_mode()
    assert notch._current_mode == 0
    assert "[DICTATE]" in notch.mode_tag.text()
    notch.close()

def test_notch_widget_volume_level(qapp_session):
    notch = NotchWidget()
    notch.transition_to_expanded(animated=False)
    assert len(notch.wave_bars) == 5

    # Should safely adjust heights without error
    notch.set_volume_level(0.75)
    for bar in notch.wave_bars:
        assert bar.height() >= 6
    notch.close()

def test_notch_slash_commands(qapp_session):
    notch = NotchWidget()
    notch.transition_to_expanded(animated=False)

    # Test /time command
    notch._handle_slash_command("/time")
    assert "🕒" in notch.content_label.text()

    # Test /calc command
    notch._handle_slash_command("/calc 50 * 2")
    assert "100" in notch.content_label.text()

    # Test /persona command
    notch._handle_slash_command("/persona Ultron")
    assert notch._persona_name == "Ultron"
    notch.close()


def test_notch_dimensions_and_no_clipping(qapp_session):
    """
    Verifies that the expanded notch has ample vertical room and that the
    input box is never clipped at the bottom.
    """
    notch = NotchWidget()
    notch.transition_to_expanded(animated=False)
    assert notch.height() >= 125
    assert notch.width() >= 480

    notch.start_typing()
    assert notch._is_typing is True
    assert notch.type_input.isVisible() is True
    assert notch.type_input.height() >= 34
    # Layout clearance: notch height must leave generous padding below input box
    assert notch.height() >= notch.type_input.height() + 50
    notch.close()


def test_notch_weather_card_expansion(qapp_session):
    """
    Verifies that weather queries expand the notch into the 270px full card view
    with the weather widget visible.
    """
    notch = NotchWidget()
    notch.expand("what is the weather in Tokyo?", animated=False)
    assert notch._state == NotchWidget.STATE_EXPANDED
    assert notch.height() == NotchWidget.EXPANDED_CARD_H
    assert notch.weather_widget.isVisible() is True
    assert "Tokyo" in notch.weather_city_lbl.text()
    notch.close()


def test_notch_peek_hover_and_leave(qapp_session):
    """
    Verifies the peek hover state machine and leave timer.
    """
    notch = NotchWidget()
    assert notch._state == NotchWidget.STATE_HIDDEN
    assert notch.height() == NotchWidget.HIDDEN_H

    # Simulate hover enter
    notch.transition_to_peeking(animated=False)
    assert notch._state == NotchWidget.STATE_PEEKING
    assert notch.height() == NotchWidget.PEEKING_H

    # Trigger peek timeout
    notch._on_peek_leave_timeout(animated=False)
    assert notch._state == NotchWidget.STATE_HIDDEN
    assert notch.height() == NotchWidget.HIDDEN_H
    notch.close()


def test_notch_outside_click_behavior(qapp_session):
    """
    Verifies that clicks outside the notch frame geometry collapse it to hidden,
    while clicks inside do not collapse it.
    """
    from PySide6.QtCore import QPoint
    notch = NotchWidget()
    notch.transition_to_expanded(animated=False)
    notch._expansion_timestamp = 0.0  # Bypass initial grace period for test

    # 1. Cursor INSIDE notch geometry -> Should stay expanded
    inside_pos = notch.frameGeometry().center()
    with patch("PySide6.QtGui.QCursor.pos", return_value=inside_pos), \
         patch("win32api.GetAsyncKeyState", return_value=0x8000):
        notch._mouse_was_down = False
        notch._check_outside_click(animated=False)
        assert notch._state == NotchWidget.STATE_EXPANDED

    # 2. Cursor OUTSIDE notch geometry (e.g. at desktop or another app) -> Should collapse
    outside_pos = QPoint(inside_pos.x() + 1000, inside_pos.y() + 800)
    with patch("PySide6.QtGui.QCursor.pos", return_value=outside_pos), \
         patch("win32api.GetAsyncKeyState", return_value=0x8000):
        notch._mouse_was_down = False
        notch._check_outside_click(animated=False)
        assert notch._state == NotchWidget.STATE_HIDDEN
        assert notch.height() == NotchWidget.HIDDEN_H

    notch.close()

