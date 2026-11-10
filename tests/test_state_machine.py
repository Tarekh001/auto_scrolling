from auto_scrolling.config import AppConfig
from auto_scrolling.models import GestureType
from auto_scrolling.state_machine import GestureStateMachine


def test_static_gesture_requires_hold_and_wait_for_release():
    cfg = AppConfig(hold_frames_required=3, static_cooldown_sec=1.0)
    sm = GestureStateMachine(cfg)

    # First 2 frames do not trigger yet
    assert sm.update(GestureType.OK_SIGN, 0.00) is None
    assert sm.update(GestureType.OK_SIGN, 0.03) is None
    # 3rd consecutive frame triggers OK_SIGN
    assert sm.update(GestureType.OK_SIGN, 0.06) == GestureType.OK_SIGN

    # Holding OK_SIGN during and even AFTER cooldown (t=1.5s) must NOT re-trigger
    for t in [0.2, 0.5, 1.1, 1.3, 1.5]:
        assert sm.update(GestureType.OK_SIGN, t) is None

    # Once released to NONE, user can trigger OK_SIGN again
    assert sm.update(GestureType.NONE, 1.6) is None
    assert sm.update(GestureType.OK_SIGN, 1.7) is None
    assert sm.update(GestureType.OK_SIGN, 1.8) is None
    assert sm.update(GestureType.OK_SIGN, 1.9) == GestureType.OK_SIGN


def test_swipe_not_blocked_by_static_cooldown():
    cfg = AppConfig(hold_frames_required=2, static_cooldown_sec=1.2, swipe_cooldown_sec=0.5)
    sm = GestureStateMachine(cfg)

    # Suppose FIVE_FINGERS triggers at t=0.05
    assert sm.update(GestureType.FIVE_FINGERS, 0.00) is None
    assert sm.update(GestureType.FIVE_FINGERS, 0.05) == GestureType.FIVE_FINGERS

    # User immediately swipes up at t=0.20 -> must NOT be blocked by FIVE_FINGERS cooldown!
    assert sm.update(GestureType.SWIPE_UP, 0.20) == GestureType.SWIPE_UP
    # Subsequent swipe within swipe_cooldown_sec (0.5s) is blocked
    assert sm.update(GestureType.SWIPE_UP, 0.40) is None
    # Swipe after 0.5s succeeds
    assert sm.update(GestureType.SWIPE_UP, 0.75) == GestureType.SWIPE_UP
