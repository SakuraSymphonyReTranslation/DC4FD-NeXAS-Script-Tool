"""
exefs_patch_tool.py — Patcher Pesan Info UI D.C.4 FD (area ExeFS / file `main`).

Apa ini?
  Beberapa teks UI (mis. pesan info pojok kiri-bawah: "QUICK 1番をロードしました"
  saat Quick Load/Quick Save/Jump) TIDAK tersimpan di romfs (.datu8/.spm/.png),
  melainkan tertanam di executable game (`main` di ExeFS). Tool ini mencarinya
  di dump ExeFS milikmu sendiri lalu menggantinya dengan terjemahan Indonesia
  DENGAN PANJANG BYTE SAMA (dipad spasi) agar offset tidak bergeser.

  Daftar string & terjemahan dibaca dari CSV sehingga bisa DIEDIT MANUAL:
      scratch/exefs_messages.csv   (kolom: japanese_text, indonesian_translation, keterangan)

PENTING (kebijakan):
  - Dump ExeFS berisi kode berhak cipta. JANGAN pernah meng-upload file `main`
    (asli maupun hasil patch) ke GitHub / tempat publik. Folder dump & hasil
    patch sudah di-gitignore.
  - Hasil patch hanya untuk pemakaian pribadi di konsol/emulator milikmu.

Cara pakai:
  1) Dump ExeFS game sendiri (lihat README bagian "Dump ExeFS Manual").
  2) Taruh hasil dump di  scratch/exefs_dump/main
  3) Edit terjemahan manual di: scratch/exefs_messages.csv
     (boleh menambah baris baru: isi japanese_text dengan potongan JP yang
      mau dicari, lalu isi terjemahannya)
  4) python exefs_patch_tool.py scan     # cari string dari CSV di binary
  5) python exefs_patch_tool.py apply    # terapkan -> scratch/exefs_patch/main
  6) Pasang hasil patch ke emulator (lihat output tool).
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DUMP_DIR = os.path.join('scratch', 'exefs_dump')
OUT_DIR = os.path.join('scratch', 'exefs_patch')
CSV_PATH = os.path.join('scratch', 'exefs_messages.csv')

# CSV awal (dibuat bila belum ada). Edit kolom indonesian_translation sesukamu,
# atau tambah baris sendiri. Terjemahan kosong = dicari di scan, TIDAK diganti di apply.
DEFAULT_ROWS = [
    # japanese_text, indonesian_translation, keterangan
    ('番をロードしました', 'dimuat', 'QUICK 1番をロードしました -> QUICK 1 dimuat'),
    ('番をセーブしました', 'disimpan', 'pesan save slot'),
    ('をロードしました', 'dimuat', 'pesan load umum'),
    ('をセーブしました', 'disimpan', 'pesan save umum'),
    ('ジャンプしました', 'lompat', 'MAX 8 huruf (slot UTF-16 hanya 16 byte)'),
    ('をロードしています', '', 'varian sedang memuat (isi manual bila ketemu)'),
    ('オートセーブしました', '', 'auto save (isi manual bila ketemu)'),
    ('ジャンプします', '', 'tooltip tombol jump (isi manual bila perlu)'),
]


def ensure_csv():
    if not os.path.exists(CSV_PATH):
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(['japanese_text', 'indonesian_translation', 'keterangan'])
            for row in DEFAULT_ROWS:
                w.writerow(row)
        print('[i] CSV template dibuat: %s — EDIT FILE INI untuk terjemahan manual.' % CSV_PATH)


def load_csv():
    """Return list of (jp, idn, keterangan). Baris tanpa japanese_text dilewati."""
    ensure_csv()
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            jp = (r.get('japanese_text') or '').strip()
            idn = (r.get('indonesian_translation') or '').strip()
            ket = (r.get('keterangan') or '').strip()
            if jp:
                rows.append((jp, idn, ket))
    return rows


def find_main():
    for name in ('main', 'main.bin', 'main.elf'):
        p = os.path.join(DUMP_DIR, name)
        if os.path.exists(p):
            return p
    return None


def find_hits(data: bytes, terms):
    hits = []
    seen = set()
    for term, _idn in terms:
        for enc in ('utf-8', 'shift_jis', 'utf-16-le'):
            needle = term.encode(enc)
            start = 0
            while True:
                idx = data.find(needle, start)
                if idx < 0:
                    break
                lo = max(0, idx - 40)
                ctx = data[lo:idx + len(needle) + 60]
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
        print('        (file biasanya puluhan MB, tanpa ekstensi, bernama persis "main")')
        return 1
    rows = load_csv()
    data = open(main, 'rb').read()
    print('File   : %s (%.1f MB)' % (main, len(data) / 1048576))
    print('CSV    : %s (%d entri)' % (CSV_PATH, len(rows)))
    hits = find_hits(data, [(jp, idn) for jp, idn, _k in rows])
    if not hits:
        print('[TIDAK KETEMU] Tidak ada string dari CSV di dump ini.')
        print('  Kemungkinan: versi game berbeda, atau string memakai susunan huruf lain.')
        print('  Tips: jalankan dump string (scan dengan potongan lebih pendek) atau')
        print('  tambahkan baris baru di CSV dengan potongan JP yang berbeda.')
        return 1
    print('Ditemukan %d lokasi:\n' % len(hits))
    for h in hits:
        tr = next((i for jp, i, _k in rows if jp == h['term']), '')
        status = 'TERJEMAHAN: %r' % tr if tr else '(terjemahan kosong — isi CSV dulu)'
        print('  offset 0x%08X [%s] kunci=%r  %s' % (h['offset'], h['enc'], h['term'], status))
        print('      ctx: %r' % h['ctx'])
    print()
    print('Edit terjemahan di CSV: %s' % CSV_PATH)
    print('Lalu jalankan: python exefs_patch_tool.py apply')
    return 0


def pad_to_bytes(text: str, nbytes: int, enc: str) -> bytes:
    """Encode text ke tepat nbytes (pad spasi); error bila lebih panjang."""
    b = text.encode(enc, errors='strict')
    if len(b) > nbytes:
        raise ValueError('terjemahan %d byte > asli %d byte (enc=%s): %r'
                         % (len(b), nbytes, enc, text))
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
    rows = [r for r in load_csv() if r[1]]  # hanya yang terjemahannya diisi
    if not rows:
        print('[KOSONG] Tidak ada terjemahan di CSV (%s). Isi kolom indonesian_translation dulu.' % CSV_PATH)
        return 1
    data = bytearray(open(main, 'rb').read())
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for jp, idn, _k in rows:
        for enc in ('utf-8', 'shift_jis', 'utf-16-le'):
            nb = jp.encode(enc)
            count = 0
            while True:
                idx = bytes(data).find(nb)
                if idx < 0:
                    break
                repl = pad_to_bytes(idn, len(nb), enc)
                data[idx:idx + len(nb)] = repl
                count += 1
                total += 1
            if count:
                print('[OK] %r -> %r x%d [%s] (slot %d byte dipertahankan)' % (jp, idn, count, enc, len(nb)))
    if not total:
        print('[TIDAK ADA] Tidak ada string CSV yang cocok — jalankan "scan" dulu.')
        return 1
    out = os.path.join(OUT_DIR, 'main')
    open(out, 'wb').write(bytes(data))
    print()
    print('[SELESAI] %d penggantian. Hasil patch: %s' % (total, out))
    print()
    print('CARA PASANG (pilih salah satu):')
    print('  Eden/emulator : salin sebagai %APPDATA%\\eden\\exefs\\010081E0161B2000\\main')
    print('  Ryujinx       : Options -> Manage Mods -> ExeFS -> pilih file main ini')
    print('  Atmosphere    : atmosphere/exefs/010081E0161B2000/main')
    print()
    print('INGAT: file main hasil patch = kode berhak cipta. JANGAN dibagikan/upload.')
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    ensure_csv()  # template CSV selalu siap untuk diedit manual
    if cmd == 'scan':
        sys.exit(cmd_scan())
    elif cmd == 'apply':
        sys.exit(cmd_apply())
    elif cmd == 'csv':
        print('CSV terjemahan: %s' % CSV_PATH)
        print('(buka & edit kolom indonesian_translation secara manual)')
        sys.exit(0)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
