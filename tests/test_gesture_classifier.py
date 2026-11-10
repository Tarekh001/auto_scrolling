from auto_scrolling.config import AppConfig
from auto_scrolling.gesture_classifier import GestureClassifier
from auto_scrolling.models import GestureType, Point3D


def make_hand(
    wrist: tuple[float, float] = (0.5, 0.7),
    thumb_open: bool = False,
    index_open: bool = False,
    middle_open: bool = False,
    ring_open: bool = False,
    pinky_open: bool = False,
    ok_pinch: bool = False,
    scale: float = 1.0,
) -> list[Point3D]:
    wx, wy = wrist
    pts = [Point3D(wx, wy, 0.0) for _ in range(21)]
    # MCP positions relative to wrist scaled by `scale`
    pts[5] = Point3D(wx - 0.06 * scale, wy - 0.15 * scale)
    pts[9] = Point3D(wx - 0.02 * scale, wy - 0.16 * scale)
    pts[13] = Point3D(wx + 0.02 * scale, wy - 0.15 * scale)
    pts[17] = Point3D(wx + 0.06 * scale, wy - 0.14 * scale)

    # Thumb IP(3) and TIP(4)
    pts[3] = Point3D(wx - 0.08 * scale, wy - 0.12 * scale)
    pts[4] = Point3D(
        wx - (0.14 if thumb_open else 0.06) * scale,
        wy - 0.16 * scale,
    )

    # Fingers PIP and TIP
    finger_specs = [
        (6, 8, index_open, -0.06),
        (10, 12, middle_open, -0.02),
        (14, 16, ring_open, 0.02),
        (18, 20, pinky_open, 0.06),
    ]
    for pip_idx, tip_idx, is_open, dx in finger_specs:
        pip_y = wy - 0.22 * scale
        tip_y = wy - (0.32 if is_open else 0.18) * scale
        pts[pip_idx] = Point3D(wx + dx * scale, pip_y)
        pts[tip_idx] = Point3D(wx + dx * scale, tip_y)

    if ok_pinch:
        pinch_pt = Point3D(wx - 0.08 * scale, wy - 0.22 * scale)
        pts[4] = pinch_pt
        pts[8] = Point3D(pinch_pt.x + 0.01 * scale, pinch_pt.y + 0.01 * scale)
    return pts


def test_ok_sign_scale_invariant():
    clf = GestureClassifier(AppConfig())
    near_hand = make_hand(
        middle_open=True, ring_open=True, pinky_open=True, ok_pinch=True, scale=1.5
    )
    far_hand = make_hand(
        middle_open=True, ring_open=True, pinky_open=True, ok_pinch=True, scale=0.4
    )
    assert clf.evaluate(near_hand, 1.0) == GestureType.OK_SIGN
    clf.reset()
    assert clf.evaluate(far_hand, 2.0) == GestureType.OK_SIGN


def test_three_fingers_comment_gesture_both_variants():
    clf = GestureClassifier(AppConfig())
    # Variant 1: Index + Middle + Ring open (even if thumb happens to be relaxed/open)
    hand_imr = make_hand(
        index_open=True,
        middle_open=True,
        ring_open=True,
        thumb_open=True,
        pinky_open=False,
    )
    assert clf.evaluate(hand_imr, 1.0) == GestureType.THREE_FINGERS

    # Variant 2: Thumb + Index + Middle open, Ring + Pinky closed
    clf.reset()
    hand_tim = make_hand(
        thumb_open=True,
        index_open=True,
        middle_open=True,
        ring_open=False,
        pinky_open=False,
    )
    assert clf.evaluate(hand_tim, 2.0) == GestureType.THREE_FINGERS


def test_five_fingers_pause_play_only_when_stationary():
    clf = GestureClassifier(AppConfig())
    hand1 = make_hand(
        wrist=(0.5, 0.7),
        thumb_open=True,
        index_open=True,
        middle_open=True,
        ring_open=True,
        pinky_open=True,
    )
    assert clf.evaluate(hand1, 1.0) == GestureType.FIVE_FINGERS

    # Fast upward motion with 5 fingers open must trigger SWIPE_UP, not FIVE_FINGERS
    hand2 = make_hand(
        wrist=(0.5, 0.52),
        thumb_open=True,
        index_open=True,
        middle_open=True,
        ring_open=True,
        pinky_open=True,
    )
    assert clf.evaluate(hand2, 1.2) == GestureType.SWIPE_UP


def test_swipe_tolerates_single_dropped_frame_and_rejects_horizontal():
    clf = GestureClassifier(AppConfig())
    clf.evaluate(make_hand(wrist=(0.5, 0.3)), 1.0)
    # 1 dropped frame at t=1.1 due to motion blur must NOT erase swipe history
    assert clf.evaluate(None, 1.1) == GestureType.NONE
    assert clf.evaluate(make_hand(wrist=(0.5, 0.50)), 1.2) == GestureType.SWIPE_DOWN

    # Horizontal movement should not trigger vertical swipe
    clf.reset()
    clf.evaluate(make_hand(wrist=(0.1, 0.3)), 2.0)
    assert clf.evaluate(make_hand(wrist=(0.7, 0.50)), 2.2) == GestureType.NONE


def test_long_camera_dropout_resets_swipe_history():
    clf = GestureClassifier(AppConfig())
    clf.evaluate(make_hand(wrist=(0.5, 0.8)), 1.0)
    # Dropout longer than 0.4s resets history
    assert clf.evaluate(None, 1.6) == GestureType.NONE
    assert clf.evaluate(make_hand(wrist=(0.5, 0.3)), 1.7) != GestureType.SWIPE_UP
