from __future__ import annotations

from collections import deque
import math
from typing import Sequence

from auto_scrolling.config import AppConfig
from auto_scrolling.models import GestureType, Point3D


def _dist2d(a: Point3D, b: Point3D) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


class GestureClassifier:
    """Classifies 21 MediaPipe hand landmarks into one of the 5 target gestures."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        # Stores (timestamp, wrist_x, wrist_y, finger_anchor_y)
        self._motion_history: deque[tuple[float, float, float, float]] = deque(
            maxlen=25
        )
        self._last_seen_time: float | None = None

    def reset(self) -> None:
        """Clear motion history."""
        self._motion_history.clear()
        self._last_seen_time = None

    def evaluate(
        self, landmarks: Sequence[Point3D] | None, timestamp: float
    ) -> GestureType:
        if not landmarks or len(landmarks) < 21:
            # Tolerate brief 1-3 frame camera dropouts (< 0.35s) during fast swipes
            if (
                self._last_seen_time is not None
                and (timestamp - self._last_seen_time) > 0.35
            ):
                self.reset()
            return GestureType.NONE

        self._last_seen_time = timestamp
        wrist = landmarks[0]
        # Finger/palm vertical anchor captures both wrist swipes and finger-flick swipes
        anchor_y = 0.5 * landmarks[9].y + 0.5 * landmarks[8].y

        self._motion_history.append((timestamp, wrist.x, wrist.y, anchor_y))
        self._prune_history(timestamp)

        # Priority 1: Dynamic swipe gestures (SWIPE_UP / SWIPE_DOWN)
        swipe_gesture = self._detect_swipe(timestamp, wrist.x, wrist.y, anchor_y)
        if swipe_gesture != GestureType.NONE:
            self.reset()
            return swipe_gesture

        # If hand is moving rapidly vertically or horizontally, suppress static gestures
        if self._is_moving_fast(timestamp, wrist.x, wrist.y, anchor_y):
            return GestureType.NONE

        # Priority 2..4: Static hand pose classification
        return self._classify_static(landmarks)

    def _prune_history(self, current_time: float) -> None:
        window = max(self.config.swipe_max_duration_sec, 0.5)
        while (
            self._motion_history
            and (current_time - self._motion_history[0][0]) > window
        ):
            self._motion_history.popleft()

    def _detect_swipe(
        self,
        current_time: float,
        current_x: float,
        current_wrist_y: float,
        current_anchor_y: float,
    ) -> GestureType:
        for t0, x0, wy0, ay0 in self._motion_history:
            dt = current_time - t0
            if dt <= 0.01 or dt > self.config.swipe_max_duration_sec:
                continue
            dx = current_x - x0
            if abs(dx) >= self.config.swipe_max_dx:
                continue

            d_wrist_y = current_wrist_y - wy0
            d_anchor_y = current_anchor_y - ay0
            # Use whichever vertical displacement (wrist or palm/finger) is stronger
            dy = d_wrist_y if abs(d_wrist_y) >= abs(d_anchor_y) else d_anchor_y

            if dy <= -self.config.swipe_threshold_y:
                return GestureType.SWIPE_UP
            if dy >= self.config.swipe_threshold_y:
                return GestureType.SWIPE_DOWN
        return GestureType.NONE

    def _is_moving_fast(
        self,
        current_time: float,
        current_x: float,
        current_wrist_y: float,
        current_anchor_y: float,
    ) -> bool:
        for t0, x0, wy0, ay0 in self._motion_history:
            if (current_time - t0) <= 0.20:
                if (
                    abs(current_wrist_y - wy0) > 0.06
                    or abs(current_anchor_y - ay0) > 0.07
                    or abs(current_x - x0) > 0.08
                ):
                    return True
        return False

    def _classify_static(self, lm: Sequence[Point3D]) -> GestureType:
        palm_len = max(_dist2d(lm[0], lm[9]), 1e-4)
        margin = 0.06 * palm_len
        # Relaxed margin for ring finger when pinky is folded (shared tendon)
        ring_margin = 0.02 * palm_len

        index_open = lm[8].y < (lm[6].y - margin)
        middle_open = lm[12].y < (lm[10].y - margin)
        ring_open = lm[16].y < (lm[14].y - ring_margin)
        pinky_open = lm[20].y < (lm[18].y - margin)

        # Thumb extension check: either spread away from pinky MCP (17)
        # or spread away from index MCP (5)
        thumb_tip_to_pinky = _dist2d(lm[4], lm[17])
        thumb_ip_to_pinky = max(_dist2d(lm[3], lm[17]), 1e-4)
        thumb_tip_to_index_mcp = _dist2d(lm[4], lm[5])
        thumb_open = (thumb_tip_to_pinky > (1.06 * thumb_ip_to_pinky)) or (
            thumb_tip_to_index_mcp > (0.42 * palm_len)
        )

        # Priority 2: OK_SIGN (Like) -> thumb tip (4) & index tip (8) pinched,
        # while middle (12), ring (16), and pinky (20) are extended
        pinch_ratio = _dist2d(lm[4], lm[8]) / palm_len
        if (
            pinch_ratio < self.config.ok_pinch_ratio
            and middle_open
            and ring_open
            and pinky_open
        ):
            return GestureType.OK_SIGN

        # Priority 3: THREE_FINGERS (Buka/Tutup Komentar)
        # Supports both common 3-finger poses:
        #   Variant A: Index + Middle + Ring open, Pinky closed (regardless of thumb)
        #   Variant B: Thumb + Index + Middle open, Ring + Pinky closed
        if not pinky_open and pinch_ratio >= self.config.ok_pinch_ratio:
            if index_open and middle_open and ring_open:
                return GestureType.THREE_FINGERS
            if thumb_open and index_open and middle_open and not ring_open:
                return GestureType.THREE_FINGERS

        # Priority 4: FIVE_FINGERS (Pause/Play) -> 4 main fingers open + thumb open
        if (
            thumb_open
            and index_open
            and middle_open
            and ring_open
            and pinky_open
        ):
            return GestureType.FIVE_FINGERS

        return GestureType.NONE
