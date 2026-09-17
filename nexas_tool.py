#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeXAS Script Extractor & Inserter (Switch / PC)
Khusus game berengine NeXAS (seperti D.C.4 Fortunate Departures, Aquarium, dll)
Mendukung format JSON:
- Dialog:  {"name": "...", "message": "..."}
- Monolog: {"message": "..."}
Menjaga tag voice (@v...), formatting ruby (@r...), face tag (@h...), tag waktu (@t...), dsb.
"""

import os
import sys
import json
import re
import struct
import argparse
from pathlib import Path

VOICE_REGEX = re.compile(r'^(@v\S+?)(?=[「『（\s]|$)\s*')

def is_asset_or_system_string(s):
    if not s or not s.strip():
        return True
    clean = s.strip()
    lower = clean.lower()
    # File extensions
    if any(lower.endswith(ext) for ext in [
        '.png', '.opus', '.jpg', '.jpeg', '.bmp', '.nmv', '.fxb', 
        '.ttc', '.ttf', '.fnt', '.spm', '.bin', '.binu8', '.dat', '.datu8', '.csv'
    ]):
        return True
    # Sound/music identifiers (e.g. se083, bgm001, voice123, sys001)
    if re.match(r'^(?:se|bgm|voice|sys)\d+', clean, re.IGNORECASE):
        return True
    # Known engine keywords / scene jump targets
    if clean in ['ReplayMode', 'EventMode', 'Title', 'System', 'PackList', 'cgmode', 'musicmode', 'BGM']:
        return True
    # Short formatting commands like @b
    if clean.startswith('@b') and len(clean) <= 5:
        return True
    # Pure ASCII symbols / labels / IDs (must not contain any Japanese / CJK characters)
    if re.match(r'^[a-zA-Z0-9_\-\.\:\/]+$', clean) and not any('\u3040' <= c <= '\u9fff' for c in clean):
        return True
    return False

def parse_binu8(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    pos = 0
    version = data[0:9]
    if version[0:3] == b'VER':
        pos = 9
        unk_count = struct.unpack('<L', data[pos:pos+4])[0]
        pos += 4 + unk_count * 4
    elif version[0] == 9 and version[4:7] == b'VER':
        pos = 13
        unk_count = struct.unpack('<L', data[pos:pos+4])[0]
        pos += 4 + unk_count * 4
    else:
        pos = 0

    init_code_count = struct.unpack('<L', data[pos:pos+4])[0]
    pos += 4 + init_code_count * 8

    code_count = struct.unpack('<L', data[pos:pos+4])[0]
    pos += 4
    codes = [struct.unpack('<II', data[pos+i*8:pos+i*8+8]) for i in range(code_count)]
    pos += code_count * 8

    header_prefix = data[:pos]
    str_count = struct.unpack('<L', data[pos:pos+4])[0]
    pos += 4

    strings = []
    for _ in range(str_count):
        slen = struct.unpack('<L', data[pos:pos+4])[0]
        pos += 4
        s_bytes = data[pos:pos+slen-1]
        s = s_bytes.decode('utf-8', errors='replace')
        pos += slen
        strings.append(s)

    footer_bytes = data[pos:]

    # Bytecode speaker map:
    # Pada engine NeXAS, pembicara dialog dipasangkan melalui opcode:
    # (0, name_idx), (5, 1), (0, msg_idx)
    msg_to_speaker = {}
    for i in range(len(codes) - 2):
        if codes[i+1] == (5, 1) and codes[i][0] == 0 and codes[i+2][0] == 0:
            name_idx = codes[i][1]
            msg_idx = codes[i+2][1]
            if name_idx < len(strings) and msg_idx < len(strings):
                name_str = strings[name_idx].strip()
                if name_str and not is_asset_or_system_string(name_str) and len(name_str) <= 20:
                    msg_to_speaker[msg_idx] = (name_idx, name_str)

    return {
        'header_prefix': header_prefix,
        'str_count': str_count,
        'strings': strings,
        'codes': codes,
        'msg_to_speaker': msg_to_speaker,
        'footer_bytes': footer_bytes,
        'filesize': len(data)
    }

def extract_script(binu8_path, out_json_path):
    parsed = parse_binu8(binu8_path)
    strings = parsed['strings']
    msg_to_speaker = parsed['msg_to_speaker']

    entries = []
    total_strings = len(strings)

    # Lacak pembicara dialog aktif untuk menangani dialog bersambung (@k)
    active_speaker = None

    for i in range(total_strings):
        s = strings[i]
        if is_asset_or_system_string(s):
            continue

        clean = s.strip()

        # Cek apakah string ini adalah definisi nama karakter
        is_speaker_def = any(n_idx == i for n_idx, _ in msg_to_speaker.values())
        is_msg = i in msg_to_speaker

        if is_msg:
            active_speaker = msg_to_speaker[i][1]
        elif is_speaker_def and not is_msg:
            # Ini adalah slot definisi nama pembicara, jangan diekstrak sebagai baris dialog/monolog terpisah!
            continue
        elif clean.startswith('「') or clean.startswith('『') or VOICE_REGEX.match(clean):
            if not is_msg:
                active_speaker = None
        elif clean.startswith('\u3000'):
            # Narasi / monolog
            active_speaker = None

        # Deteksi apakah baris ini adalah bagian percakapan karakter:
        # 1. Memiliki nama di bytecode (is_msg)
        # 2. Diawali tanda petik/kurung 「...」 atau suara @v
        # 3. Merupakan SAMBUNGAN dari dialog sebelumnya yang belum ditutup (misal diawali @k lalu dilanjutkan di string ini)
        is_speech = (is_msg or 
                     clean.startswith('「') or 
                     clean.startswith('『') or 
                     VOICE_REGEX.match(clean) or 
                     (active_speaker is not None and (clean.endswith('」') or clean.endswith('』') or '@k' in clean)))

        clean_msg = strip_ruby_tags(VOICE_REGEX.sub('', s).strip())

        entry = {}
        if is_speech and active_speaker:
            entry["name"] = active_speaker
        entry["message"] = clean_msg
        entries.append(entry)

        # Jika dialog sudah selesai (tutup kurung 」 dan tidak ada sambungan @k lagi), reset active_speaker
        if (clean.endswith('」') or clean.endswith('』')) and not clean.endswith('@k'):
            active_speaker = None

    os.makedirs(os.path.dirname(os.path.abspath(out_json_path)), exist_ok=True)
    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return len(entries)

EMBEDDED_NAME_REGEX = re.compile(r'^([A-Za-z0-9_ \.\-]+?)\s*:\s*([「『"“\'].+)', re.DOTALL)
EMBEDDED_BRACKET_REGEX = re.compile(r'^\[([A-Za-z0-9_ \.\-]+?)\]\s*(.+)', re.DOTALL)

def strip_ruby_tags(text):
    """
    Menghapus tag Ruby / Furigana (@r... atau @・@) dan menyisakan teks intinya.
    Contoh:
      - @rあ@・@@rい@・@@rつ@・@ -> あいつ
      - @rd@・@@ri@・@@ra@・@ -> dia
      - @r系統樹の径@パ　ス@ -> 系統樹の径
      - @r七月七日@きょう@ -> 七月七日
    """
    if not text:
        return text
    # Pola standar: @rBase@Ruby@ -> Base
    cleaned = re.sub(r"@[rR]([^@]+)@[^@]*@", r"\1", text)
    # Sisa tag bouten / titik penekanan
    cleaned = re.sub(r"@・@", "", cleaned)
    cleaned = re.sub(r"@[rR]", "", cleaned)
    return cleaned

def separate_tags_from_latin_words(text):
    """
    Pada engine NeXAS, nama tag (@h..., @t...) diparsing menggunakan regex alfabet ASCII.
    Jika tag langsung menempel dengan kata Latin/Indonesia tanpa spasi,
    contoh: '@hAlice_l150215Bagaimanapun'
    Engine game akan menganggap 'Bagaimanapun' sebagai bagian dari nama gambar avatar,
    sehingga kata 'Bagaimanapun' hilang/ditelan dari layar game.
    Fungsi ini otomatis menyisipkan spasi pemisah agar kata tidak hilang:
    '@hAlice_l150215 Bagaimanapun'.
    """
    if not text:
        return text
    # Tag yang berakhiran angka menempel dengan huruf Latin: @hAlice_l150215Kata -> @hAlice_l150215 Kata
    text = re.sub(r"(@[a-zA-Z0-9_]*\d)([A-Za-z\u00C0-\u024F])", r"\1 \2", text)
    # Tag huruf tunggal menempel dengan huruf Latin: @kKata -> @k Kata
    text = re.sub(r"(@[kgd])([A-Za-z\u00C0-\u024F])", r"\1 \2", text)
    return text

def clean_translated_entry(entry):
    """
    Membersihkan entry terjemahan:
    1. Memisahkan awalan nama 'Nama: 「...」' jika terselip di dalam message.
    2. Menghapus tag ruby sisa (@rd@・@).
    3. Menyisipkan spasi pemisah jika ada kata Latin yang menempel langsung di belakang tag (@h...Kata).
    """
    msg = entry.get("message", "")
    if msg:
        msg = strip_ruby_tags(msg)
        msg = separate_tags_from_latin_words(msg)
        entry["message"] = msg

    if ("name" not in entry or not entry["name"]) and msg:
        m = EMBEDDED_NAME_REGEX.match(msg)
        if m:
            entry["name"] = m.group(1).strip()
            entry["message"] = m.group(2).strip()
            return
        m2 = EMBEDDED_BRACKET_REGEX.match(msg)
        if m2:
            entry["name"] = m2.group(1).strip()
            entry["message"] = m2.group(2).strip()
            return
    elif "name" in entry and entry["name"] and msg:
        m = EMBEDDED_NAME_REGEX.match(msg)
        if m:
            entry["message"] = m.group(2).strip()
        else:
            m2 = EMBEDDED_BRACKET_REGEX.match(msg)
            if m2:
                entry["message"] = m2.group(2).strip()

def format_comu_bubble_text(text):
    """
    Format khusus untuk teks percakapan di dalam balon obrolan (Comu / Phonechat).
    Aturan cerdas untuk menjamin line spacing konsisten dan tidak ada baris yang meluber:
    
    1. Pesan Pendek (<= 38 karakter):
       - 1 baris tanpa @n.
    
    2. Pesan Sedang:
       - Dibagi seimbang ke dalam 2 baris (jika masing-masing baris <= 40 karakter).
    
    3. Pesan Panjang:
       - Dibagi secara merata dan proporsional ke dalam 3 baris dengan algoritma
         optimasi lebar baris, memastikan setiap baris <= 40 karakter.
       - Dengan panjang per baris yang seimbang dan tidak ada baris yang overflow,
         engine NeXAS merender baris 1, 2, dan 3 dengan line pitch yang rata sempurna!
    """
    clean = text.replace('@d', '').replace('@k', '').replace('@n', ' ').replace('\n', ' ')
    clean = re.sub(r'\s+', ' ', clean).strip()
    words = clean.split(' ')
    total_len = len(clean)

    if total_len <= 38 or len(words) <= 1:
        return clean

    # Cek apakah bisa 2 baris seimbang (tiap baris <= 40 karakter)
    best_2 = None
    best_2_max = float('inf')
    for i in range(1, len(words)):
        l1 = ' '.join(words[:i])
        l2 = ' '.join(words[i:])
        m = max(len(l1), len(l2))
        if m < best_2_max:
            best_2_max = m
            best_2 = [l1, l2]

    if best_2_max <= 40:
        return f"{best_2[0]}@n{best_2[1]}"

    # Jika tidak muat di 2 baris, bagi seimbang optimal ke dalam 3 baris
    best_3 = None
    best_3_score = float('inf')
    for i in range(1, len(words) - 1):
        for j in range(i + 1, len(words)):
            l1 = ' '.join(words[:i])
            l2 = ' '.join(words[i:j])
            l3 = ' '.join(words[j:])
            lens = [len(l1), len(l2), len(l3)]
            penalty = sum(max(0, l - 40) * 100 for l in lens)
            variance = max(lens) - min(lens)
            score = max(lens) * 10 + variance + penalty
            if score < best_3_score:
                best_3_score = score
                best_3 = [l1, l2, l3]

    if best_3:
        return '@n'.join(best_3)

    return clean

# Gunakan implementasi algoritma dari script_auto_wrap jika tersedia
try:
    import script_auto_wrap
    def apply_word_wrap(text, max_len=56, initial_width=0):
        if not max_len or max_len <= 0:
            return text
        return script_auto_wrap.wrap_text(text, max_chars=max_len, initial_width=initial_width)
    def visible_length(text):
        return script_auto_wrap.visible_length(text)
except ImportError:
    import unicodedata
    def char_width(c):
        if c in '\u3000…「」『』・―〜～★☆♪※♥':
            return 2
        w = unicodedata.east_asian_width(c)
        if w in ('F', 'W'):
            return 2
        return 1

    def visible_length(text):
        clean = re.sub(r'@(?:v[A-Za-z0-9_]+|h[A-Za-z0-9_]+|t\d+|n|k|g)', '', text)
        return sum(char_width(c) for c in clean)

    def apply_word_wrap(text, max_len=56, initial_width=0):
        if not max_len or max_len <= 0:
            return text
        leading_indent = ""
        if text.startswith("\u3000"):
            leading_indent = "\u3000"
            text = text[1:]
            initial_width += 2

        text = text.replace("@n", "")
        tokens = re.findall(r'@(?:v[A-Za-z0-9_]+|h[A-Za-z0-9_]+|t\d+|n|k|g|[a-zA-Z0-9_]+)|\s+|[^\s@]+', text)
        lines = []
        current = ""
        pending_space = ""
        for token in tokens:
            if token.isspace():
                pending_space = token
                continue
            if re.match(r'^@(?:v[A-Za-z0-9_]+|h[A-Za-z0-9_]+|t\d+|n|k|g)', token):
                current += pending_space + token
                pending_space = ""
                continue
            word = token
            separator = pending_space if current else ""
            candidate = current + separator + word
            eff_width = (initial_width if not lines else 0) + visible_length(candidate)
            if eff_width <= max_len:
                current = candidate
            else:
                if current:
                    lines.append(current)
                elif initial_width > 0 and not lines:
                    lines.append("")
                current = word
                initial_width = 0
            pending_space = ""
        if current:
            lines.append(current)
        if leading_indent and lines:
            lines[0] = leading_indent + lines[0]
        return "@n".join(lines)

def insert_script(binu8_orig_path, json_path, binu8_out_path, word_wrap=56):
    parsed = parse_binu8(binu8_orig_path)
    orig_strings = parsed['strings']
    total_strings = len(orig_strings)

    with open(json_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Otomatis bersihkan setiap entry dari nama yang terselip di dalam message
    for entry in entries:
        clean_translated_entry(entry)

    new_strings = list(orig_strings)

    # Check if entries have metadata index tags (_idx_msg)
    has_meta = len(entries) > 0 and "_idx_msg" in entries[0]

    if has_meta:
        for entry in entries:
            if "name" in entry and "_idx_name" in entry:
                idx_name = entry["_idx_name"]
                new_strings[idx_name] = entry["name"]

            if "_idx_msg" in entry:
                idx_msg = entry["_idx_msg"]
                msg = entry.get("message", "")
                voice_tag = entry.get("_voice")
                orig_s = orig_strings[idx_msg]
                if not voice_tag and orig_s.startswith('\u3000') and not msg.startswith('\u3000') and not msg.startswith('「') and not msg.startswith('『'):
                    msg = f"\u3000{msg}"
                if word_wrap > 0:
                    msg = apply_word_wrap(msg, word_wrap)
                if voice_tag:
                    new_msg = f"{voice_tag}{msg}"
                else:
                    new_msg = msg
                new_strings[idx_msg] = new_msg
    else:
        # Sequential match using bytecode mapping
        msg_to_speaker = parsed['msg_to_speaker']
        entry_idx = 0
        num_entries = len(entries)
        prev_line_col = 0
        last_speaker = None

        for i in range(total_strings):
            s = orig_strings[i]
            if is_asset_or_system_string(s):
                continue

            if entry_idx >= num_entries:
                break

            clean = s.strip()
            is_speaker_def = any(n_idx == i for n_idx, _ in msg_to_speaker.values())
            is_msg = i in msg_to_speaker

            # 1. Slot definisi nama pembicara saja (bukan dialog), lewati
            if is_speaker_def and not is_msg:
                continue

            # 2. Penanganan Khusus Phonechat / Tablet (@d):
            if s.startswith('@d') and not s.startswith('@d@*stamp'):
                entry = entries[entry_idx]
                clean_m = entry.get("message", "").replace('@d', '').replace('@k', '').strip()
                if word_wrap > 0:
                    clean_m = apply_word_wrap(clean_m, word_wrap)
                new_strings[i] = f"@d{clean_m}@k"
                prev_line_col = 0
                entry_idx += 1
                continue
            elif i > 0 and orig_strings[i-1].startswith('@d') and not orig_strings[i-1].startswith('@d@*stamp'):
                entry = entries[entry_idx]
                new_strings[i] = format_comu_bubble_text(entry.get("message", ""))
                prev_line_col = 0
                entry_idx += 1
                continue

            # 3. SEMUA PESAN DIALOG & NARASI (termasuk sambungan @k):
            entry = entries[entry_idx]
            curr_speaker = entry.get("name")

            # Update speaker name if defined in bytecode
            if is_msg and "name" in entry:
                n_idx = msg_to_speaker[i][0]
                new_strings[n_idx] = entry["name"]

            # Update message
            msg = entry.get("message", "")
            v_match = VOICE_REGEX.match(s)

            # Cek apakah string ini merupakan sambungan langsung pada baris yang sama (chained continuation)
            is_continuation = (
                prev_line_col > 0
                and not v_match
                and not msg.startswith('「')
                and not msg.startswith('『')
                and not s.startswith('「')
                and not s.startswith('『')
                and (
                    (bool(curr_speaker) and curr_speaker == last_speaker)
                    or (not curr_speaker and not s.startswith('\u3000') and ('」' in msg or '@h' in msg or '@t' in msg))
                )
            )

            if not is_continuation:
                prev_line_col = 0

            is_narrative = (not curr_speaker) and (not is_continuation)
            if is_msg:
                if is_narrative:
                    last_speaker = None
                elif curr_speaker:
                    last_speaker = curr_speaker

            if is_continuation:
                # Sambungan dialog pada baris yang sama (chained continuation @k)
                if not msg.startswith(' ') and not msg.startswith('\u3000'):
                    msg = f" {msg}"
                if word_wrap > 0:
                    msg = apply_word_wrap(msg, word_wrap, initial_width=prev_line_col)
            else:
                if not v_match and s.startswith('\u3000') and not msg.startswith('\u3000') and not msg.startswith('「') and not msg.startswith('『'):
                    msg = f"\u3000{msg}"
                if word_wrap > 0:
                    msg = apply_word_wrap(msg, word_wrap, initial_width=0)

            if v_match:
                new_strings[i] = f"{v_match.group(1)}{msg}"
            else:
                new_strings[i] = msg

            # Update prev_line_col untuk string berikutnya
            res_str = new_strings[i]
            # Jika kalimat/kutipan telah ditutup dengan '」' atau '』', dialog selesai (tidak ada sambungan ke baris berikutnya)
            has_closed_quote = bool(
                re.search(r'[」』](?:@[a-zA-Z0-9_*~]+)*\s*$', res_str)
                or re.search(r'[」』](?:@[a-zA-Z0-9_*~]+)*\s*$', s)
            )

            if (
                res_str.rstrip().endswith('@k')
                and not res_str.endswith('@n@k')
                and not res_str.endswith('@n')
                and not has_closed_quote
                and not is_narrative
            ):
                parts = res_str.split('@n')
                if len(parts) > 1:
                    prev_line_col = visible_length(parts[-1])
                else:
                    prev_line_col = prev_line_col + visible_length(parts[0])
            else:
                prev_line_col = 0

            entry_idx += 1

    # Rebuild binu8 binary
    os.makedirs(os.path.dirname(os.path.abspath(binu8_out_path)), exist_ok=True)
    with open(binu8_out_path, 'wb') as f:
        f.write(parsed['header_prefix'])
        f.write(struct.pack('<L', len(new_strings)))

        for s in new_strings:
            s_bytes = s.encode('utf-8')
            f.write(struct.pack('<L', len(s_bytes) + 1))
            f.write(s_bytes)
            f.write(b'\x00')

        f.write(parsed['footer_bytes'])

    return len(entries)

def main():
    parser = argparse.ArgumentParser(
        description="NeXAS Switch/PC Script Tool (Extract / Insert)",
        epilog="Support Da Capo 4 Fortunate Departures, Aquarium, etc."
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Extract
    ext_parser = subparsers.add_parser('extract', help='Extract .binu8 to .json (name + message / message)')
    ext_parser.add_argument('-i', '--input', required=True, help='Input binu8 file or folder')
    ext_parser.add_argument('-o', '--output', required=True, help='Output json file or folder')

    # Insert
    ins_parser = subparsers.add_parser('insert', help='Insert translated .json back into .binu8')
    ins_parser.add_argument('-b', '--base', required=True, help='Original binu8 file or folder')
    ins_parser.add_argument('-j', '--json', required=True, help='Translated json file or folder')
    ins_parser.add_argument('-o', '--output', required=True, help='Output binu8 file or folder')
    ins_parser.add_argument('-w', '--wordwrap', type=int, default=56, help='Max visual width per line before @n (0 to disable, default: 56)')

    args = parser.parse_args()

    if args.command == 'extract':
        in_p = Path(args.input)
        out_p = Path(args.output)
        if in_p.is_file():
            cnt = extract_script(str(in_p), str(out_p))
            print(f"[+] Extracted {cnt} entries: {in_p.name} -> {out_p}")
        elif in_p.is_dir():
            files = [p for p in in_p.glob('**/*.binu8') if p.name != '__global.binu8']
            print(f"[*] Found {len(files)} binu8 files in {in_p}...")
            total = 0
            for p in sorted(files):
                rel = p.relative_to(in_p)
                dst = out_p / rel.with_suffix('.json')
                cnt = extract_script(str(p), str(dst))
                total += cnt
            print(f"[+] Successfully extracted {len(files)} files ({total} total entries) to {out_p}")

    elif args.command == 'insert':
        base_p = Path(args.base)
        json_p = Path(args.json)
        out_p = Path(args.output)
        wrap_val = args.wordwrap
        if base_p.is_file():
            cnt = insert_script(str(base_p), str(json_p), str(out_p), word_wrap=wrap_val)
            print(f"[+] Inserted {cnt} entries into {out_p}")
        elif base_p.is_dir():
            json_files = list(json_p.glob('**/*.json'))
            print(f"[*] Found {len(json_files)} json files in {json_p} (WordWrap={wrap_val})...")
            count = 0
            for jf in sorted(json_files):
                rel = jf.relative_to(json_p)
                bin_base = base_p / rel.with_suffix('.binu8')
                if not bin_base.exists():
                    continue
                bin_out = out_p / rel.with_suffix('.binu8')
                insert_script(str(bin_base), str(jf), str(bin_out), word_wrap=wrap_val)
                count += 1
            print(f"[+] Successfully inserted {count} scripts into {out_p}")

if __name__ == '__main__':
    main()
