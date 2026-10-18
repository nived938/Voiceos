import pytest
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
