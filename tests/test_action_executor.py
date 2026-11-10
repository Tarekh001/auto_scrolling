from unittest.mock import MagicMock, call
from auto_scrolling.action_executor import WindowsActionExecutor
from auto_scrolling.config import AppConfig
from auto_scrolling.models import GestureType


def test_execute_all_five_gestures_in_universal_profile():
    mock_gui = MagicMock()
    cfg = AppConfig(
        active_profile="desktop_universal",
        video_center_xy=(700, 500),
        comment_button_xy=(1100, 550),
        scroll_amount=600,
    )
    executor = WindowsActionExecutor(cfg, backend=mock_gui)

    executor.execute(GestureType.SWIPE_UP)
    mock_gui.moveTo.assert_called_with(700, 500)
    mock_gui.scroll.assert_called_with(-600, x=700, y=500)

    executor.execute(GestureType.SWIPE_DOWN)
    mock_gui.moveTo.assert_called_with(700, 500)
    mock_gui.scroll.assert_called_with(600, x=700, y=500)

    executor.execute(GestureType.OK_SIGN)
    mock_gui.doubleClick.assert_called_with(x=700, y=500)

    executor.execute(GestureType.THREE_FINGERS)
    mock_gui.moveTo.assert_called_with(1100, 550)
    mock_gui.click.assert_called_with(x=1100, y=550)

    # FIVE_FINGERS in desktop_universal clicks video center (works even without keyboard focus)
    executor.execute(GestureType.FIVE_FINGERS)
    mock_gui.moveTo.assert_called_with(700, 500)
    mock_gui.click.assert_called_with(x=700, y=500)


def test_tiktok_and_instagram_profiles_and_dry_run():
    mock_gui = MagicMock()
    cfg = AppConfig(
        active_profile="tiktok_desktop",
        video_center_xy=(700, 500),
        comment_button_xy=(1100, 550),
    )
    executor = WindowsActionExecutor(cfg, backend=mock_gui)

    executor.execute(GestureType.SWIPE_UP)
    mock_gui.moveTo.assert_called_with(700, 500)
    mock_gui.scroll.assert_called_with(-600, x=700, y=500)
    mock_gui.press.assert_called_with("down")

    executor.execute(GestureType.OK_SIGN)
    mock_gui.doubleClick.assert_called_with(x=700, y=500)

    # Cycle to instagram_desktop
    new_profile = executor.cycle_profile()
    assert new_profile == "instagram_desktop"
    executor.execute(GestureType.FIVE_FINGERS)
    mock_gui.click.assert_called_with(x=700, y=500)

    # Dry run does not call backend
    mock_gui.reset_mock()
    dry_exec = WindowsActionExecutor(cfg, backend=mock_gui, dry_run=True)
    label = dry_exec.execute(GestureType.OK_SIGN)
    assert "DRY-RUN" in label
    mock_gui.assert_not_called()
