# DC4FD NeXAS Script Tool (CLI & GUI)

Toolkit ekstraksi dan injeksi naskah skrip visual novel berbasis engine **Circus NeXAS** untuk **Da Capo 4 Fortunate Departures (D.C.4 FD)** versi Nintendo Switch (Title ID: `010081E0161B2000`) dan judul NeXAS lainnya (seperti *Aquarium*).

Dilengkapi dengan algoritma **Smart Character-Width Aware Word Wrapping**, **Chained Dialogue Cursor Tracking**, serta **Konfigurasi Font Kustom** (`system.datu8`) untuk mencegah teks meluber, terpotong, atau bertumpuk di layar konsol Nintendo Switch maupun emulator.

---

## 🌟 Fitur Utama

1. **Ekstraksi Bersih & Terstruktur (`.binu8` ➔ `.json`)**
   - Mengurai bytecode NeXAS secara akurat, memetakan string dialog (`0x0001`) dan nama pembicara (`0x0002` / `0x0003`).
   - Menyaring otomatis aset audio/BGM, file gambar grafik, nama file skrip, dan jump label sistem.
   - Format JSON standar dan bersih:
     - Dialog karakter: `{"name": "Hiyori", "message": "「Halo!」"}`
     - Narasi / monolog: `{"message": "Aku berjalan di koridor sekolah."}`

2. **Smart Character-Width Aware Word Wrapping (Batas Rekomendasi: `56`)**
   - Menghitung lebar visual karakter East Asian / CJK secara presisi (`unicodedata.east_asian_width`): karakter fullwidth (seperti indentasi `\u3000`, tanda kurung `「` `」` `『` `』`, tanda elipsis `……`, dsb.) dihitung tepat sebagai **2 kolom visual**, sementara huruf Latin/ASCII dihitung **1 kolom visual**.
   - **Bebas Pemotongan Kata:** Kata yang tidak muat utuh di ujung baris otomatis diturunkan ke baris berikutnya tanpa terputus di tengah kata.
   - **Mengabaikan Kode Kontrol:** Tag suara (`@v...`), animasi ekspresi (`@h...`), timing jeda (`@t...`), ruby text (`@r...@`), dan line break (`@n`) dipertahankan tanpa dihitung sebagai lebar karakter tampilan.

3. **Chained Dialogue Cursor Tracking (`@k` Continuation)**
   - Pada engine NeXAS, satu kalimat ucapan karakter sering dipecah menjadi beberapa string binary terpisah yang dihubungkan dengan tag `@k` (tunggu klik user untuk efek jeda dramatis).
   - Tool ini melacak posisi kursor visual baris terakhir (`prev_line_col`). String sambungan berikutnya dibungkus secara proporsional sesuai sisa ruang kolom pada baris tersebut (56 - kolom terpakai).

4. **Pemisahan Tegas Dialog vs Narasi**
   - Mendeteksi penutupan kutipan dialog (`」` atau `』`) untuk langsung mereset kursor ke 0.
   - Kalimat narasi tidak akan pernah mewarisi sisa kolom dari ucapan karakter sebelumnya, dan otomatis dipasangi indentasi `\u3000` sesuai standar visual novel Jepang.

5. **Konfigurasi Font Kustom (`system.datu8`)**
   - Sudah termasuk berkas konfigurasi sistem font `romfs/Custom Config/system.datu8` yang telah dioptimalkan ukuran font-nya agar teks alfabet Latin/Indonesia/Inggris proporsional dan nyaman dibaca di layar Nintendo Switch.

6. **Antarmuka Grafis Modern (GUI) & Terminal (CLI)**
   - GUI modern berbasis Tkinter (`gui.py` / `run_gui.bat`) dengan log real-time, tab navigasi, dan tombol preset batas word wrap (56 / 52 / 0).
   - CLI bertenaga tinggi (`nexas_tool.py`) yang sanggup memproses ratusan file dalam hitungan detik.

7. **Automasi Pembuatan Patch Mod (`update_patch.bat`)**
   - Sekali klik untuk menyalin skrip termodifikasi ke struktur LayeredFS Nintendo Switch, menginstal langsung ke emulator Eden/Ryujinx/Yuzu, dan mengompres file ZIP rilis mod.

---

## 📋 Persyaratan Sistem

- **Python 3.8** atau versi yang lebih baru (mendukung Windows, Linux, dan macOS).
- **Zero External Dependencies:** Hanya menggunakan library bawaan Python (`tkinter`, `json`, `struct`, `argparse`, `re`, `unicodedata`, `pathlib`). Tidak perlu `pip install`.

---

## 🚀 Panduan Penggunaan

### 1. Menggunakan GUI (Paling Praktis)

Cukup jalankan **`run_gui.bat`** (Windows) atau jalankan perintah:
```bash
python gui.py
```

- **Tab Extract Script:**
  1. Pilih file binary tunggal (`.binu8`) atau folder skrip asli (misal: folder `romfs/Script`).
  2. Tentukan folder tujuan output JSON.
  3. Klik **"Mulai Ekstraksi"**.
