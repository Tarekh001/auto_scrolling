from __future__ import annotations

import argparse
from pathlib import Path
import time

import cv2

from auto_scrolling.action_executor import WindowsActionExecutor
from auto_scrolling.camera_tracker import HandLandmarkExtractor, render_hud
from auto_scrolling.config import AppConfig
from auto_scrolling.gesture_classifier import GestureClassifier
from auto_scrolling.models import GestureType
from auto_scrolling.state_machine import GestureStateMachine

WINDOW_TITLE = "Auto-Scrolling Hand Controller"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Touchless Hand-Gesture Controller untuk Aplikasi Desktop Windows (TikTok, Instagram, dll.)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Lokasi file konfigurasi JSON (default: config.json)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=None,
        help="Indeks webcam (override nilai camera_index di config.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode latihan: tampilkan deteksi gestur di HUD tanpa mengirim klik/scroll ke Windows",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = AppConfig.load(args.config)
    if args.camera is not None:
        config.camera_index = args.camera

    classifier = GestureClassifier(config)
    state_machine = GestureStateMachine(config)
    executor = WindowsActionExecutor(config, dry_run=args.dry_run)
    extractor = HandLandmarkExtractor()

    cap = cv2.VideoCapture(config.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    if not cap.isOpened():
        print(
            f"[ERROR] Tidak dapat membuka webcam pada indeks {config.camera_index}."
        )
        extractor.close()
        return 1

    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    if config.always_on_top:
        try:
            cv2.setWindowProperty(WINDOW_TITLE, cv2.WND_PROP_TOPMOST, 1)
        except cv2.error:
            pass

    muted = False
    last_action = "Menunggu gestur tangan..."
    print("=== Auto-Scrolling Hand Controller Aktif ===")
    print("Pintasan di jendela kamera:")
    print("  [V] Simpan posisi kursor mouse sebagai titik Tengah Video")
    print("  [C] Simpan posisi kursor mouse sebagai titik Tombol Komentar")
    print("  [P] Ganti profil aplikasi (Universal / TikTok / Instagram)")
    print("  [M] Mute / Unmute pembacaan gestur")
    print("  [Q] atau [ESC] Keluar")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Mirror horizontally so movements feel natural
            frame = cv2.flip(frame, 1)
            now = time.monotonic()

            obs = extractor.process_frame(frame)
            extractor.draw_landmarks(frame)

            landmarks = obs.landmarks if obs is not None else None
            raw_gesture = classifier.evaluate(landmarks, now)

            if not muted:
                confirmed = state_machine.update(raw_gesture, now)
                if confirmed is not None and confirmed != GestureType.NONE:
                    last_action = executor.execute(confirmed)
                    print(f"[{time.strftime('%H:%M:%S')}] {confirmed.value} -> {last_action}")
            else:
                state_machine.reset()

            render_hud(
                frame_bgr=frame,
                raw_gesture=raw_gesture,
                last_action=last_action,
                hold_progress=state_machine.hold_progress,
                cooldown_rem=state_machine.cooldown_remaining(now),
                profile=config.active_profile,
                video_xy=config.video_center_xy,
                comment_xy=config.comment_button_xy,
                muted=muted,
            )

            cv2.imshow(WINDOW_TITLE, frame)
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q"), 27):
                break
            elif key in (ord("v"), ord("V")):
                coords = executor.calibrate_video_center()
                config.save(args.config)
                last_action = f"Kalibrasi Video: {coords}"
                print(f"[INFO] Posisi tengah video disimpan ke {coords}")
            elif key in (ord("c"), ord("C")):
                coords = executor.calibrate_comment_button()
                config.save(args.config)
                last_action = f"Kalibrasi Komentar: {coords}"
                print(f"[INFO] Posisi tombol komentar disimpan ke {coords}")
            elif key in (ord("p"), ord("P")):
                new_prof = executor.cycle_profile()
                config.save(args.config)
                last_action = f"Profil: {new_prof}"
                print(f"[INFO] Profil diganti ke {new_prof}")
            elif key in (ord("m"), ord("M")):
                muted = not muted
                state_txt = "PAUSED" if muted else "AKTIF"
                last_action = f"Mode: {state_txt}"
                print(f"[INFO] Mode pembacaan gestur: {state_txt}")
    finally:
        cap.release()
        extractor.close()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
