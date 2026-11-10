# Product Requirements Document (PRD)
**Nama Produk:** Auto-Scrolling Touchless Hand Controller  
**Versi Dokumen:** 1.0.0  
**Platform Target:** Windows 10 / 11 (Aplikasi Desktop TikTok, Instagram, YouTube Shorts, dll.)  
**Status:** Disetujui  

---

## 1. Ringkasan Eksekutif & Tujuan Produk
**Auto-Scrolling Touchless Hand Controller** adalah aplikasi desktop ringan berbasis *Computer Vision* yang memungkinkan pengguna mengendalikan aplikasi media sosial vertikal di laptop Windows (seperti aplikasi desktop TikTok dan Instagram) menggunakan gerakan tangan dari jarak jauh melalui webcam bawaan laptop.

### 1.1 Latar Belakang Masalah
Saat bersantai, makan, atau duduk agak jauh dari laptop (0,5 – 1,5 meter), pengguna sering kali kesulitan atau malas harus terus-menerus menyentuh *touchpad*, *mouse*, atau *keyboard* hanya untuk menggulir (*scroll*) video berikutnya, memberikan *Like*, membuka komentar, atau menjeda (*Pause/Play*) video.

### 1.2 Tujuan Produk (Goals)
1. **Navigasi Tanpa Sentuh (*Zero-Touch Navigation*):** Mengizinkan pengguna melakukan 5 aksi utama (*Scroll Bawah*, *Scroll Atas*, *Like*, *Buka Komentar*, *Pause/Play*) 100% menggunakan satu tangan di depan webcam.
2. **Kompatibilitas Lintas Aplikasi Desktop Windows:** Berfungsi langsung pada aplikasi desktop TikTok, Instagram, maupun peramban tanpa memerlukan modifikasi atau *plugin* khusus di dalam aplikasi target.
3. **Kemudahan Pemeliharaan (*Maintainability*):** Memiliki arsitektur modular dan konfigurasi eksternal (`config.json`) sehingga gestur, sensitivitas, maupun titik klik layar mudah diubah di masa depan.

### 1.3 Bukan Tujuan (Non-Goals & Anti-Goals)
- **Non-Goal:** Menggantikan *mouse* sepenuhnya untuk pengetikan teks komentar atau pengeditan video.
- **Anti-Goal (Kondisi Gagal):** Sistem memicu aksi secara tidak sengaja (*false positive*) saat pengguna hanya menggaruk kepala, mengangkat tangan biasa, atau saat tangan sedang bergerak menuju posisi gestur.

---

## 2. Profil Pengguna & Skenario Penggunaan (*User Stories*)

| ID | Sebagai... | Saya ingin... | Sehingga... | Kriteria Penerimaan (*Acceptance Criteria*) |
|---|---|---|---|---|
| **US-01** | Pengguna aplikasi desktop TikTok/IG | Melakukan gerakan *swipe* tangan ke atas di depan kamera | Konten bergulir ke bawah (berpindah ke video berikutnya) | Ketika tangan bergerak ke atas melewati ambang jarak dalam waktu singkat, sistem mengirim perintah *scroll down* / panah bawah. |
| **US-02** | Pengguna aplikasi desktop TikTok/IG | Melakukan gerakan *swipe* tangan ke bawah di depan kamera | Konten bergulir ke atas (kembali ke video sebelumnya) | Ketika tangan bergerak ke bawah melewati ambang jarak dalam waktu singkat, sistem mengirim perintah *scroll up* / panah atas. |
| **US-03** | Pengguna aplikasi desktop TikTok/IG | Membentuk jari "OK" (jempol dan telunjuk menyentuh) | Video yang sedang diputar mendapatkan *Like* | Saat bentuk tangan "OK" ditahan stabil selama ~150 ms, sistem mengeksekusi aksi *Like* (*double-click* pada area video atau tombol `L`). |
| **US-04** | Pengguna aplikasi desktop TikTok/IG | Mengangkat 3 jari (telunjuk, tengah, manis) | Panel komentar terbuka atau tertutup | Saat gestur 3 jari ditahan stabil selama ~150 ms, sistem mengklik titik koordinat ikon komentar yang telah dikonfigurasi. |
| **US-05** | Pengguna aplikasi desktop TikTok/IG | Membuka telapak tangan 5 jari dengan tenang | Video dijeda (*Pause*) atau dilanjutkan (*Play*) | Saat 5 jari terbuka tanpa gerakan *swipe* selama ~150 ms, sistem menekan `Space` / klik tunggal pada area video. |
| **US-06** | Pemelihara Sistem (*Maintainer*) | Mengatur ulang posisi tombol komentar dan sensitivitas tanpa mengubah kode utama | Sistem tetap akurat meskipun ukuran jendela aplikasi TikTok/IG berubah | Terdapat berkas `config.json` dan tombol kalibrasi cepat (`C` & `V`) pada jendela kamera. |

