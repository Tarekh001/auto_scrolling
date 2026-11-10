import numpy as np

from auto_scrolling.camera_tracker import HandLandmarkExtractor, render_hud
from auto_scrolling.models import GestureType


def test_extractor_and_hud_on_blank_frame():
    extractor = HandLandmarkExtractor()
    try:
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        obs = extractor.process_frame(blank)
        assert obs is None

        rendered = render_hud(
            frame_bgr=blank,
            raw_gesture=GestureType.OK_SIGN,
            last_action="LIKE VIDEO",
            hold_progress=0.6,
            cooldown_rem=0.0,
            profile="desktop_universal",
            video_xy=(680, 520),
            comment_xy=(1080, 560),
            muted=False,
        )
        assert rendered.shape == (480, 640, 3)
        assert int(rendered.sum()) > 0
    finally:
        extractor.close()
