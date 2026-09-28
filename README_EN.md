# DC4FD NeXAS Script Tool (CLI & GUI)

> 🇮🇩 Versi Bahasa Indonesia: [README.md](README.md)

A toolkit for extracting and injecting script text from visual novels built on the **Circus NeXAS** engine — made for **Da Capo 4 Fortunate Departures (D.C.4 FD)** on Nintendo Switch (Title ID: `010081E0161B2000`).

It ships with a **Smart Character-Width Aware Word Wrapping** algorithm, **Chained Dialogue Cursor Tracking**, and a **Custom Font Configuration** (`system.datu8`) to keep translated text from overflowing, getting cut off mid-word, or overlapping on the Switch screen or in emulators.

---

## ✨ Key Features

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
   - A high-throughput CLI (`nexas_tool.py`) that processes hundreds of files in seconds.

7. **Patch Deployment Automation (`update_patch.bat`)**
   - One click copies modified scripts into the Nintendo Switch LayeredFS structure, installs directly into the Eden/Ryujinx/Yuzu emulator, and packages the release ZIP.

---

## 📋 Requirements

- **Python 3.8** or newer (Windows, Linux, and macOS supported).
- **Zero External Dependencies:** Uses only the Python standard library (`tkinter`, `json`, `struct`, `argparse`, `re`, `unicodedata`, `pathlib`). No `pip install` needed.

---

## 🚀 Usage Guide

### 1. Using the GUI (Easiest)

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

### 2. Using the CLI

#### Extract scripts (`extract`)
- Extract an entire game script folder:
  ```bash
  python nexas_tool.py extract -i "romfs/Script" -o "Json_Export"
  ```
- Extract a single file:
  ```bash
  python nexas_tool.py extract -i "romfs/Script/4fd_hiy191109b.binu8" -o "Json_Export/4fd_hiy191109b.json"
  ```

#### Inject scripts (`insert`)
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

### 3. Patch Deployment Automation (`update_patch.bat`)

The Indonesian patch is distributed **separately from the base game** (no merged NSP) to respect Nintendo's copyright — it ships as a LayeredFS mod, which works on emulators (Citron, Eden, Ryujinx, Yuzu — desktop **and** Android) as well as real consoles running Atmosphere CFW.

#### Ready-made packages (built automatically by `build_release_packages.py`)

| Package | Target | How to Install |
|---|---|---|
| `DC4FD_Indo_Patch_Atmosphere_Switch.zip` | **Real Switch (Atmosphere)** | Extract to the root of your microSD → it lands in `atmosphere/contents/010081E0161B2000/romfs/`. Via PC or DBI. |
| `DC4FD_Indo_Patch_Emulators.zip` | **Eden / Citron / Yuzu / Sudachi — Windows & Android** | Extract into the emulator's `load` folder. Android emulator folder layouts are identical to desktop, so one ZIP works for both. On Windows, extract then double-click the bundled `installer.bat` — it detects your emulator and installs automatically. |
| `DC4FD_Indo_Patch_Ryujinx.zip` | **Ryujinx (desktop)** | Extract into Ryujinx's `mods` folder → becomes `mods/contents/010081E0161B2000/romfs/`. |

Notes:
- **Eden (Windows):** `update_patch.bat` also syncs the patch straight to `%APPDATA%\eden\load\010081E0161B2000\D.C.4 Fortunate Departures Patch\`.
- **Citron / Yuzu:** alternatively right-click the game ➔ *Open Mod Data Location* ➔ paste the package contents there.
- **Why so many `.binu8` files?** The FD NeXAS engine reads RomFS files one by one (it has no archive mechanism like Da Capo 4's Shin-engine `patch.rom`), and LayeredFS works per-path — so the mod must mirror the RomFS structure. The packages above hide that complexity: end users just **extract one ZIP** (or one-click the installer on Windows).

#### Deprecation notice: standalone `.nsp` packages

> [!IMPORTANT]
> By distribution policy, the **base game is never merged** into a single NSP —
> that would redistribute copyrighted Nintendo assets. The Indonesian patch ships
> separately (LayeredFS ZIP above) and users install it into their own
> emulator/console mod folder. NSP building options in `update_patch.bat` are
> disabled. (Technically, the Switch NeXAS engine also lacks the Shin engine's
> `patch.rom` archive mechanism — all mods are strictly per-file RomFS
> replacements.)

#### Using `update_patch.bat`:
1. Make sure `romfs\Script_Mod` contains the injected `.binu8` files.
2. Double-click **`update_patch.bat`**.
3. The script will automatically:
   - Copy the mod binaries into the local LayeredFS structure (`DC4FD_Indo_Patch\romfs\Script\`).
   - Copy the custom font config (`romfs\Custom Config\system.datu8`) into `DC4FD_Indo_Patch\romfs\Config\`.
   - Sync the patch directly into the Eden emulator (`%APPDATA%\eden\load\010081E0161B2000\...`).
   - Repackage `DC4FD_Translation_Patch.zip` (~2.4 MB), ready to distribute.
4. Indonesian OP lyric video (optional): encode per `docs\SPEK_ENCODE_VIDEO.md`, then copy it as `romfs\Movie\4fd_op.mp4` into the patch folder before running the batch.

---

## 📐 Why the 56-Column Wrap Limit?

- The dialogue box on the Switch NeXAS engine has a physical width of about **65 display units**.
- Setting the limit too close to 65 (e.g. 63 or 64) risks broken words: the moment a word crosses column 65, the engine force-breaks it and throws the remainder onto a new line.
- The **56-column visual limit** leaves a ~9-column safety margin. Long words (like `"menggandeng"` or `"memperhitungkan"`) drop to the next line intact, producing clean, readable typography.

---

## 📁 Repository Layout

```text
├── nexas_tool.py                  # Core engine: extraction, injection, opcode parsing, word wrap
├── script_auto_wrap.py            # CJK/fullwidth-aware line wrapping module
├── gui.py                         # Tkinter GUI app with dark theme & wrap presets
├── run_gui.bat                    # 1-click GUI launcher for Windows
├── update_patch.bat               # Batch script: patch deployment automation & ZIP packaging
├── build_release_packages.py      # Builds the 3 multi-platform release zips
├── installer.bat                  # 1-click installer (ships inside the emulator zip)
├── docs/
│   ├── SPEK_ENCODE_VIDEO.md       # Spesifikasi encode video Movie NeXAS (Indonesian)
│   └── SPEK_ENCODE_VIDEO_EN.md    # NeXAS movie encode spec (H.264 Main@L4.1, AAC-LC)
├── romfs/
│   └── Custom Config/
│       └── system.datu8           # Custom visual novel font size config
├── README.md                      # Dokumentasi lengkap (Bahasa Indonesia)
├── README_EN.md                   # Full documentation (English, this file)
└── .gitignore                     # Game & binary cache filters
```

---

## ⚠️ Legal Disclaimer

This repository **only provides developer tooling (tools & scripts)** and **does not include any original game assets or copyrighted script content**. Please dump your own `.binu8` script files from your own legitimately-owned Nintendo Switch cartridge or digital copy.

---

## 🌸 Credits & License

Developed for the **Sakura Symphony Re; Translation** localization project.  
NeXAS engine file-format research builds on community documentation from
[Niflheim](https://github.com/Yggdrasill-Moe/Niflheim) (research on the *Aquarium* title).
Free to use and modify for non-commercial purposes and visual novel preservation.
