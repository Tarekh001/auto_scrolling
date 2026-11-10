# Auto-Scrolling Touchless Hand Controller

Sistem kontrol tanpa sentuh (*touchless hand-gesture controller*) untuk mengendalikan aplikasi desktop di Windows (**TikTok Desktop**, **Instagram Desktop**, YouTube Shorts, dll.) hanya menggunakan gerakan tangan dari jarak jauh melalui webcam bawaan laptop.

---

## Daftar Gestur & Aksi

| Gerakan Tangan | Kode Gestur | Aksi di Aplikasi Desktop |
|---|---|---|
| **Swipe Tangan ke Atas** | `SWIPE_UP` | **Scroll ke Bawah** (berpindah ke video berikutnya) |
| **Swipe Tangan ke Bawah** | `SWIPE_DOWN` | **Scroll ke Atas** (kembali ke video sebelumnya) |
| **Bentuk Tangan "OK"** (jempol & telunjuk menyatu, 3 jari lain terbuka) | `OK_SIGN` | **Like** video (*double-click* tengah video / tombol `L`) |
| **Bentuk Tangan 3 Jari** (telunjuk, tengah, manis terbuka) | `THREE_FINGERS` | **Buka / Tutup Komentar** (klik pada ikon komentar) |
| **Bentuk Tangan 5 Jari Terbuka** (tahan stabil) | `FIVE_FINGERS` | **Pause / Play** video (tombol `Space` / klik tengah video) |

---

## Cara Menjalankan

### 1. Mode Latihan (Dry-Run — Tanpa Menggerakkan Mouse/Keyboard)
Gunakan mode ini terlebih dahulu untuk mencoba gerakan tangan di depan kamera:
```powershell
uv run --python 3.12 python -m auto_scrolling.main --dry-run
```

### 2. Mode Aktif (Mengontrol TikTok / Instagram Desktop)
```powershell
uv run --python 3.12 python -m auto_scrolling.main
```

### 3. Cara Kalibrasi Cepat (1 Detik)
Saat jendela kamera (*HUD*) terbuka dan aplikasi desktop TikTok/Instagram sudah tampil di layar:
1. Arahkan kursor mouse ke **tengah area video**, lalu klik jendela kamera dan tekan tombol **`V`**.
2. Arahkan kursor mouse tepat di atas **ikon balon Komentar**, lalu klik jendela kamera dan tekan tombol **`C`**.
3. Koordinat otomatis tersimpan ke dalam `config.json`!

### Pintasan Keyboard pada Jendela HUD Kamera
- **`V`**: Simpan posisi kursor mouse saat ini sebagai titik tengah **Video**
- **`C`**: Simpan posisi kursor mouse saat ini sebagai titik tombol **Komentar**
- **`P`**: Ganti profil aplikasi (`desktop_universal` / `tiktok_desktop` / `instagram_desktop`)
- **`M`**: Jeda / lanjutkan pembacaan gestur (*Mute / Unmute*)
- **`Q` / `ESC`**: Keluar dari program

---

## Struktur Proyek & Pemeliharaan (*Maintenance*)

```
e:\My_Project\auto_scrolling\
├── config.json                # Konfigurasi sensitivitas, cooldown, & koordinat layar
├── pyproject.toml             # Definisi paket & dependensi uv (Python 3.12)
├── docs/
│   ├── PRD.md                 # Product Requirements Document
│   └── SRS.md                 # Software Requirements Specification
├── src/auto_scrolling/
│   ├── models.py              # Definisi tipe data (GestureType, Point3D)
│   ├── config.py              # Pembaca & penyimpan config.json
│   ├── gesture_classifier.py  # Algoritma matematika 21 titik tangan MediaPipe
│   ├── state_machine.py       # Filter Hold-to-Confirm, Cooldown, & Wait-for-Release
│   ├── action_executor.py     # Eksekutor perintah Windows (PyAutoGUI)
│   ├── camera_tracker.py      # Akuisisi kamera OpenCV, MediaPipe, & tampilan HUD
│   └── main.py                # Entry point CLI
└── tests/                     # Pengujian otomatis (pytest)
```

### Menjalankan Unit Tests
```powershell
uv run --python 3.12 pytest -v
```
