# Software Requirements Specification (SRS)
**Nama Proyek:** Auto-Scrolling Touchless Hand Controller  
**Versi Dokumen:** 1.0.0  
**Standar Referensi:** IEEE 830 / ISO/IEC/IEEE 29148  
**Lingkungan Target:** Windows 10/11 (x64), Python 3.12 (dikelola melalui `uv`)  

---

## 1. Pendahuluan & Arsitektur Sistem

### 1.1 Tujuan Dokumen
Dokumen SRS ini mendefinisikan spesifikasi teknis, algoritma deteksi gestur, *state machine* pengendali aksi, serta struktur modul agar proyek dapat dipelihara (*maintainable*), diuji (*testable* tanpa harus selalu menyalakan webcam), dan dikembangkan lebih lanjut.

### 1.2 Komponen Sistem
Sistem dirancang dengan pemisahan tanggung jawab (*Separation of Concerns*) ke dalam 4 lapisan independen:
1. **`AppConfig` (`config.py`):** Menyimpan dan memuat parameter sensitivitas, waktu *cooldown*, profil aplikasi desktop aktif, serta koordinat layar (`video_center_xy` dan `comment_button_xy`) dari `config.json`.
2. **`GestureClassifier` (`gesture_classifier.py`):** Mengevaluasi 21 titik *landmark* tangan 3D menjadi salah satu dari 5 `GestureType` (`SWIPE_UP`, `SWIPE_DOWN`, `OK_SIGN`, `THREE_FINGERS`, `FIVE_FINGERS`) atau `NONE`.
3. **`GestureStateMachine` (`state_machine.py`):** Menerapkan filter *Hold-to-Confirm* (N frame berturut-turut untuk gestur statis), *Cooldown Timer*, dan *Wait-for-Release* agar tidak terjadi pemicuan berulang.
4. **`WindowsActionExecutor` (`action_executor.py`) & `CameraTracker` (`camera_tracker.py`):** Menjalankan simulasi input OS Windows melalui `pyautogui` dan menampilkan HUD visual melalui `OpenCV` + `MediaPipe Hands`.

---

## 2. Spesifikasi Kebutuhan Fungsional (*Functional Requirements*)

### 2.1 Akuisisi Video & Ekstraksi Landmark (`FR-01`)
- **FR-01.1:** Sistem menangkap *stream* video dari webcam bawaan pada resolusi `640x480` piksel dengan target `30 FPS` dan membalik citra secara horizontal (*mirror view*).
- **FR-01.2:** Sistem menggunakan **MediaPipe Hands** (`max_num_hands=1`, `min_detection_confidence=0.7`, `min_tracking_confidence=0.7`) untuk menghasilkan 21 koordinat ternormalisasi `(x_i, y_i, z_i)` dalam rentang `[0.0, 1.0]`.

### 2.2 Algoritma Klasifikasi Gestur (`FR-02`)
Indeks titik *landmark* MediaPipe yang digunakan:
- Pergelangan tangan (*Wrist*): `0`
- Jempol (*Thumb*): `CMC=1, MCP=2, IP=3, TIP=4`
- Telunjuk (*Index*): `MCP=5, PIP=6, DIP=7, TIP=8`
- Tengah (*Middle*): `MCP=9, PIP=10, DIP=11, TIP=12`
- Manis (*Ring*): `MCP=13, PIP=14, DIP=15, TIP=16`
- Kelingking (*Pinky*): `MCP=17, PIP=18, DIP=19, TIP=20`

#### A. Aturan Status Jari Terbuka (*Finger Extended Rule*)
- Untuk 4 jari utama (Telunjuk, Tengah, Manis, Kelingking), sebuah jari dinyatakan **Terbuka (`True`)** jika `y_TIP < y_PIP - 0.02 * scale`.
- Untuk Jempol, dinyatakan **Terbuka (`True`)** jika jarak Euclidean antara ujung jempol (`TIP=4`) dan sendi kelingking (`MCP=17`) lebih besar dari `1.15 * dist(IP=3, MCP=17)`.

#### B. Definisi Matematis 5 Gestur Utama

