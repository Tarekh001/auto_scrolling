from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

VALID_PROFILES = ("desktop_universal", "tiktok_desktop", "instagram_desktop")


@dataclass
class AppConfig:
    """Persistent configuration for gesture thresholds and screen coordinates."""

    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    active_profile: str = "desktop_universal"
    swipe_threshold_y: float = 0.12
    swipe_max_duration_sec: float = 0.45
    swipe_max_dx: float = 0.25
    ok_pinch_ratio: float = 0.34
    hold_frames_required: int = 5
    static_cooldown_sec: float = 1.2
    swipe_cooldown_sec: float = 0.6
    video_center_xy: tuple[int, int] = (1071, 553)
    comment_button_xy: tuple[int, int] = (1520, 751)
    scroll_amount: int = 600
    always_on_top: bool = True

    @classmethod
    def load(cls, path: Path | str = "config.json") -> AppConfig:
        cfg_path = Path(path)
        if not cfg_path.exists():
            default_cfg = cls()
            default_cfg.save(cfg_path)
            return default_cfg

        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        if "video_center_xy" in raw:
            raw["video_center_xy"] = tuple(int(v) for v in raw["video_center_xy"])
        if "comment_button_xy" in raw:
            raw["comment_button_xy"] = tuple(int(v) for v in raw["comment_button_xy"])

        known_fields = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in raw.items() if k in known_fields}
        return cls(**filtered)

    def save(self, path: Path | str = "config.json") -> None:
        cfg_path = Path(path)
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data["video_center_xy"] = list(self.video_center_xy)
        data["comment_button_xy"] = list(self.comment_button_xy)
        cfg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
