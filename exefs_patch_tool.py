"""
exefs_patch_tool.py — Patcher Pesan Info UI D.C.4 FD (area ExeFS / file `main`).

Apa ini?
  Beberapa teks UI (mis. pesan info pojok kiri-bawah: "QUICK 1番をロードしました"
  saat Quick Load/Quick Save/Jump) TIDAK tersimpan di romfs (.datu8/.spm/.png),
  melainkan tertanam di executable game (`main` di ExeFS). Tool ini mencarinya
  di dump ExeFS milikmu sendiri lalu menggantinya dengan terjemahan Indonesia
  DENGAN PANJANG BYTE SAMA (dipad spasi) agar offset tidak bergeser.

PENTING (kebijakan):
  - Dump ExeFS berisi kode berhak cipta. JANGAN pernah meng-upload file `main`
    (asli maupun hasil patch) ke GitHub / tempat publik. Folder dump & hasil
    patch sudah di-gitignore.
  - Hasil patch hanya untuk pemakaian pribadi di konsol/emulator milikmu.

Cara pakai:
  1) Dump ExeFS game sendiri (lihat README bagian "Dump ExeFS Manual").
  2) Taruh hasil dump di  scratch/exefs_dump/  :
        scratch/exefs_dump/main
        scratch/exefs_dump/main.npdm   (opsional)
  3) python exefs_patch_tool.py scan     # temukan & tampilkan string pesan
  4) python exefs_patch_tool.py apply    # terapkan terjemahan -> scratch/exefs_patch/main
  5) Pasang hasil patch ke emulator (lihat output tool).

Encoding string di `main`: tool mencoba UTF-8, Shift_JIS, dan UTF-16LE otomatis.
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DUMP_DIR = os.path.join('scratch', 'exefs_dump')
OUT_DIR = os.path.join('scratch', 'exefs_patch')

# Pesan info UI pojok kiri-bawah (format %s/%d diganti runtime oleh engine).
# Kata kunci dipakai untuk MENCARI di binary; template dipakai untuk MENGGANTI.
# Panjang byte terjemahan <= panjang byte asli (dipad spasi otomatis oleh tool).
SEARCH_TERMS = [
    'ロードしました',     # ...をロードしました (loaded)
    'セーブしました',     # ...をセーブしました (saved)
    'ジャンプしました',   # jump destination
    'クイックロード',
    'クイックセーブ',
]

# Terjemahan (UI saja) — kunci = potongan JP unik, nilai = ID dengan panjang byte <= asli.
# Karakter '_' dipakai sebagai penanda spasi-pad yang diisi tool.
REPLACE_MAP = {
    '番をロードしました': 'dimuat',        # "QUICK 1番をロードしました" -> "QUICK 1 dimuat"
    '番をセーブしました': 'disimpan',
    'をロードしました': 'dimuat',
    'をセーブしました': 'disimpan',
    'ジャンプしました': 'lompat',   # harus muat 8 huruf JP (16 byte UTF-16)
}


def encodings_for(data: bytes):
    """Encoding kandidat: deteksi kasar dari keberadaan byte Jepang."""
    yield 'utf-8'
    yield 'shift_jis'
    yield 'utf-16-le'


def find_main():
    for name in ('main', 'main.bin', 'main.elf'):
        p = os.path.join(DUMP_DIR, name)
        if os.path.exists(p):
            return p
    return None


def find_hits(data: bytes):
    hits = []
    seen = set()
    for term in SEARCH_TERMS:
        for enc in ('utf-8', 'shift_jis', 'utf-16-le'):
            needle = term.encode(enc)
            start = 0
            while True:
                idx = data.find(needle, start)
                if idx < 0:
                    break
                # ambil konteks lebih lebar: mundur ke awal string yang masuk akal
                lo = max(0, idx - 80)
                ctx = data[lo:idx + len(needle) + 80]
                key = (idx, enc)
                if key not in seen:
                    seen.add(key)
                    hits.append({'offset': idx, 'enc': enc, 'term': term, 'ctx': ctx})
                start = idx + 1
    return sorted(hits, key=lambda h: h['offset'])


def cmd_scan():
    main = find_main()
    if not main:
        print('[ERROR] Tidak menemukan %s/{main,main.bin,main.elf}' % DUMP_DIR)
        print('        Dump ExeFS game-mu dulu, lalu taruh file "main" di situ.')
        return 1
    data = open(main, 'rb').read()
    print('File   : %s (%.1f MB)' % (main, len(data) / 1048576))
    hits = find_hits(data)
    if not hits:
        print('[TIDAK KETEMU] Tidak ada string pesan info di dump ini.')
        print('  Kemungkinan: dump dari versi game berbeda, atau string dipadatkan/terkompresi.')
        return 1
    print('Ditemukan %d lokasi:\n' % len(hits))
    for h in hits:
        print('  offset 0x%08X [%s] kunci=%r' % (h['offset'], h['enc'], h['term']))
        print('      ctx: %r' % h['ctx'])
    print()
    print('Gunakan: python exefs_patch_tool.py apply  untuk mengganti dengan terjemahan.')
    return 0


def pad_to_bytes(text: str, nbytes: int, enc: str) -> bytes:
    """Encode text ke tepat nbytes (pad spasi); error bila lebih panjang."""
    b = text.encode(enc, errors='strict')
    if len(b) > nbytes:
        raise ValueError('terjemahan %d byte > asli %d byte (enc=%s): %r' % (len(b), nbytes, enc, text))
    if enc == 'utf-16-le':
        pad = b' \x00'
    else:
        pad = b' '
    return b + pad * ((nbytes - len(b)) // len(pad))


def cmd_apply():
    main = find_main()
    if not main:
        print('[ERROR] Tidak menemukan dump main di', DUMP_DIR)
        return 1
    data = bytearray(open(main, 'rb').read())
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for jp, idn in REPLACE_MAP.items():
        for enc in ('utf-8', 'shift_jis', 'utf-16-le'):
            nb = jp.encode(enc)
            idx = data.find(nb)
            if idx < 0:
                continue
            # terapkan di SEMUA kemunculan
            count = 0
            while True:
                idx = bytes(data).find(nb)
                if idx < 0:
                    break
                repl = pad_to_bytes(idn, len(nb), enc)
                data[idx:idx + len(nb)] = repl
                count += 1
                total += 1
            print('[OK] %r -> %r x%d [%s] (panjang %d byte dipertahankan)' % (jp, idn, count, enc, len(nb)))
    if not total:
        print('[TIDAK ADA] Tidak ada string yang cocok — jalankan "scan" dulu.')
        return 1
    out = os.path.join(OUT_DIR, 'main')
    open(out, 'wb').write(bytes(data))
    print()
    print('[SELESAI] %d penggantian. Hasil patch: %s' % (total, out))
    print()
    print('CARA PASANG (pilih salah satu):')
    print('  Eden/emu lain (ExeFS mod): salin sebagai:')
    print('    %APPDATA%\\eden\\exefs\\010081E0161B2000\\main')
    print('  Ryujinx:管理与対象 (Manage Mods) -> add ExeFS mod -> pilih file main ini.')
    print('  Atmosphere (konsol): atmosphere/exefs/010081E0161B2000/main')
    print()
    print('INGAT: file main hasil patch = kode berhak cipta. JANGAN dibagikan/upload.')
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    if cmd == 'scan':
        sys.exit(cmd_scan())
    elif cmd == 'apply':
        sys.exit(cmd_apply())
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
