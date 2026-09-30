"""
exefs_patch_tool.py — Patcher Pesan Info UI D.C.4 FD (area ExeFS / file `main`).

Apa ini?
  Beberapa teks UI (mis. pesan info pojok kiri-bawah: "QUICK 1番をロードしました"
  saat Quick Load/Quick Save/Jump) TIDAK tersimpan di romfs (.datu8/.spm/.png),
  melainkan tertanam di executable game (`main` di ExeFS). Tool ini mencarinya
  di dump ExeFS milikmu sendiri lalu menggantinya dengan terjemahan Indonesia
  DENGAN PANJANG BYTE SAMA (dipad spasi) agar offset tidak bergeser.

  File `main` dari ExeFS berformat **NSO (ter-kompresi LZ4)** — tool ini
  mendekompresinya OTOMATIS (murni python, tanpa dependensi), mem-patch
  string pada image hasil dekompresi, lalu menulis ulang NSO tanpa kompresi
  (flags dibersihkan) yang tetap valid dimuat emulator/Atmosphere.

  Daftar string & terjemahan dibaca dari CSV sehingga bisa DIEDIT MANUAL:
      scratch/exefs_messages.csv   (kolom: japanese_text, indonesian_translation, keterangan)

PENTING (kebijakan):
  - Dump ExeFS berisi kode berhak cipta. JANGAN pernah meng-upload file `main`
    (asli maupun hasil patch) ke GitHub / tempat publik. Folder dump & hasil
    patch sudah di-gitignore.
  - Hasil patch hanya untuk pemakaian pribadi di konsol/emulator milikmu.

Cara pakai:
  1) Dump ExeFS game sendiri (lihat README bagian "Dump ExeFS Manual")
     -- file yang dibutuhkan cukup `main` (NSO, boleh langsung dari exefs).
  2) Taruh di  scratch/exefs_dump/main
  3) Edit terjemahan manual di: scratch/exefs_messages.csv
  4) python exefs_patch_tool.py scan     # cari string dari CSV (auto-dekompresi NSO)
  5) python exefs_patch_tool.py apply    # terapkan -> scratch/exefs_patch/main
  6) Pasang hasil patch ke emulator (lihat output tool).
"""
import csv
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DUMP_DIR = os.path.join('scratch', 'exefs_dump')
OUT_DIR = os.path.join('scratch', 'exefs_patch')
CSV_PATH = os.path.join('scratch', 'exefs_messages.csv')