---

## 3. Spesifikasi Fitur & Pemetaan Gestur

### 3.1 Daftar Gestur & Perilaku
1. **Swipe ke Atas (`SWIPE_UP`) → Scroll ke Bawah (Video Berikutnya)**
   - **Cara melakukan:** Gerakkan tangan dari bawah ke atas secara cepat di depan kamera.
   - **Perilaku sistem:** Mengirimkan perintah gulir ke bawah (`scroll down` / `Down Arrow`).
2. **Swipe ke Bawah (`SWIPE_DOWN`) → Scroll ke Atas (Video Sebelumnya)**
   - **Cara melakukan:** Gerakkan tangan dari atas ke bawah secara cepat di depan kamera.
   - **Perilaku sistem:** Mengirimkan perintah gulir ke atas (`scroll up` / `Up Arrow`).
3. **Bentuk Tangan "OK" (`OK_SIGN`) → Like**
   - **Cara melakukan:** Tempelkan ujung jempol dan ujung telunjuk membentuk lingkaran, sementara 3 jari lainnya (tengah, manis, kelingking) terbuka ke atas.
   - **Perilaku sistem:** Melakukan *double-click* pada koordinat tengah video (mendukung TikTok & Instagram Desktop sekaligus).
4. **Bentuk Tangan 3 Jari (`THREE_FINGERS`) → Buka/Tutup Komentar**
   - **Cara melakukan:** Angkat jari telunjuk, jari tengah, dan jari manis; lipat jempol dan kelingking.
   - **Perilaku sistem:** Mengklik koordinat tombol komentar pada layar aplikasi desktop.
5. **Bentuk Tangan 5 Jari (`FIVE_FINGERS`) → Pause / Play**
   - **Cara melakukan:** Buka kelima jari telapak tangan menghadap kamera dan tahan diam sejenak.
   - **Perilaku sistem:** Menekan tombol `Space` (atau klik tunggal di tengah video sesuai profil) untuk menjeda atau melanjutkan pemutaran.

---

## 4. Pengalaman Pengguna (UX) & Jendela Umpan Balik (HUD)
Agar pengguna tahu apakah tangannya terbaca dengan benar dari jauh, sistem menyediakan jendela *Heads-Up Display* (HUD) mini yang selalu tampil di pojok layar (*Always on Top*):
- Menampilkan pratinjau webcam dengan gambar kerangka tangan (*skeleton*).
- Menampilkan teks status besar: **Gestur Terdeteksi**, **Aksi Terakhir**, dan indikator **Cooldown** (bar hijau/kuning).
- **Pintasan Kalibrasi & Kontrol:**
  - `V`: Simpan posisi kursor mouse saat ini sebagai titik tengah **Video** (untuk *Like* / *Pause*).
  - `C`: Simpan posisi kursor mouse saat ini sebagai titik tombol **Komentar**.
  - `P`: Ganti profil aksi (`desktop_universal`, `tiktok_desktop`, `instagram_desktop`).
  - `M`: Jeda/aktifkan pembacaan gestur sementara (*Mute Gestures*).
  - `Q` / `ESC`: Keluar dari aplikasi.

---

## 5. Metrik Keberhasilan (*Success Metrics*)
- **Latensi Respons:** <= 100 ms dari saat gestur selesai hingga aksi terkirim ke Windows.
- **Akurasi Gestur:** >= 90% keberhasilan deteksi pada jarak 0,5 – 1,5 meter dalam pencahayaan ruangan normal.
- **Tingkat Aksi Berulang Tak Disengaja (*Accidental Double-Trigger*):** 0% berkat mekanisme *Hold-to-Confirm* dan *Cooldown Timer*.