| Kode Gestur | Nama Aksi | Syarat Matematis Deteksi | Prioritas Evaluasi |
|---|---|---|---|
| `SWIPE_UP` | **Scroll ke Bawah** (Konten Berikutnya) | Pergeseran vertikal pusat tangan `dy <= -0.18` dalam jendela waktu `dt <= 0.35s` dengan pergeseran horizontal `|dx| < 0.15`. | **Prioritas 1** (Dinamis) |
| `SWIPE_DOWN` | **Scroll ke Atas** (Konten Sebelumnya) | Pergeseran vertikal pusat tangan `dy >= +0.18` dalam jendela waktu `dt <= 0.35s` dengan pergeseran horizontal `|dx| < 0.15`. | **Prioritas 1** (Dinamis) |
| `OK_SIGN` | **Like** | Jarak ternormalisasi ujung jempol (`4`) dan ujung telunjuk (`8`) relatif terhadap ukuran telapak tangan (`L_palm = dist(p0, p9)`) memenuhi `dist(p4, p8) / L_palm < 0.32`, **DAN** jari Tengah (`12`), Manis (`16`), serta Kelingking (`20`) berstatus **Terbuka**. | **Prioritas 2** (Statis) |
| `THREE_FINGERS` | **Buka/Tutup Komentar** | Jari Telunjuk (`8`), Tengah (`12`), dan Manis (`16`) berstatus **Terbuka**, sedangkan Jempol (`4`) dan Kelingking (`20`) berstatus **Tertutup**, serta bukan `OK_SIGN`. | **Prioritas 3** (Statis) |
| `FIVE_FINGERS` | **Pause / Play** | Kelima jari (`4, 8, 12, 16, 20`) berstatus **Terbuka**, **DAN** kecepatan vertikal tangan rendah (`|dy| < 0.05` dalam `0.15s` terakhir) agar tangan yang baru diangkat untuk *swipe* tidak memicu *Pause/Play*. | **Prioritas 4** (Statis) |

---

### 2.3 State Machine: Debounce & Cooldown (`FR-03`)
1. **Aturan *Hold-to-Confirm* (`FR-03.1`):** Gestur statis (`OK_SIGN`, `THREE_FINGERS`, `FIVE_FINGERS`) wajib terdeteksi secara konsisten selama `hold_frames_required = 5` frame berturut-turut sebelum dieksekusi. Gestur dinamis (`SWIPE_UP`, `SWIPE_DOWN`) langsung dieksekusi begitu ambang kecepatan terpenuhi.
2. **Aturan *Cooldown* (`FR-03.2`):** Setelah satu gestur memicu aksi, sistem masuk ke status `COOLDOWN` selama `static_cooldown_sec = 1.2` detik (untuk gestur statis) atau `swipe_cooldown_sec = 0.6` detik (untuk *swipe*).
3. **Aturan *Wait-for-Release* (`FR-03.3`):** Untuk gestur statis, setelah *cooldown* habis, jika pengguna masih menahan pose jari yang sama persis tanpa menurunkannya, sistem tidak memicu ulang aksi tersebut sampai pose tangan berubah atau kembali ke posisi netral (`NONE`).

---

### 2.4 Eksekutor Aksi Desktop Windows (`FR-04`)

| Gestur | Profil `desktop_universal` (Default) | Profil `tiktok_desktop` | Profil `instagram_desktop` |
|---|---|---|---|
| `SWIPE_UP` (Scroll Bawah) | `scroll(-600)` pada `video_center_xy` | Tekan tombol `down` | `scroll(-600)` pada `video_center_xy` |
| `SWIPE_DOWN` (Scroll Atas) | `scroll(600)` pada `video_center_xy` | Tekan tombol `up` | `scroll(600)` pada `video_center_xy` |
| `OK_SIGN` (Like) | `doubleClick(video_center_xy)` | Tekan tombol `l` | `doubleClick(video_center_xy)` |
| `THREE_FINGERS` (Komentar) | `click(comment_button_xy)` | `click(comment_button_xy)` | `click(comment_button_xy)` |
| `FIVE_FINGERS` (Pause/Play) | Tekan tombol `space` | Tekan tombol `space` | `click(video_center_xy)` |

---

## 3. Kebutuhan Non-Fungsional (*Non-Functional Requirements*)
- **NFR-01 (Kinerja):** Pemrosesan per frame selesai dalam waktu `< 25 ms` pada CPU laptop standar.
- **NFR-02 (Isolasi Pengujian):** `GestureClassifier` dan `GestureStateMachine` murni memproses data koordinat numerik dan diuji otomatis melalui `pytest`.
- **NFR-03 (Keamanan Eksekusi):** Jika tangan keluar dari tangkapan kamera (`None`), riwayat gerakan *swipe* dibersihkan dan *state machine* di-reset.
