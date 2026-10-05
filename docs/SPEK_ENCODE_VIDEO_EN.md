# Movie Video Encode Specification — D.C.4 FD (NeXAS Switch)

> 🇮🇩 Versi Bahasa Indonesia: [SPEK_ENCODE_VIDEO.md](SPEK_ENCODE_VIDEO.md)

This specification is derived directly from `ffprobe` data of the original files
in `romfs/Movie/` — use it as the reference when producing the Indonesian-lyrics
opening video that will go into the mod patch (the `Movie/` folder).

---

## Verified Original Files

| File | Video | Audio |
|---|---|---|
| `4fd_op.mp4` (Opening) | H.264 **Main@L4.1**, 1920x1080, yuv420p, **24 fps**, ~9.8 Mbps | AAC-LC 48 kHz stereo ~317 kbps |
| `asa_ed.mp4` / `hi_ed.mp4` (ED) | H.264 Main@L4.0, 1920x1080, 24 fps, ~0.9 Mbps | AAC-LC 48 kHz stereo ~195 kbps |
| `pmove_l.mp4` (system video) | H.264 Main@L4.0, 1920x1080, 24 fps, ~20 Mbps | AAC-LC 48 kHz stereo ~117 kbps |

Consistency conclusion: all shipped movies are **1920x1080, 24 fps, H.264 Main, yuv420p, AAC-LC 48 kHz stereo**.

---

## Mandatory Encode Target (lyrics video replacing `4fd_op.mp4`)

> ⚠️ **v2 revision (Oct 2026).** The old target (1080p, Main@L4.1, `-r 24` CFR,
> ~9.8 Mbps) proved **too heavy for emulators on mobile SoCs**
> (Snapdragon 6 Gen 1 / Helio G99 on Citron): the decode drops frames, which
> makes the lyrics appear late relative to the audio. The target below replaces it.

```
Video codec   : H.264, profile High, level 3.1
Resolution    : 1280x720 (the engine upscales to screen; far cheaper to decode)
Pixel format  : yuv420p
Frame rate    : FOLLOW THE SOURCE — no `-r`, no forced CFR (`-fps_mode passthrough`)
Video bitrate : CRF 21 + maxrate 4M + bufsize 8M (±3–4 Mbps for a musical OP)
Audio codec   : AAC-LC, 48000 Hz, 2 channels, 160 kbps
Container     : MP4, +faststart
Duration      : identical to the master (A/V timing untouched)
```

### Ready-to-use ffmpeg command

```bash
ffmpeg -i 4fd_op_indo_master.mp4 ^
  -map 0:v:0 -map 0:a:0 ^
  -vf "scale=1280:720:flags=lanczos" -fps_mode passthrough ^
  -c:v libx264 -profile:v high -level 3.1 -preset slow -tune animation ^
  -crf 21 -maxrate 4M -bufsize 8M -pix_fmt yuv420p ^
  -c:a aac -b:a 160k -ar 48000 -ac 2 ^
  -movflags +faststart ^
  -map_metadata -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact ^
  4fd_op_indo_light.mp4
```

Notes:
- **Never add `-r 24`** (or an `fps=24` filter) to the lyrics video. Source
  timestamps are passed through as-is (`-fps_mode passthrough`) so the
  lyric-to-audio sync matches the master exactly.
- `-movflags +faststart` mirrors the `ftyp|moov|mdat` layout of the original
  `4fd_op.mp4` (moov first). The Switch NeXAS engine is known to accept both
  layouts (the original ED files use `isom|free|mdat|moov`), but matching the
  layout of the file being replaced is the safest choice.
- `-map_metadata -1` + `+bitexact` produce deterministic output with no encoder
  metadata the engine doesn't need.

---

## Why the Old Encode Felt Out of Sync on Emulators (v2 analysis)

- The old file: 1080p ~9.6 Mbps Main@L4.1 → heavy decode load. In an emulator
  the game's video decoder runs on the CPU alongside the game + rendering;
  entry-level SoCs can't keep up → video frames get dropped → the burned-in
  lyrics appear increasingly late compared to the audio.
- The old 24 fps CFR file itself was **structurally correct**: A/V
  `start_time` = 0, consistent A/V durations, and **the game's own OP is also
  24 fps**. Quick check: if the stock Japanese OP also desyncs on Citron, the
  cause is 100% decode load (not the fps).
- A 720p ~3–4 Mbps encode cuts the decode load >4× → frame drops disappear and
  the lyrics sync again, without touching the timing.

