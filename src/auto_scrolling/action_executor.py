from __future__ import annotations

from typing import Any

from auto_scrolling.config import VALID_PROFILES, AppConfig
from auto_scrolling.models import GestureType


class WindowsActionExecutor:
    """Translates confirmed gestures into Windows desktop input events."""

    def __init__(
        self,
        config: AppConfig,
        backend: Any | None = None,
        dry_run: bool = False,
    ) -> None:
        self.config = config
        self.dry_run = dry_run
        if backend is None:
            import pyautogui

            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0.01
            self._gui = pyautogui
        else:
            self._gui = backend

    def cycle_profile(self) -> str:
        try:
            idx = VALID_PROFILES.index(self.config.active_profile)
        except ValueError:
            idx = 0
        next_profile = VALID_PROFILES[(idx + 1) % len(VALID_PROFILES)]
        self.config.active_profile = next_profile
        return next_profile

    def calibrate_video_center(self) -> tuple[int, int]:
        pos = self._gui.position()
        coords = (int(pos[0]), int(pos[1]))
        self.config.video_center_xy = coords
        return coords

    def calibrate_comment_button(self) -> tuple[int, int]:
        pos = self._gui.position()
        coords = (int(pos[0]), int(pos[1]))
        self.config.comment_button_xy = coords
        return coords

    def execute(self, gesture: GestureType) -> str:
        if gesture == GestureType.NONE:
            return "IDLE"

        vx, vy = self.config.video_center_xy
        cx, cy = self.config.comment_button_xy
        profile = self.config.active_profile
        scroll_amt = abs(int(self.config.scroll_amount))

        action_label = self._describe_action(gesture)
        if self.dry_run:
            return f"[DRY-RUN] {action_label}"

        if gesture == GestureType.SWIPE_UP:
            # Swipe tangan ke atas -> Scroll ke bawah (video berikutnya)
            # PENTING: moveTo wajib dipanggil karena pyautogui.scroll di Windows
            # tidak memindahkan kursor ke (x, y) sebelum mengirim WM_MOUSEWHEEL.
            self._gui.moveTo(vx, vy)
            self._gui.scroll(-scroll_amt, x=vx, y=vy)
            if profile == "tiktok_desktop":
                self._gui.press("down")

        elif gesture == GestureType.SWIPE_DOWN:
            # Swipe tangan ke bawah -> Scroll ke atas (video sebelumnya)
            self._gui.moveTo(vx, vy)
            self._gui.scroll(scroll_amt, x=vx, y=vy)
            if profile == "tiktok_desktop":
                self._gui.press("up")

        elif gesture == GestureType.OK_SIGN:
            # Tangan OK -> Like video
            self._gui.moveTo(vx, vy)
            self._gui.doubleClick(x=vx, y=vy)

        elif gesture == GestureType.THREE_FINGERS:
            # 3 Jari -> Buka / Tutup Komentar
            self._gui.moveTo(cx, cy)
            self._gui.click(x=cx, y=cy)

        elif gesture == GestureType.FIVE_FINGERS:
            # 5 Jari -> Pause / Play video
            # Klik tunggal di tengah video bekerja di TikTok & Instagram Desktop
            # meskipun jendela kamera OpenCV sedang aktif (fokus).
            self._gui.moveTo(vx, vy)
            self._gui.click(x=vx, y=vy)

        return action_label

    @staticmethod
    def _describe_action(gesture: GestureType) -> str:
        mapping = {
            GestureType.SWIPE_UP: "SCROLL KE BAWAH (Next Video)",
            GestureType.SWIPE_DOWN: "SCROLL KE ATAS (Prev Video)",
            GestureType.OK_SIGN: "LIKE VIDEO (OK Sign)",
            GestureType.THREE_FINGERS: "BUKA/TUTUP KOMENTAR (3 Jari)",
            GestureType.FIVE_FINGERS: "PAUSE / PLAY (5 Jari)",
        }
        return mapping.get(gesture, "IDLE")
