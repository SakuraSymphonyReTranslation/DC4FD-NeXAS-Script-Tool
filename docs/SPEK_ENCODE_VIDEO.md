# Spesifikasi Encode Video Movie — D.C.4 FD (NeXAS Switch)

> 🇬🇧 English version: [SPEK_ENCODE_VIDEO_EN.md](SPEK_ENCODE_VIDEO_EN.md)

Spesifikasi ini diturunkan langsung dari probe (`ffprobe`) file asli di
`romfs/Movie/` — dipakai sebagai acuan membuat video opening berlirik Indonesia
yang nanti dimasukkan ke patch mod (folder `Movie/`).

---

## Data Asli Terverifikasi

| File | Video | Audio |
|---|---|---|
| `4fd_op.mp4` (Opening) | H.264 **Main@L4.1**, 1920x1080, yuv420p, **24 fps**, ~9.8 Mbps | AAC-LC 48 kHz stereo ~317 kbps |
| `asa_ed.mp4` / `hi_ed.mp4` (ED) | H.264 Main@L4.0, 1920x1080, 24 fps, ~0.9 Mbps | AAC-LC 48 kHz stereo ~195 kbps |
| `pmove_l.mp4` (video sistem) | H.264 Main@L4.0, 1920x1080, 24 fps, ~20 Mbps | AAC-LC 48 kHz stereo ~117 kbps |

Kesimpulan konsistensi: seluruh movie bawaan = **1920x1080, 24 fps, H.264 Main, yuv420p, AAC-LC 48 kHz stereo**.

---

## Target Encode Wajib (video lirik pengganti `4fd_op.mp4`)

> ⚠️ **Revisi v2 (Okt 2026).** Target lama (1080p, Main@L4.1, `-r 24` CFR,
> ~9.8 Mbps) terbukti **terlalu berat untuk emulator di SoC mobile**
> (Snapdragon 6 Gen 1 / Helio G99 pada Citron): decode-nya drop frame sehingga
> lirik terasa telanjur dibanding audio. Target di bawah menggantikannya.

```
Codec video   : H.264, profile High, level 3.1
Resolusi      : 1280x720 (engine meng-upscale ke layar; jauh lebih ringan didecode)
Pixel format  : yuv420p
Frame rate    : MENGIKUTI SUMBER — tanpa `-r`, tanpa paksaan CFR (`-fps_mode passthrough`)
Bitrate video : CRF 21 + maxrate 4M + bufsize 8M (hasil ±3–4 Mbps untuk OP musikal)
Codec audio   : AAC-LC, 48000 Hz, 2 channel, 160 kbps
Container     : MP4, +faststart
Duration      : sama dengan master (timing A/V tidak diubah sama sekali)
```

### Perintah ffmpeg siap pakai

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

Catatan:
- **Jangan pernah menambahkan `-r 24`** (atau filter `fps=24`) pada video lirik.
  Timestamp sumber diteruskan apa adanya (`-fps_mode passthrough`) supaya
  sinkronisasi lirik vs audio persis mengikuti master.
- `-movflags +faststart` meniru struktur `ftyp|moov|mdat` milik `4fd_op.mp4` asli
  (moov di depan). Engine NeXAS Switch diketahui menerima keduanya (file ED asli
  memakai `isom|free|mdat|moov`), tapi mengikuti struktur file yang digantikan paling aman.
- `-map_metadata -1` + `+bitexact` membuat output deterministik tanpa metadata encoder
  yang tidak diperlukan engine.

---

## Kenapa Encode Lama Terasa Desinkron di Emulator (analisis v2)

- File lama: 1080p ~9.6 Mbps Main@L4.1 → beban decode besar. Di emulator,
  decoder video game berjalan di CPU bersama game + rendering; SoC entry-mid
  tidak real-time → frame video terlewat → lirik (yang ter-burn ke gambar)
  tampak makin telat dibanding audio.
- Struktur file 24 fps CFR lama sendiri **benar**: A/V `start_time` = 0,
  durasi A/V konsisten, dan **OP asli game juga 24 fps**. Uji cepat: kalau OP
  Jepang bawaan juga desinkron di Citron, penyebabnya 100% beban decode (bukan fps).
- Encode 720p ±3–4 Mbps memangkas beban decode >4× → frame drop hilang,
  lirik kembali sinkron tanpa menyentuh timing.

