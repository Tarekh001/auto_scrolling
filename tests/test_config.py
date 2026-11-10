from pathlib import Path
from auto_scrolling.config import AppConfig
from auto_scrolling.models import GestureType, Point3D


def test_config_roundtrip_and_defaults(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cfg = AppConfig.load(cfg_file)
    assert cfg.active_profile == "desktop_universal"
    assert cfg.hold_frames_required == 5
    assert cfg.static_cooldown_sec == 1.2
    assert cfg.swipe_cooldown_sec == 0.6

    cfg.video_center_xy = (800, 500)
    cfg.comment_button_xy = (1150, 600)
    cfg.save(cfg_file)

    loaded = AppConfig.load(cfg_file)
    assert loaded.video_center_xy == (800, 500)
    assert loaded.comment_button_xy == (1150, 600)


def test_models_enums_and_point3d():
    pt = Point3D(0.5, 0.4)
    assert pt.x == 0.5
    assert pt.y == 0.4
    assert pt.z == 0.0
    assert GestureType.SWIPE_UP.value == "SWIPE_UP"