- **Tab Insert Script:**
  1. Pilih file/folder `.binu8` asli (Base Script).
  2. Pilih file/folder `.json` hasil terjemahan.
  3. Tentukan folder output untuk binary hasil modifikasi (misal: `romfs/Script_Mod`).
  4. Tentukan batas Word Wrap (Gunakan preset **`56 (Aman / Rekomendasi)`**).
  5. Klik **"Mulai Injeksi"**.

---

### 2. Menggunakan CLI (Command Line Interface)

#### Ekstraksi Skrip (`extract`)
- **Ekstrak seluruh folder skrip game:**
  ```bash
  python nexas_tool.py extract -i "romfs/Script" -o "Json_Export"
  ```
- **Ekstrak satu file saja:**
  ```bash
  python nexas_tool.py extract -i "romfs/Script/4fd_hiy191109b.binu8" -o "Json_Export/4fd_hiy191109b.json"
  ```

#### Injeksi Skrip (`insert`)
- **Injeksi seluruh folder dengan word wrap 56 kolom (Rekomendasi):**
  ```bash
  python nexas_tool.py insert -b "romfs/Script" -j "Json_Translation" -o "romfs/Script_Mod" -w 56
  ```
- **Injeksi satu file saja:**
  ```bash
  python nexas_tool.py insert -b "romfs/Script/4fd_hiy191109b.binu8" -j "Json_Translation/4fd_hiy191109b.json" -o "romfs/Script_Mod/4fd_hiy191109b.binu8" -w 56
  ```
- **Injeksi tanpa word wrap otomatis (menggunakan wrap manual dari JSON):**
  ```bash
  python nexas_tool.py insert -b "romfs/Script" -j "Json_Translation" -o "romfs/Script_Mod" -w 0
  ```

---

### 3. Automasi Deployment Patch (`update_patch.bat`)

Jika Anda bermain menggunakan emulator Eden / Ryujinx di PC atau ingin menyiapkan berkas mod LayeredFS untuk konsol Nintendo Switch (Atmosphere):

1. Pastikan folder `romfs\Script_Mod` telah berisi file `.binu8` hasil injeksi.
2. Dobel-klik **`update_patch.bat`**.
3. Skrip otomatis akan:
   - Menyalin binary mod ke struktur LayeredFS lokal (`DC4FD_Indo_Patch\romfs\Script\`).
   - Menyalin konfigurasi font kustom (`romfs\Custom Config\system.datu8`) ke `DC4FD_Indo_Patch\romfs\Config\`.
   - Menyinkronkan patch langsung ke folder load emulator Eden (`%APPDATA%\eden\load\010081E0161B2000\...`).
   - Mengemas ulang berkas `DC4FD_Translation_Patch.zip` yang siap disalin ke kartu microSD konsol Nintendo Switch (`atmosphere/contents/010081E0161B2000/`).

---

## 📐 Penjelasan Batas Word Wrap (Mengapa 56 Kolom?)

- Area dialog visual novel pada engine Circus NeXAS Nintendo Switch memiliki batas fisik layar sekitar **65 unit lebar tampilan**.
- Menggunakan batas yang terlalu mendekati 65 (seperti 63 atau 64) berisiko memotong kata panjang, karena jika sebuah kata melampaui kolom ke-65, engine game akan memotong huruf di ujung baris secara paksa dan melempar sisa kata ke baris baru.
- **Batas 56 Kolom Visual** memberikan bantalan aman sekitar 9 kolom. Jika ada kata panjang (seperti `"menggandeng"` atau `"memperhitungkan"`), seluruh kata akan diturunkan utuh ke baris berikutnya, menghasilkan tipografi teks yang rapi dan nyaman dibaca.

---

## 📁 Struktur Berkas Repositori

```text
├── nexas_tool.py                  # Engine inti ekstraksi, injeksi, parsing opcode & word wrap
├── script_auto_wrap.py            # Modul algoritma pembungkus baris teks CJK/Fullwidth
├── gui.py                         # Aplikasi visual Tkinter dengan dark theme & preset wrap
├── run_gui.bat                    # Launcher praktis 1-klik untuk GUI di Windows
├── update_patch.bat               # Script batch otomatisasi deployment patch & packaging ZIP
├── romfs/
│   └── Custom Config/
│       └── system.datu8           # Konfigurasi ukuran font kustom visual novel
├── README.md                      # Panduan lengkap dokumentasi penggunaan
└── .gitignore                     # Filter berkas game & cache biner
```

---

## ⚠️ Peringatan Hukum (Disclaimer)

Repositori ini **hanya menyediakan perkakas pengembang (tools & scripts)** dan **tidak menyertakan aset game asli ataupun naskah cerita berhak cipta**. Harap lakukan dump berkas naskah (`.binu8`) secara mandiri dari cartridge atau salinan digital game Nintendo Switch resmi milik Anda sendiri.

---

## 🌸 Kredit & Lisensi

Dikembangkan untuk proyek lokalisasi **Sakura Symphony Re; Translation**.  
Bebas digunakan dan dimodifikasi untuk keperluan non-komersial dan pelestarian visual novel.
