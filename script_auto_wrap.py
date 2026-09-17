import re
import unicodedata

MAX_CHARS = 56

# Control code NeXAS.
# Control code tidak dihitung sebagai karakter layar.
CONTROL_CODE = re.compile(
    r'@(?:v[A-Za-z0-9_]+|h[A-Za-z0-9_]+|t\d+|n|k|g)'
)


def char_width(c):
    """Menghitung lebar visual karakter (Fullwidth / CJK = 2, Halfwidth / ASCII = 1)."""
    if c in '\u3000…「」『』・―〜～★☆♪※♥':
        return 2
    w = unicodedata.east_asian_width(c)
    if w in ('F', 'W'):
        return 2
    return 1


def visible_length(text):
    """Menghitung lebar kolom visual yang benar-benar terlihat di layar."""
    clean = CONTROL_CODE.sub("", text)
    return sum(char_width(c) for c in clean)


def tokenize(text):
    """
    Memisahkan teks menjadi token kata, whitespace, dan control code.
    Control code dipertahankan tetapi tidak dihitung.
    """

    pattern = re.compile(
        r'@(?:v[A-Za-z0-9_]+|h[A-Za-z0-9_]+|t\d+|n|k|g)'
        r'|\s+'
        r'|[^\s@]+'
    )

    return pattern.findall(text)


def wrap_text(text, max_chars=MAX_CHARS, initial_width=0):
    """
    Auto-wrap cerdas dengan batas visual lebar karakter.

    - Mendukung initial_width jika teks merupakan sambungan kalimat sebelumnya (@k).
    - Mempertahankan indentasi \u3000 pada awal narasi.
    - Tidak memotong kata (kata yang tidak muat langsung turun utuh ke baris berikutnya).
    - Memperhitungkan karakter fullwidth sebagai 2 kolom tampilan.
    - Spasi dihitung.
    - @n digunakan sebagai line break.
    - @n lama dihapus dan posisi wrap dihitung ulang.
    - Control code tidak dihitung.
    """

    leading_indent = ""
    if text.startswith("\u3000"):
        leading_indent = "\u3000"
        text = text[1:]
        initial_width += 2

    # Hapus @n lama.
    text = text.replace("@n", "")

    tokens = tokenize(text)

    lines = []
    current = ""
    pending_space = ""

    for token in tokens:

        # Whitespace menjadi separator.
        if token.isspace():
            pending_space = token
            continue

        # Control code tidak dihitung sebagai karakter.
        if CONTROL_CODE.fullmatch(token):
            current += pending_space + token
            pending_space = ""
            continue

        # Token ini adalah teks/kata biasa.
        word = token

        separator = pending_space if current else ""
        candidate = current + separator + word

        eff_width = (initial_width if not lines else 0) + visible_length(candidate)

        if eff_width <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            elif initial_width > 0 and not lines:
                # Kata pertama tidak muat di sisa ruang baris sebelumnya,
                # langsung turun ke baris baru
                lines.append("")
            current = word
            initial_width = 0

        pending_space = ""

    if current:
        lines.append(current)

    if leading_indent and lines:
        lines[0] = leading_indent + lines[0]

    # Jangan membuat @n setelah baris terakhir.
    return "@n".join(lines)


def is_marker_line(line):
    """Mendeteksi marker ○00000000○ / ●00000000●."""
    return bool(re.fullmatch(r'\s*[○●].*[○●]\s*', line))


def process_line(line):
    """
    Memproses satu physical line.
    Tidak pernah membuat newline tambahan.
    """

    if not line.strip():
        return line

    # Marker tidak disentuh.
    if is_marker_line(line):
        return line

    # Pertahankan indentasi asli.
    leading_match = re.match(r'^\s*', line)
    leading = leading_match.group(0)

    body = line[len(leading):]

    if not body:
        return line

    return leading + wrap_text(body)


def process_file(input_file, output_file):

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []

    for line in lines:
        # Hilangkan newline physical line sementara.
        content = line.rstrip("\r\n")

        processed = process_line(content)

        # Selalu satu physical line.
        output_lines.append(processed)

    with open(output_file, "w", encoding="utf-8", newline="\n") as f:
        for line in output_lines:
            f.write(line + "\n")

    print("Selesai.")
    print(f"Jumlah physical line input : {len(lines)}")
    print(f"Jumlah physical line output: {len(output_lines)}")
    print(f"Output: {output_file}")


def main():

    input_file = input("File input  : ").strip()
    output_file = input("File output : ").strip()

    process_file(input_file, output_file)


if __name__ == "__main__":
    main()