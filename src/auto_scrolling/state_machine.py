from __future__ import annotations

from auto_scrolling.config import AppConfig
from auto_scrolling.models import GestureType


class GestureStateMachine:
    """Enforces hold-to-confirm, cooldowns, and wait-for-release for gestures."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._candidate: GestureType = GestureType.NONE
        self._consecutive_frames: int = 0
        self._static_cooldown_until: float = 0.0
        self._swipe_cooldown_until: float = 0.0
        self._latched_static: GestureType = GestureType.NONE

    def cooldown_remaining(self, timestamp: float) -> float:
        return max(
            0.0,
            max(self._static_cooldown_until, self._swipe_cooldown_until) - timestamp,
        )

    @property
    def hold_progress(self) -> float:
        if self.config.hold_frames_required <= 0:
            return 1.0
        return min(
            1.0, self._consecutive_frames / float(self.config.hold_frames_required)
        )

    def reset(self) -> None:
        self._candidate = GestureType.NONE
        self._consecutive_frames = 0
        self._latched_static = GestureType.NONE

    def update(
        self, raw_gesture: GestureType, timestamp: float
    ) -> GestureType | None:
        # Release latched static gesture as soon as user changes pose or lowers hand
        if (
            self._latched_static != GestureType.NONE
            and raw_gesture != self._latched_static
        ):
            self._latched_static = GestureType.NONE

        if raw_gesture == GestureType.NONE:
            self._candidate = GestureType.NONE
            self._consecutive_frames = 0
            return None

        # Dynamic swipes trigger immediately and are ONLY gated by swipe_cooldown_until
        # (never blocked by a static gesture cooldown such as FIVE_FINGERS)
        if raw_gesture.is_dynamic:
            self._candidate = GestureType.NONE
            self._consecutive_frames = 0
            self._latched_static = GestureType.NONE
            if timestamp < self._swipe_cooldown_until:
                return None
            self._swipe_cooldown_until = timestamp + self.config.swipe_cooldown_sec
            # Also push static cooldown forward so static pose right after swipe won't fire
            self._static_cooldown_until = max(
                self._static_cooldown_until,
                timestamp + self.config.swipe_cooldown_sec,
            )
            return raw_gesture

        # During static or swipe cooldown, ignore static triggers
        if timestamp < self._static_cooldown_until or timestamp < self._swipe_cooldown_until:
            self._candidate = GestureType.NONE
            self._consecutive_frames = 0
            return None

        # Static gestures: prevent re-trigger if still holding the exact same pose
        if raw_gesture == self._latched_static:
            return None

        if raw_gesture == self._candidate:
            self._consecutive_frames += 1
        else:
            self._candidate = raw_gesture
            self._consecutive_frames = 1

        if self._consecutive_frames >= self.config.hold_frames_required:
            confirmed = self._candidate
            self._candidate = GestureType.NONE
            self._consecutive_frames = 0
            self._latched_static = confirmed
            self._static_cooldown_until = timestamp + self.config.static_cooldown_sec
            return confirmed

        return None