DEFAULT_ROWS = [
    ('番をロードしました', ' dimuat', 'QUICK 1番をロードしました -> QUICK 1 dimuat'),
    ('をロードしました', ' dimuat', 'pesan load umum'),
    ('番をロードしています', ' dimuat', 'varian sedang memuat slot'),
    ('をロードしています', ' dimuat', 'varian sedang memuat'),
    ('ロードしました', ' dimuat', 'potongan pendek fallback'),
    ('ロードしています', ' dimuat', 'potongan pendek varian'),
    ('番をセーブしました', ' disimpan', 'QUICK 1番をセーブしました -> QUICK 1 disimpan'),
    ('をセーブしました', ' disimpan', 'pesan save umum'),
    ('をセーブしています', ' disimpan', 'varian sedang menyimpan'),
    ('セーブしました', ' disimpan', 'potongan pendek fallback'),
    ('セーブしています', ' disimpan', 'potongan pendek varian'),
    ('オートセーブしました', ' auto-save', 'auto save selesai'),
    ('オートセーブしています', ' auto-save', 'sedang auto save'),
    ('の選択肢にジャンプしました', ' dilompati', 'lompat ke pilihan N selesai (13 huruf)'),
    ('選択肢にジャンプしました', ' dilompati', 'fallback tanpa の'),
    ('の選択肢へジャンプします', ' dilompati', 'varian へ + akan'),
    ('選択肢へジャンプします', ' dilompati', 'varian fallback'),
    ('にジャンプしました', ' lompat', 'fallback pendek'),
    ('ジャンプしました', ' lompat', 'fallback terpendek (MAX 8 huruf JP)'),
    ('クイックロードしました', ' quick load', 'quick load selesai (bila ada string penuh)'),
    ('クイックセーブしました', ' quick save', 'quick save selesai (bila ada string penuh)'),
    ('クイックロード', ' Quick Load', 'label quick load'),
    ('クイックセーブ', ' Quick Save', 'label quick save'),
    ('サスペンドしました', ' suspend disimpan', 'suspend/save-and-exit'),
    ('タイトルへ戻りました', ' kembali ke title', 'kembali ke judul'),
    ('デフォルトに戻しました', ' kembali ke default', 'reset pengaturan'),
    ('削除しました', ' dihapus', 'hapus data save'),
    ('移動しました', ' dipindah', 'pindah/tukar data save'),
    ('データがありません', ' tidak ada data', 'slot kosong'),
    ('を読み込みました', ' dimuat', 'varian formal memuat'),
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
    """Return list of (jp, idn, keterangan). Spasi terjemahan dipertahankan verbatim."""
    ensure_csv()
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            jp = (r.get('japanese_text') or '').strip()
            idn = r.get('indonesian_translation') or ''
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


# ============================ NSO handling ============================

def lz4_block_decompress(src: bytes, dst_size: int) -> bytes:
    """Dekompresi blok LZ4 murni-python (format literal/match standar)."""
    dst = bytearray()
    i, n = 0, len(src)
    while i < n and len(dst) < dst_size:
        token = src[i]
        i += 1
        lit_len = token >> 4
        if lit_len == 15:
            while True:
                b = src[i]
                i += 1
                lit_len += b
                if b != 255:
                    break
        dst += src[i:i + lit_len]
        i += lit_len
        if len(dst) >= dst_size:
            break
        if i + 2 > n:  # tidak ada match lagi (akhir blok)
            break
        offset = src[i] | (src[i + 1] << 8)
        i += 2
        match_len = token & 0xF
        if match_len == 15:
            while True:
                b = src[i]
                i += 1
                match_len += b
                if b != 255:
                    break
        match_len += 4
        start = len(dst) - offset
        if start < 0:
            raise ValueError('LZ4: offset match tidak valid')
        if match_len > dst_size - len(dst):
            match_len = dst_size - len(dst)
        # copy dengan slice (aman utk overlapping: sumber disalin dulu)
        dst += dst[start:start + match_len]
    if len(dst) != dst_size:
        raise ValueError('LZ4: ukuran hasil %d != ekspektasi %d' % (len(dst), dst_size))
    return bytes(dst)


def nso_parse(data: bytes):
    """Parse header NSO0 (layout SwitchBrew). size di 0x10+ = ukuran FILE
    (ter-kompresi bila flag segmen aktif); ukuran asli ada di section header 0x60+."""
    if data[:4] != b'NSO0':
        raise ValueError('bukan NSO (magic %r)' % data[:4])
    flags = struct.unpack_from('<I', data, 0x0C)[0]
    segs = []
    for si, name in enumerate(('.text', '.ro', '.data')):
        mem_off, file_off, fsize = struct.unpack_from('<III', data, 0x10 + 12 * si)
        # section header di 0x60 + 0x10*si: +0 mem_off, +4 size (uncompressed)
        sec_mem_off, real_size = struct.unpack_from('<II', data, 0x60 + 0x10 * si)
        compressed = bool(flags & (1 << si))
        segs.append({'name': name, 'mem_off': mem_off, 'file_off': file_off,
                     'fsize': fsize, 'size': real_size if compressed else fsize,
                     'compressed': compressed})
    bss_size = struct.unpack_from('<I', data, 0x34)[0]
    return {'flags': flags, 'segs': segs, 'bss_size': bss_size}


def nso_decompress(data: bytes):
    """NSO -> image memori (segmen di offset memori masing-masing + bss nol)."""
    info = nso_parse(data)
    total = max(s['mem_off'] + s['size'] for s in info['segs']) + info['bss_size']
    img = bytearray(total)
    for s in info['segs']:
        raw = data[s['file_off']:s['file_off'] + s['fsize']]
        if s['compressed']:
            raw = lz4_block_decompress(raw, s['size'])
        img[s['mem_off']:s['mem_off'] + s['size']] = raw
    return bytes(img), info


def nso_build_uncompressed(img: bytes, info: dict) -> bytes:
    """Image memori -> NSO tanpa kompresi (flags & verifikasi hash dibersihkan)."""
    hdr = bytearray(0x100)
    hdr[0:4] = b'NSO0'
    struct.pack_into('<I', hdr, 0x0C, 0)  # flags=0: tanpa kompresi & tanpa cek hash
    fo = 0x100
    for si, s in enumerate(info['segs']):
        mem_off, size = s['mem_off'], s['size']
        struct.pack_into('<III', hdr, 0x10 + 12 * si, mem_off, fo, size)
        # section header: dst offset + ukuran asli
        struct.pack_into('<II', hdr, 0x60 + 0x10 * si, mem_off, size)
        hdr[fo:fo + size] = img[mem_off:mem_off + size]
        fo += size
        if fo % 0x10:
            fo += 0x10 - (fo % 0x10)
    struct.pack_into('<I', hdr, 0x34, info['bss_size'])
    return bytes(hdr[:fo])


def load_main_image():
    """Baca dump main. Return (image_bytes, is_nso, info_or_None, path)."""
    path = find_main()
    if not path:
        return None, False, None, None
    data = open(path, 'rb').read()
    if data[:4] == b'NSO0':
        img, info = nso_decompress(data)
        return img, True, info, path
    return data, False, None, path


# ============================ pencarian & patch ============================

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
                ctx = data[max(0, idx - 40):idx + len(needle) + 60]
                key = (idx, enc)
                if key not in seen:
                    seen.add(key)
                    hits.append({'offset': idx, 'enc': enc, 'term': term, 'ctx': ctx})
                start = idx + 1
    return sorted(hits, key=lambda h: h['offset'])


def pad_to_bytes(text: str, nbytes: int, enc: str) -> bytes:
    b = text.encode(enc, errors='strict')
    if len(b) > nbytes:
        raise ValueError('terjemahan %d byte > asli %d byte (enc=%s): %r'
                         % (len(b), nbytes, enc, text))
    pad = b' \x00' if enc == 'utf-16-le' else b' '
    return b + pad * ((nbytes - len(b)) // len(pad))


# ============================ perintah ============================

def cmd_scan():
    img, is_nso, info, path = load_main_image()
    if img is None:
        print('[ERROR] Tidak menemukan %s/{main,main.bin,main.elf}' % DUMP_DIR)
        print('        Dump ExeFS game-mu dulu, lalu taruh file "main" di situ.')
        print('        (file biasanya puluhan MB; boleh langsung NSO dari exefs)')
        return 1
    rows = load_csv()
    print('File   : %s (%.1f MB)%s' % (path, os.path.getsize(path) / 1048576,
                                        '  [NSO ter-dekompresi otomatis]' if is_nso else ''))
    if is_nso:
        for s in info['segs']:
            print('   seg %-6s mem=0x%X size=0x%X %s' % (s['name'], s['mem_off'], s['size'],
                                                         '(lz4)' if s['compressed'] else ''))
    print('CSV    : %s (%d entri)' % (CSV_PATH, len(rows)))
    hits = find_hits(img, [(jp, idn) for jp, idn, _k in rows])
    if not hits:
        print('[TIDAK KETEMU] Tidak ada string dari CSV di dump ini.')
        print('  Kemungkinan: versi game berbeda / susunan huruf lain / pesan memang tidak ada.')
        return 1
    print('Ditemukan %d lokasi (offset pada image ter-dekompresi):\n' % len(hits))
    for h in hits:
        tr = next((i for jp, i, _k in rows if jp == h['term']), '')
        status = 'TERJEMAHAN: %r' % tr if tr else '(terjemahan kosong — isi CSV dulu)'
        print('  offset 0x%08X [%s] kunci=%r  %s' % (h['offset'], h['enc'], h['term'], status))
        print('      ctx: %r' % h['ctx'])
    print()
    print('Edit terjemahan di CSV: %s' % CSV_PATH)
    print('Lalu jalankan: python exefs_patch_tool.py apply')
    return 0


def cmd_apply():
    img, is_nso, info, path = load_main_image()
    if img is None:
        print('[ERROR] Tidak menemukan dump main di', DUMP_DIR)
        return 1
    rows = [r for r in load_csv() if r[1]]  # hanya yang terjemahannya diisi
    if not rows:
        print('[KOSONG] Tidak ada terjemahan di CSV (%s).' % CSV_PATH)
        return 1
    data = bytearray(img)
    rows = sorted(rows, key=lambda r: len(r[0]), reverse=True)  # panjang dulu
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    skipped = []
    for jp, idn, _k in rows:
        for enc in ('utf-8', 'shift_jis', 'utf-16-le'):
            nb = jp.encode(enc)
            count = 0
            while True:
                idx = bytes(data).find(nb)
                if idx < 0:
                    break
                try:
                    repl = pad_to_bytes(idn, len(nb), enc)
                except ValueError as e:
                    skipped.append(str(e))
                    break
                data[idx:idx + len(nb)] = repl
                count += 1
                total += 1
            if count:
                print('[OK] %r -> %r x%d [%s] (slot %d byte dipertahankan)' % (jp, idn, count, enc, len(nb)))
    if not total:
        print('[TIDAK ADA] Tidak ada string CSV yang cocok — jalankan "scan" dulu.')
        for s in set(skipped):
            print('  [SKIP]', s)
        return 1
    for s in sorted(set(skipped)):
        print('[SKIP]', s)
    out = os.path.join(OUT_DIR, 'main')
    if is_nso:
        # kembalikan sebagai NSO tanpa kompresi (valid dimuat emulator/Atmosphere)
        open(out, 'wb').write(nso_build_uncompressed(bytes(data), info))
        print('[i] NSO ditulis ulang tanpa kompresi (flags dibersihkan).')
    else:
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
    ensure_csv()
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
