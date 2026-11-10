from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class GestureType(str, Enum):
    """Supported hand gestures mapped to Windows desktop actions."""

    NONE = "NONE"
    SWIPE_UP = "SWIPE_UP"          # Scroll ke bawah (video berikutnya)
    SWIPE_DOWN = "SWIPE_DOWN"      # Scroll ke atas (video sebelumnya)
    OK_SIGN = "OK_SIGN"            # Like video
    THREE_FINGERS = "THREE_FINGERS"  # Buka/tutup komentar
    FIVE_FINGERS = "FIVE_FINGERS"  # Pause / Play video

    @property
    def is_dynamic(self) -> bool:
        return self in (GestureType.SWIPE_UP, GestureType.SWIPE_DOWN)

    @property
    def is_static(self) -> bool:
        return self in (
            GestureType.OK_SIGN,
            GestureType.THREE_FINGERS,
            GestureType.FIVE_FINGERS,
        )


class Point3D(NamedTuple):
    """Normalized 3D hand landmark coordinate in [0.0, 1.0]."""

    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class HandObservation:
    """Single-frame observation of a detected hand (21 landmarks)."""

    landmarks: list[Point3D]
    handedness: str = "Right"
    score: float = 1.0
