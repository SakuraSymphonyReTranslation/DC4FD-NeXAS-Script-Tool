# DC4FD NeXAS Script Tool (CLI & GUI)

<p align="center">
  <a href="#-versi-bahasa-indonesia">🇮🇩 Bahasa Indonesia</a> &nbsp;·&nbsp;
  <a href="#-english-version">🇬🇧 English</a>
</p>

---

<a id="-versi-bahasa-indonesia"></a>

## 🇮🇩 Versi Bahasa Indonesia

> 🌐 Pilih bahasa: [🇮🇩 Bahasa Indonesia](#-versi-bahasa-indonesia) · [🇬🇧 English](#-english-version)

Toolkit ekstraksi dan injeksi naskah skrip visual novel berbasis engine **Circus NeXAS** untuk **Da Capo 4 Fortunate Departures (D.C.4 FD)** versi Nintendo Switch (Title ID: `010081E0161B2000`).

Dilengkapi dengan algoritma **Smart Character-Width Aware Word Wrapping**, **Chained Dialogue Cursor Tracking**, serta **Konfigurasi Font Kustom** (`system.datu8`) untuk mencegah teks meluber, terpotong, atau bertumpuk di layar konsol Nintendo Switch maupun emulator.

---

### 🌟 Fitur Utama

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
   - 4 tab lengkap: **Extract**, **Insert**, **UI Translation** (6 mode: extract, audit PNG, export PNG, apply config, apply SPM, pack PNG), dan **Build Patch Lengkap** (satu klik menggabungkan scenario + UI + video lirik ke satu patch, opsi ZIP rilis & instal otomatis ke Eden).
   - CLI bertenaga tinggi (`nexas_tool.py`) yang sanggup memproses ratusan file dalam hitungan detik.

7. **Automasi Pembuatan Patch Mod (`update_patch.bat`)**
   - Sekali klik untuk menyalin skrip termodifikasi ke struktur LayeredFS Nintendo Switch, menginstal langsung ke emulator Eden/Ryujinx/Yuzu, dan mengompres file ZIP rilis mod.

8. **Perkakas Terjemahan Antarmuka (UI) — `ui_translation_tool.py`**
   - Ekstrak & terapkan teks UI (`.datu8` Config via CSV, `.spm` System via penggantian string), audit PNG ber-teks Jepang, serta ekspor PNG untuk diedit di Photoshop/GIMP dengan konversi format otomatis saat dikemas kembali ke patch.
   - Panduan lengkap: [README_UI_TRANSLATION.md](README_UI_TRANSLATION.md).

9. **Builder Patch Lengkap — `build_full_patch.py`**
   - Satu perintah menggabungkan SEMUA komponen terjemahan ke satu patch LayeredFS: naskah scenario (`.binu8`), UI Config (`.datu8`), UI layout (`.spm`), tekstur PNG hasil edit, dan video lirik OP Indonesia (`Movie/4fd_op.mp4`) — komponen yang belum ada dilewati dengan jelas, jadi patch selalu valid.
   - `python build_full_patch.py --zip --install` langsung membuat 3 paket ZIP rilis dan memasang ke emulator Eden.

---

### 📋 Persyaratan Sistem

- **Python 3.8** atau versi yang lebih baru (mendukung Windows, Linux, dan macOS).
- **Zero External Dependencies:** Hanya menggunakan library bawaan Python (`tkinter`, `json`, `struct`, `argparse`, `re`, `unicodedata`, `pathlib`). Tidak perlu `pip install`.

---

### 🚀 Panduan Penggunaan

#### 1. Menggunakan GUI (Paling Praktis)

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

#### 2. Menggunakan CLI (Command Line Interface)

**Ekstraksi Skrip (`extract`)**
- **Ekstrak seluruh folder skrip game:**
  ```bash
  python nexas_tool.py extract -i "romfs/Script" -o "Json_Export"
  ```
- **Ekstrak satu file saja:**
  ```bash
  python nexas_tool.py extract -i "romfs/Script/4fd_hiy191109b.binu8" -o "Json_Export/4fd_hiy191109b.json"
  ```

**Injeksi Skrip (`insert`)**
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

#### 3. Automasi Deployment Patch (`update_patch.bat`)

Tool ini mendukung **dua format patch resmi** yang kompatibel dengan emulator (Citron, Eden, Ryujinx, Yuzu) maupun konsol Nintendo Switch asli (Atmosphere CFW):

**A. Format 1: LayeredFS Mod — *Format Standar & Sangat Ringan***
Format ini hanya berisi file teks modifikasi (`Script/` dan `Config/`), sangat cepat diunduh, legal dibagikan secara publik (tanpa copyright game), dan didukung langsung oleh semua sistem.

Tersedia **3 varian paket siap pakai** (dibuat otomatis oleh `build_release_packages.py`):

| Paket | Untuk | Cara Pasang |
|---|---|---|
| `DC4FD_Indo_Patch_Atmosphere_Switch.zip` | **Switch asli (Atmosphere)** | Ekstrak ke root microSD → otomatis menjadi `atmosphere/contents/010081E0161B2000/romfs/`. Bisa via PC atau DBI. |
| `DC4FD_Indo_Patch_Emulators.zip` | **Eden / Citron / Yuzu / Sudachi — Windows & Android** | Ekstrak ke folder `load` milik emulator. Struktur folder emulator Android identik dengan desktop, jadi 1 ZIP sama untuk keduanya. Di Windows, ekstrak lalu dobel-klik `installer.bat` — emulator terdeteksi dan patch terpasang otomatis. |
| `DC4FD_Indo_Patch_Ryujinx.zip` | **Ryujinx desktop** | Ekstrak ke folder `mods` Ryujinx → menjadi `mods/contents/010081E0161B2000/romfs/`. |

Catatan:
- **Emulator Eden (Windows):** juga otomatis disalin oleh `update_patch.bat` ke `%APPDATA%\eden\load\010081E0161B2000\D.C.4 Fortunate Departures Patch\`.
- **Emulator Citron / Yuzu:** alternatif: klik kanan game ➔ *Open Mod Data Location* ➔ tempel isi paket ke dalamnya.
- **Mengapa banyak file `.binu8`?** Engine NeXAS FD membaca RomFS per-file (tidak punya mekanisme arsip seperti `patch.rom` milik engine Shin pada DC4) dan LayeredFS bekerja per-path — jadi mod memang berbentuk file yang meniru struktur RomFS. Kerumitan itu sudah ditangani paket di atas: pengguna akhir cukup **ekstrak 1 ZIP** (atau 1 klik installer di Windows).

**B. Format 2: Standalone Installable Package (`.nsp`) — *Tidak Lagi Didukung***

> [!IMPORTANT]
> Berdasarkan kebijakan distribusi, **base game tidak digabung** ke dalam satu NSP
> besar agar tidak melanggar hak cipta Nintendo. Patch bahasa Indonesia
> **distribusikan terpisah** dalam Format 1 (LayeredFS ZIP) di atas, dan pengguna
> memasangnya dengan menyalin isi ZIP ke folder mod emulator/konsol masing-masing.
> Opsi pembuatan NSP pada `update_patch.bat` telah dinonaktifkan.
> (Secara teknis, engine NeXAS versi Switch juga tidak mendukung mekanisme arsip
> patch seperti `patch.rom` milik engine Shin pada Da Capo 4 — seluruh mod
> bekerja murni lewat penggantian file RomFS per-file.)

**Cara Menggunakan `update_patch.bat`:**
1. Pastikan folder `romfs\Script_Mod` telah berisi file `.binu8` hasil injeksi.
2. Dobel-klik **`update_patch.bat`**.
3. Skrip otomatis akan:
   - Menyalin binary mod ke struktur LayeredFS lokal (`DC4FD_Indo_Patch\romfs\Script\`).
   - Menyalin konfigurasi font kustom (`romfs\Custom Config\system.datu8`) ke `DC4FD_Indo_Patch\romfs\Config\`.
   - Menyinkronkan patch langsung ke emulator Eden (`%APPDATA%\eden\load\010081E0161B2000\...`).
   - Mengemas ulang berkas `DC4FD_Translation_Patch.zip` (~2.4 MB) siap distribusi.
4. Video lirik OP Indonesia (opsional): encode video sesuai `docs\SPEK_ENCODE_VIDEO.md`, lalu salin sebagai `romfs\Movie\4fd_op.mp4` pada folder patch sebelum menjalankan batch.

---

### 📐 Penjelasan Batas Word Wrap (Mengapa 56 Kolom?)

- Area dialog visual novel pada engine Circus NeXAS Nintendo Switch memiliki batas fisik layar sekitar **65 unit lebar tampilan**.
- Menggunakan batas yang terlalu mendekati 65 (seperti 63 atau 64) berisiko memotong kata panjang, karena jika sebuah kata melampaui kolom ke-65, engine game akan memotong huruf di ujung baris secara paksa dan melempar sisa kata ke baris baru.
- **Batas 56 Kolom Visual** memberikan bantalan aman sekitar 9 kolom. Jika ada kata panjang (seperti `"menggandeng"` atau `"memperhitungkan"`), seluruh kata akan diturunkan utuh ke baris berikutnya, menghasilkan tipografi teks yang rapi dan nyaman dibaca.

---

### 📁 Struktur Berkas Repositori

```text
├── nexas_tool.py                  # Engine inti ekstraksi, injeksi, parsing opcode & word wrap
├── script_auto_wrap.py            # Modul algoritma pembungkus baris teks CJK/Fullwidth
├── gui.py                         # Aplikasi visual Tkinter dengan dark theme & preset wrap
├── run_gui.bat                    # Launcher praktis 1-klik untuk GUI di Windows
├── update_patch.bat               # Script batch otomatisasi deployment patch & packaging ZIP
├── build_release_packages.py      # Membangun 3 paket ZIP rilis multi-platform
├── installer.bat                  # Installer 1-klik (ikut di dalam paket ZIP emulator)
├── ui_translation_tool.py         # Ekstrak/terapkan teks UI (.datu8/.spm) + audit & pack PNG UI
├── build_full_patch.py            # Builder patch lengkap: scenario + UI + video → 1 patch
├── README_UI_TRANSLATION.md       # Panduan terjemahan UI (peta file, alur kerja, checklist)
├── docs/
│   ├── SPEK_ENCODE_VIDEO.md       # Spesifikasi encode video Movie NeXAS (Indonesia)
│   └── SPEK_ENCODE_VIDEO_EN.md    # Movie encode spec (English)
├── romfs/
│   └── Custom Config/
│       └── system.datu8           # Konfigurasi ukuran font kustom visual novel
├── README.md                      # Panduan lengkap bilingual (ID + EN) — file ini
└── .gitignore                     # Filter berkas game & cache biner
```

---

### ⚠️ Peringatan Hukum (Disclaimer)

Repositori ini **hanya menyediakan perkakas pengembang (tools & scripts)** dan **tidak menyertakan aset game asli ataupun naskah cerita berhak cipta**. Harap lakukan dump berkas naskah (`.binu8`) secara mandiri dari cartridge atau salinan digital game Nintendo Switch resmi milik Anda sendiri.

---

### 🌸 Kredit & Lisensi

Dikembangkan untuk proyek lokalisasi **Sakura Symphony Re; Translation**.  
Riset format berkas engine NeXAS mengacu pada dokumentasi komunitas
[Niflheim](https://github.com/Yggdrasill-Moe/Niflheim) (riset judul *Aquarium*).
Bebas digunakan dan dimodifikasi untuk keperluan non-komersial dan pelestarian visual novel.

---

[⬆️ Kembali ke pilihan bahasa](#dc4fd-nexas-script-tool-cli--gui)

---

<a id="-english-version"></a>

## 🇬🇧 English Version

> 🌐 Choose language: [🇮🇩 Bahasa Indonesia](#-versi-bahasa-indonesia) · [🇬🇧 English](#-english-version)

A toolkit for extracting and injecting script text from visual novels built on the **Circus NeXAS** engine — made for **Da Capo 4 Fortunate Departures (D.C.4 FD)** on Nintendo Switch (Title ID: `010081E0161B2000`).

It ships with a **Smart Character-Width Aware Word Wrapping** algorithm, **Chained Dialogue Cursor Tracking**, and a **Custom Font Configuration** (`system.datu8`) to keep translated text from overflowing, getting cut off mid-word, or overlapping on the Switch screen or in emulators.

---

### ✨ Key Features

1. **Clean, Structured Extraction (`.binu8` ➔ `.json`)**
   - Accurately parses NeXAS bytecode, mapping dialogue strings (`0x0001`) and speaker names (`0x0002` / `0x0003`).
   - Automatically filters out audio/BGM assets, graphic files, script filenames, and system jump labels.
   - Produces a clean, standard JSON format:
     - Character dialogue: `{"name": "Hiyori", "message": "「Hello!」"}`
     - Narration / monologue: `{"message": "I walked down the school corridor."}`

2. **Smart Character-Width Aware Word Wrapping (Recommended Limit: `56`)**
   - Precisely measures East Asian / CJK visual character widths using `unicodedata.east_asian_width`: fullwidth characters (like the `\u3000` ideographic space, brackets `「` `」` `『` `』`, ellipsis `……`, etc.) count as exactly **2 visual columns**, while Latin/ASCII letters count as **1 column**.
   - **No Mid-Word Breaks:** If a word doesn't fit at the end of a line, the whole word moves to the next line instead of being split.
   - **Control Codes Ignored:** Voice tags (`@v...`), expression animations (`@h...`), pause timing (`@t...`), ruby text (`@r...@`), and line breaks (`@n`) are preserved but never counted toward display width.

3. **Chained Dialogue Cursor Tracking (`@k` Continuations)**
   - On the NeXAS engine, a single spoken line is often split across multiple binary strings chained by `@k` tags (wait for click, for dramatic pauses).
   - The tool tracks the last line's visual cursor position (`prev_line_col`). Continuation strings are wrapped proportionally to the remaining column space on that line (56 − used columns).

4. **Strict Dialogue vs Narration Separation**
   - Detects closing quote marks (`」` or `』`) to reset the cursor to 0 immediately.
   - Narration lines never inherit leftover columns from the preceding character speech, and automatically receive the `\u3000` indentation used by Japanese visual novels.

5. **Custom Font Configuration (`system.datu8`)**
   - Includes a pre-tuned `romfs/Custom Config/system.datu8` system font config, with sizes optimized so Latin/Indonesian/English text renders proportionally and comfortably on the Switch screen.

6. **Modern GUI & CLI**
   - A polished Tkinter GUI (`gui.py` / `run_gui.bat`) with a real-time log, tab navigation, and word-wrap preset buttons (56 / 52 / 0).
   - 4 complete tabs: **Extract**, **Insert**, **UI Translation** (6 modes: extract, PNG audit, PNG export, apply config, apply SPM, pack PNG), and **Full Patch Builder** (one click combines scenario + UI + lyric video into a single patch, with release ZIP & automatic Eden install options).
   - A high-throughput CLI (`nexas_tool.py`) that processes hundreds of files in seconds.

7. **Patch Deployment Automation (`update_patch.bat`)**
   - One click copies modified scripts into the Nintendo Switch LayeredFS structure, installs directly into the Eden/Ryujinx/Yuzu emulator, and packages the release ZIP.

8. **UI Translation Tooling — `ui_translation_tool.py`**
   - Extract & apply UI text (Config `.datu8` via CSV, System `.spm` via string replacement), audit Japanese-text PNGs, and export PNGs for Photoshop/GIMP editing with automatic format conversion when packing back into the patch.
   - Full guide: [README_UI_TRANSLATION.md](README_UI_TRANSLATION.md).

9. **Full Patch Builder — `build_full_patch.py`**
   - One command combines ALL translation components into a single LayeredFS patch: scenario scripts (`.binu8`), UI Config (`.datu8`), UI layout (`.spm`), edited PNG textures, and the Indonesian OP lyric video (`Movie/4fd_op.mp4`) — missing components are clearly skipped, so the patch stays valid.
   - `python build_full_patch.py --zip --install` builds the 3 release ZIPs and installs into the Eden emulator in one go.

---

### 📋 Requirements

- **Python 3.8** or newer (Windows, Linux, and macOS supported).
- **Zero External Dependencies:** Uses only the Python standard library (`tkinter`, `json`, `struct`, `argparse`, `re`, `unicodedata`, `pathlib`). No `pip install` needed.

---

### 🚀 Usage Guide

#### 1. Using the GUI (Easiest)

Run **`run_gui.bat`** (Windows) or:

```bash
python gui.py
```

- **Extract Script tab:**
  1. Pick a single binary file (`.binu8`) or the original script folder (e.g. `romfs/Script`).
  2. Choose the output folder for JSON.
  3. Click **"Mulai Ekstraksi"** (Start Extraction).
- **Insert Script tab:**
  1. Pick the original `.binu8` file/folder (Base Script).
  2. Pick the translated `.json` file/folder.
  3. Choose the output folder for the modified binaries (e.g. `romfs/Script_Mod`).
  4. Set the Word Wrap limit (use the **`56 (Aman / Rekomendasi)`** = Safe/Recommended preset).
  5. Click **"Mulai Injeksi"** (Start Injection).

---

#### 2. Using the CLI

**Extract scripts (`extract`)**
- Extract an entire game script folder:
  ```bash
  python nexas_tool.py extract -i "romfs/Script" -o "Json_Export"
  ```
- Extract a single file:
  ```bash
  python nexas_tool.py extract -i "romfs/Script/4fd_hiy191109b.binu8" -o "Json_Export/4fd_hiy191109b.json"
  ```

**Inject scripts (`insert`)**
- Inject an entire folder with 56-column word wrap (recommended):
  ```bash
  python nexas_tool.py insert -b "romfs/Script" -j "Json_Translation" -o "romfs/Script_Mod" -w 56
  ```
- Inject a single file:
  ```bash
  python nexas_tool.py insert -b "romfs/Script/4fd_hiy191109b.binu8" -j "Json_Translation/4fd_hiy191109b.json" -o "romfs/Script_Mod/4fd_hiy191109b.binu8" -w 56
  ```
- Inject without auto word wrap (use the manual line breaks already in the JSON):
  ```bash
  python nexas_tool.py insert -b "romfs/Script" -j "Json_Translation" -o "romfs/Script_Mod" -w 0
  ```

---

#### 3. Patch Deployment Automation (`update_patch.bat`)

The Indonesian patch is distributed **separately from the base game** (no merged NSP) to respect Nintendo's copyright — it ships as a LayeredFS mod, which works on emulators (Citron, Eden, Ryujinx, Yuzu — desktop **and** Android) as well as real consoles running Atmosphere CFW.

**Ready-made packages (built automatically by `build_release_packages.py`)**

| Package | Target | How to Install |
|---|---|---|
| `DC4FD_Indo_Patch_Atmosphere_Switch.zip` | **Real Switch (Atmosphere)** | Extract to the root of your microSD → it lands in `atmosphere/contents/010081E0161B2000/romfs/`. Via PC or DBI. |
| `DC4FD_Indo_Patch_Emulators.zip` | **Eden / Citron / Yuzu / Sudachi — Windows & Android** | Extract into the emulator's `load` folder. Android emulator folder layouts are identical to desktop, so one ZIP works for both. On Windows, extract then double-click the bundled `installer.bat` — it detects your emulator and installs automatically. |
| `DC4FD_Indo_Patch_Ryujinx.zip` | **Ryujinx (desktop)** | Extract into Ryujinx's `mods` folder → becomes `mods/contents/010081E0161B2000/romfs/`. |

Notes:
- **Eden (Windows):** `update_patch.bat` also syncs the patch straight to `%APPDATA%\eden\load\010081E0161B2000\D.C.4 Fortunate Departures Patch\`.
- **Citron / Yuzu:** alternatively right-click the game ➔ *Open Mod Data Location* ➔ paste the package contents there.
- **Why so many `.binu8` files?** The FD NeXAS engine reads RomFS files one by one (it has no archive mechanism like Da Capo 4's Shin-engine `patch.rom`), and LayeredFS works per-path — so the mod must mirror the RomFS structure. The packages above hide that complexity: end users just **extract one ZIP** (or one-click the installer on Windows).

**Deprecation notice: standalone `.nsp` packages**

> [!IMPORTANT]
> By distribution policy, the **base game is never merged** into a single NSP —
> that would redistribute copyrighted Nintendo assets. The Indonesian patch ships
> separately (LayeredFS ZIP above) and users install it into their own
> emulator/console mod folder. NSP building options in `update_patch.bat` are
> disabled. (Technically, the Switch NeXAS engine also lacks the Shin engine's
> `patch.rom` archive mechanism — all mods are strictly per-file RomFS
> replacements.)

**Using `update_patch.bat`:**
1. Make sure `romfs\Script_Mod` contains the injected `.binu8` files.
2. Double-click **`update_patch.bat`**.
3. The script will automatically:
   - Copy the mod binaries into the local LayeredFS structure (`DC4FD_Indo_Patch\romfs\Script\`).
   - Copy the custom font config (`romfs\Custom Config\system.datu8`) into `DC4FD_Indo_Patch\romfs\Config\`.
   - Sync the patch directly into the Eden emulator (`%APPDATA%\eden\load\010081E0161B2000\...`).
   - Repackage `DC4FD_Translation_Patch.zip` (~2.4 MB), ready to distribute.
4. Indonesian OP lyric video (optional): encode per `docs\SPEK_ENCODE_VIDEO_EN.md`, then copy it as `romfs\Movie\4fd_op.mp4` into the patch folder before running the batch.

---

### 📐 Why the 56-Column Wrap Limit?

- The dialogue box on the Switch NeXAS engine has a physical width of about **65 display units**.
- Setting the limit too close to 65 (e.g. 63 or 64) risks broken words: the moment a word crosses column 65, the engine force-breaks it and throws the remainder onto a new line.
- The **56-column visual limit** leaves a ~9-column safety margin. Long words (like `"menggandeng"` or `"memperhitungkan"`) drop to the next line intact, producing clean, readable typography.

---

### 📁 Repository Layout

```text
├── nexas_tool.py                  # Core engine: extraction, injection, opcode parsing, word wrap
├── script_auto_wrap.py            # CJK/fullwidth-aware line wrapping module
├── gui.py                         # Tkinter GUI app with dark theme & wrap presets
├── run_gui.bat                    # 1-click GUI launcher for Windows
├── update_patch.bat               # Batch script: patch deployment automation & ZIP packaging
├── build_release_packages.py      # Builds the 3 multi-platform release zips
├── installer.bat                  # 1-click installer (ships inside the emulator zip)
├── ui_translation_tool.py         # Extract/apply UI text (.datu8/.spm) + UI PNG audit & pack
├── build_full_patch.py            # Full patch builder: scenario + UI + video → 1 patch
├── README_UI_TRANSLATION.md       # UI translation guide (file map, workflow, checklist)
├── docs/
│   ├── SPEK_ENCODE_VIDEO.md       # Spesifikasi encode video Movie NeXAS (Indonesian)
│   └── SPEK_ENCODE_VIDEO_EN.md    # NeXAS movie encode spec (H.264 Main@L4.1, AAC-LC)
├── romfs/
│   └── Custom Config/
│       └── system.datu8           # Custom visual novel font size config
├── README.md                      # Bilingual documentation (ID + EN) — this file
└── .gitignore                     # Game & binary cache filters
```

---

### ⚠️ Legal Disclaimer

This repository **only provides developer tooling (tools & scripts)** and **does not include any original game assets or copyrighted script content**. Please dump your own `.binu8` script files from your own legitimately-owned Nintendo Switch cartridge or digital copy.

---

### 🌸 Credits & License

Developed for the **Sakura Symphony Re; Translation** localization project.  
NeXAS engine file-format research builds on community documentation from
[Niflheim](https://github.com/Yggdrasill-Moe/Niflheim) (research on the *Aquarium* title).
Free to use and modify for non-commercial purposes and visual novel preservation.

---

[⬆️ Back to language picker](#dc4fd-nexas-script-tool-cli--gui)