---

## FPS Above 24 — Testing (optional)

- The FD (NeXAS Switch) OP is 24 fps; there is **no evidence yet** whether the
  NeXAS FD engine forces 24 fps or follows container timestamps. (Comparison:
  the DC4 base game on Switch runs the Shin engine and its OP plays without an
  fps cap.)
- To test, there are two ways to build a **30 fps** variant from the 24 fps master:
  - **Quick test (frame duplication, no artifacts, minutes to encode):** change the
    filter to `scale=1280:720:flags=lanczos,fps=30` — enough to learn engine behavior.
  - **Quality (motion-compensated interpolation, slow to encode):**

```bash
ffmpeg -i 4fd_op_indo_master.mp4 ^
  -vf "scale=1280:720:flags=lanczos,minterpolate=fps=30:mi_mode=mci:scd=fdiff:scd_threshold=10" ^
  -c:v libx264 -profile:v high -level 3.1 -preset slow -tune animation ^
  -crf 21 -maxrate 4M -bufsize 8M -pix_fmt yuv420p ^
  -c:a aac -b:a 160k -ar 48000 -ac 2 ^
  -movflags +faststart ^
  -map_metadata -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact ^
  4fd_op_indo_30fps_test.mp4
```

- How to read the test on the emulator:
  - **Smooth 30 fps + lyrics still in sync** → the engine follows timestamps;
    the 30 fps variant is safe to use. 60 fps is not recommended for the target
    SoCs (2.5× the decode load of 24 fps; 30–50 fps is the realistic range).
  - **Video stretches / lyrics fall behind** → the engine forces 24 fps; use
    the 24 fps variant (the main file) and discard the high-fps one.
  - **30 fps stutters** (especially Helio G99) → stay on 24 fps; the +25% decode
    load is noticeable on big-core-poor SoCs.
- A 60 fps variant (`minterpolate=fps=60`, level 3.2) only makes sense if the
  30 fps test passes **and** the device is strong enough.

---

## Patch Integration Rules

1. The filename **must be exactly** `4fd_op.mp4` (the engine loads by RomFS path `Movie/4fd_op.mp4`).
2. Place it in the LayeredFS patch: `romfs/Movie/4fd_op.mp4` → overrides the original file.
3. Do not lengthen or shorten the duration; sync the lyrics within the original duration.
4. Hardsub (lyrics animated/burned into the frames) is the chosen approach, not soft-sub:
   the engine does not read MP4 subtitle tracks.

---

## Packaging Plan Status (user decision)

- The base game is **not merged** into one big NSP (avoids redistributing copyrighted assets).
- The Indonesian patch (`.binu8` scripts + `system.datu8` + lyrics video) is packaged **separately** from the base game.
- The final packaging format (LayeredFS ZIP vs installable package) is handled in a later
  session; the `exefs/main + romfs/patch.rom` pattern from Shin-engine DC4 **does not apply**
  to FD because FD runs on NeXAS (purely per-file RomFS mods via LayeredFS).

---

## Findings from the NeXAS FD `main` Binary (technical evidence)

Extracting the FD base NSP's ExeFS (titlekey from Eden's `title.keys_autogenerated`,
rights ID `010081E0161B2000000000000000000E`) produced a 3.0 MB `main`
(reference copy: `scratch/fd_main_reference.bin`).

Strings inside the binary prove:
- Present: `CNeXASMovie`, `MovieNXTextureMan`, `Script.dat`, `__GLOBAL.binu8`,
  `PlayerName.datu8`, `GenShinGo`, plus the `binu8`/`datu8` extensions — the engine
  reads RomFS files **one by one** via direct paths.
- Absent: the `ROM2` magic, `patch.rom` strings, or any patch-archive mechanism.
  (The DC4-era `exefs/main + romfs/patch.rom` pattern is Shin-engine NSO code
  patching plus that engine's own ROM2 archive.)

Conclusion: the only viable modding path for FD is **per-file LayeredFS**
(`.binu8` scripts, `system.datu8`, `Movie/*.mp4` videos) — and the OP lyrics video
only needs to replace `Movie/4fd_op.mp4` following the spec above.

Extraction notes (for reproduction):
```bash
hactoolnet -k prod.keys --titlekeys title.keys_autogenerated \
  <program.nca> --exefsdir <out>
# game titlekey: 43D847B6F317CF556DBFE942AC09C8D0 (from the ticket, encrypted)
```
