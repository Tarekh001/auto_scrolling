from __future__ import annotations

from pathlib import Path
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

from auto_scrolling.models import GestureType, HandObservation, Point3D

HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"
)

HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky & Palm
)


def ensure_hand_model(model_path: Path = DEFAULT_MODEL_PATH) -> Path:
    """Ensures the MediaPipe hand_landmarker.task model exists locally."""
    if model_path.exists() and model_path.stat().st_size > 100_000:
        return model_path
    model_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Mengunduh model MediaPipe HandLandmarker ke {model_path} ...")
    urllib.request.urlretrieve(HAND_LANDMARKER_URL, str(model_path))
    return model_path


class HandLandmarkExtractor:
    """Extracts 21 normalized 3D hand landmarks using MediaPipe Tasks API."""

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.65,
        min_tracking_confidence: float = 0.65,
        model_path: Path = DEFAULT_MODEL_PATH,
    ) -> None:
        self._last_observation: HandObservation | None = None
        self._use_tasks_api = hasattr(mp, "tasks")

        if self._use_tasks_api:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision

            resolved_model = ensure_hand_model(model_path)
            base_options = mp_python.BaseOptions(
                model_asset_path=str(resolved_model)
            )
            options = mp_vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.IMAGE,
                num_hands=max_num_hands,
                min_hand_detection_confidence=min_detection_confidence,
                min_hand_presence_confidence=min_tracking_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
        else:
            self._mp_hands = mp.solutions.hands
            self._landmarker = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

    def process_frame(self, frame_bgr: np.ndarray) -> HandObservation | None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._last_observation = None

        if self._use_tasks_api:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._landmarker.detect(mp_image)
            if not result.hand_landmarks:
                return None

            hand_lms = result.hand_landmarks[0]
            points = [
                Point3D(float(lm.x), float(lm.y), float(lm.z)) for lm in hand_lms
            ]
            handedness = "Right"
            score = 1.0
            if result.handedness and result.handedness[0]:
                cat = result.handedness[0][0]
                handedness = cat.category_name or "Right"
                score = float(cat.score)

            self._last_observation = HandObservation(
                landmarks=points, handedness=handedness, score=score
            )
            return self._last_observation

        results = self._landmarker.process(rgb)
        if not results.multi_hand_landmarks:
            return None
        hand_lms = results.multi_hand_landmarks[0]
        points = [
            Point3D(float(lm.x), float(lm.y), float(lm.z))
            for lm in hand_lms.landmark
        ]
        self._last_observation = HandObservation(landmarks=points)
        return self._last_observation

    def draw_landmarks(self, frame_bgr: np.ndarray) -> None:
        if self._last_observation is None:
            return

        h, w = frame_bgr.shape[:2]
        pts_px = [
            (int(lm.x * w), int(lm.y * h))
            for lm in self._last_observation.landmarks
        ]

        for i, j in HAND_CONNECTIONS:
            cv2.line(frame_bgr, pts_px[i], pts_px[j], (0, 230, 118), 2, cv2.LINE_AA)

        for idx, (px, py) in enumerate(pts_px):
            radius = 6 if idx in (4, 8, 12, 16, 20) else 4
            color = (0, 210, 255) if idx in (4, 8, 12, 16, 20) else (255, 255, 255)
            cv2.circle(frame_bgr, (px, py), radius, color, -1, cv2.LINE_AA)

    def close(self) -> None:
        self._landmarker.close()


def render_hud(
    frame_bgr: np.ndarray,
    raw_gesture: GestureType,
    last_action: str,
    hold_progress: float,
    cooldown_rem: float,
    profile: str,
    video_xy: tuple[int, int],
    comment_xy: tuple[int, int],
    muted: bool,
) -> np.ndarray:
    """Draws status HUD overlay onto the webcam frame."""
    h, w = frame_bgr.shape[:2]

    overlay = frame_bgr.copy()
    cv2.rectangle(overlay, (0, 0), (w, 108), (20, 20, 20), -1)
    cv2.rectangle(overlay, (0, h - 36), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.72, frame_bgr, 0.28, 0, frame_bgr)

    status_color = (0, 220, 120) if not muted else (0, 140, 255)
    mode_txt = "AKTIF" if not muted else "PAUSED (Tekan M)"
    cv2.putText(
        frame_bgr,
        f"Mode: {mode_txt} | Profil: {profile}",
        (12, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        status_color,
        2,
    )

    cv2.putText(
        frame_bgr,
        f"Gestur: {raw_gesture.value}",
        (12, 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        frame_bgr,
        f"Aksi Terakhir: {last_action}",
        (12, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (80, 220, 255),
        2,
    )

    bar_x, bar_y, bar_w, bar_h = 12, 92, w - 24, 8
    cv2.rectangle(
        frame_bgr, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (70, 70, 70), -1
    )
    if cooldown_rem > 0:
        fill_w = int(bar_w * min(1.0, cooldown_rem / 1.2))
        cv2.rectangle(
            frame_bgr,
            (bar_x, bar_y),
            (bar_x + fill_w, bar_y + bar_h),
            (0, 180, 255),
            -1,
        )
    elif hold_progress > 0:
        fill_w = int(bar_w * hold_progress)
        cv2.rectangle(
            frame_bgr,
            (bar_x, bar_y),
            (bar_x + fill_w, bar_y + bar_h),
            (0, 255, 120),
            -1,
        )

    help_text = (
        f"[V] Video:{video_xy}  [C] Komen:{comment_xy}  [P] Profil  [M] Mute  [Q] Keluar"
    )
    cv2.putText(
        frame_bgr,
        help_text,
        (10, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.44,
        (210, 210, 210),
        1,
    )
    return frame_bgr