---

## FPS di Atas 24 — Pengujian (opsional)

- OP bawaan FD (NeXAS Switch) 24 fps; **belum ada bukti** apakah engine NeXAS FD
  memaksa 24 fps atau mengikuti timestamp kontainer. (Pembanding: DC4 base game
  Switch memakai engine Shin dan OP-nya jalan tanpa cap fps.)
- Untuk menguji, tersedia dua cara membuat varian **30 fps** dari master 24 fps:
  - **Tes cepat (duplikasi frame, tanpa artefak, encode menit):** ganti filter jadi
    `scale=1280:720:flags=lanczos,fps=30` — cukup untuk mengetahui perilaku engine.
  - **Kualitas (interpolasi motion-compensated, encode lama):**

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

- Cara membaca hasil tes di emulator:
  - **30 fps mulus + lirik tetap sinkron** → engine mengikuti timestamp; boleh
    pakai varian 30 fps. 60 fps tidak disarankan untuk SoC target (beban decode
    2,5× dari 24 fps; 30–50 fps pilihan realistis).
  - **Video melar / lirik makin telat** → engine memaksa 24 fps; pakai varian
    24 fps (file utama), buang varian fps tinggi.
  - **30 fps tersendat** (terutama Helio G99) → tetap pakai 24 fps; beban decode
    +25% dari 24 fps cukup terasa di SoC 4 core besar.
- Varian 60 fps (`minterpolate=fps=60`, level 3.2) hanya masuk akal kalau tes
  30 fps lolos **dan** device-nya kuat.

---

## Patch Integration Rules

1. Nama file **harus persis** `4fd_op.mp4` (engine memuat berdasarkan path RomFS `Movie/4fd_op.mp4`).
2. Ditempatkan di patch LayeredFS: `romfs/Movie/4fd_op.mp4` → meng-override file asli.
3. Jangan menambah/mengurangi durasi; sinkronisasi lirik dibuat di dalam durasi asli.
4. Hardsub (lirik dianimasikan/dibakar ke frame) dipilih, bukan soft-sub:
   engine tidak membaca track subtitle MP4.

---

## Status Rencana Packaging (keputusan pengguna)

- Base game **tidak digabung** ke dalam satu NSP besar (menghindari redistribusi aset berhak cipta).
- Patch Indo (skrip `.binu8` + `system.datu8` + video lirik) dikemas **terpisah** dari base.
- Format packaging final (LayeredFS ZIP vs paket installable) akan ditindaklanjuti
  pada sesi berikutnya; opsi pola `exefs/main + romfs/patch.rom` milik engine Shin (DC4)
  **tidak berlaku** untuk FD karena FD memakai engine NeXAS (mod murni per-file RomFS via LayeredFS).

---

## Hasil Investigasi Binary `main` NeXAS FD (bukti teknis)

Ekstraksi ExeFS base NSP FD (titlekey dari `title.keys_autogenerated` Eden,
rights ID `010081E0161B2000000000000000000E`) menghasilkan `main` 3.0 MB
(arsip referensi: `scratch/fd_main_reference.bin`).

String di dalam binary membuktikan:
- Ada: `CNeXASMovie`, `MovieNXTextureMan`, `Script.dat`, `__GLOBAL.binu8`,
  `PlayerName.datu8`, `GenShinGo`, ekstensi `binu8`/`datu8` — engine membaca
  file RomFS **satu per satu** dengan path langsung.
- Tidak ada: magic `ROM2`, string `patch.rom`, atau mekanisme arsip patch.
  (Pola `exefs/main + romfs/patch.rom` versi DC4 hanyalah patch kode NSO
  milik engine Shin + arsip ROM2 engine itu juga.)

Kesimpulan: satu-satunya jalur mod resmi untuk FD adalah **LayeredFS per-file**
(script `.binu8`, `system.datu8`, video `Movie/*.mp4`) — dan video lirik OP
hanya perlu menggantikan `Movie/4fd_op.mp4` dengan spesifikasi di atas.

Catatan teknis ekstraksi (untuk reproduksi):
```bash
hactoolnet -k prod.keys --titlekeys title.keys_autogenerated \
  <program.nca> --exefsdir <out>
# titlekey game: 43D847B6F317CF556DBFE942AC09C8D0 (dari tik, ter-enkripsi)
```
