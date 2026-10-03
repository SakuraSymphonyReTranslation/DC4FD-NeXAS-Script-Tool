#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ia_dia_fix.py — Apply / De-Apply penggantian kata "ia" -> "dia" pada
terjemahan D.C.4 FD berdasarkan log tinjauan CHANGELOG_ia_dia.csv.

Aturan (sama dengan prompt TL repo):
  "ia" hanya untuk benda mati/tak bernyawa; untuk orang memakai "dia".

Sumber data:
  - Log tinjauan  : scratch/ia_scan/CHANGELOG_ia_dia.csv
                    kolom: no,file,idx,putusan,alasan,sebelum,sesudah,jp
                    putusan = "UBAH ia→dia" | "UBAH Ia→Dia" | "BIARKAN"
  - .binu8 target : romfs/Script_Mod/<file>.binu8
  - JSON kerja    : diekstrak SEGAR dari .binu8 setiap kali apply
                    (tidak lagi bergantung folder cache/ekspor lama)
  - Manifest      : scratch/ia_scan/apply_manifest.json (riwayat apply,
                    ditulis oleh sesi sebelumnya; dipertanggungjawabkan di sini)

Perintah:
  python ia_dia_fix.py status              -- ringkasan log + state apply
  python ia_dia_fix.py apply               -- terapkan semua putusan UBAH
  python ia_dia_fix.py apply --only-file X -- hanya satu file
  python ia_dia_fix.py apply --dry-run     -- simulasi tanpa menulis
  python ia_dia_fix.py deapply             -- pulihkan SEMUA file dari backup
  python ia_dia_fix.py deapply --only-file X

Perilaku penting:
  - apply SELALU mengekstrak ulang JSON dari Script_Mod saat ini, lalu
    menerapkan regex kata-utuh:  ia->dia / Ia->Dia  (idempoten; kata "dia"
    yang sudah ada tidak disentuh; BIARKAN dilewati).
  - Aman terhadap drift: kalau hasil ekstrak tampak sudah pernah diganti
    (idempoten) tetap dilanjutkan; kalau .binu8 gagal di-parse -> FAIL dan
    file dibiarkan.
  - Sebelum menulis .binu8 pertama kali untuk sebuah file, snapshot aslinya
    disimpan ke scratch/ia_scan/backup_binu8/ (TIDAK menimpa snapshot lama,
    karena snapshot lama = kondisi pre-apply yang sah untuk deapply).
  - Insert memakai word_wrap=0 agar pembagian baris (@n) terjemahan yang
    sudah ada TIDAK digeser ulang (roundtrip sudah diverifikasi identik).
  - deapply menyalin balik backup ke Script_Mod untuk file yang tercatat
    pernah di-apply (manifest + state).
"""
import argparse
import csv
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.nexas.nexas_tool import insert_script, extract_script  # noqa: E402

MOD_DIR = ROOT / "romfs" / "Script_Mod"
LOG_CSV = ROOT / "scratch" / "ia_scan" / "CHANGELOG_ia_dia.csv"
BACKUP_DIR = ROOT / "scratch" / "ia_scan" / "backup_binu8"
STATE_FILE = ROOT / "scratch" / "ia_scan" / "ia_dia_state.json"
MANIFEST = ROOT / "scratch" / "ia_scan" / "apply_manifest.json"

WORD_RE = re.compile(r"(?<![A-Za-zÀ-ÿ])([Ii])a(?![A-Za-zÀ-ÿ])")
PUTUSAN_MAP = {
    "UBAH ia→dia": ("ia", "dia"),
    "UBAH Ia→Dia": ("Ia", "Dia"),
}


def load_log():
    if not LOG_CSV.exists():
        print(f"[!] Log tidak ditemukan: {LOG_CSV}")
        sys.exit(1)
    rows = list(csv.DictReader(open(LOG_CSV, encoding="utf-8-sig")))
    # plan: {file: {idx: [putusan, ...]}} - satu idx bisa punya beberapa baris
    # log (pesan panjang berisi beberapa kalimat dengan putusan berbeda)
    plan = {}
    for r in rows:
        plan.setdefault(r["file"], {}).setdefault(int(r["idx"]), []).append(r["putusan"])
    return rows, plan


def load_state():
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE, encoding="utf-8"))
    return {"applied_files": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                          encoding="utf-8")


def applied_set(state):
    s = set(state.get("applied_files", []))
    if MANIFEST.exists():
        try:
            m = json.load(open(MANIFEST, encoding="utf-8"))
            for f in m.get("files", []):
                if f.get("status") == "OK" and f.get("verify") == "OK":
                    s.add(f["file"])
        except Exception:
            pass
    return s


def apply_regex(msg, old, new):
    pat = re.compile(r"(?<![A-Za-zÀ-ÿ])" + re.escape(old) + r"(?![A-Za-zÀ-ÿ])")
    return pat.sub(new, msg)


def do_status(rows, plan):
    cnt = {"UBAH ia→dia": 0, "UBAH Ia→Dia": 0, "BIARKAN": 0}
    for r in rows:
        cnt[r["putusan"]] = cnt.get(r["putusan"], 0) + 1
    applied = applied_set(load_state())
    files = set(plan.keys())
    done = applied & files
    pending = files - applied
    bkp = len(list(BACKUP_DIR.glob("*.binu8"))) if BACKUP_DIR.exists() else 0
    print(f"Log            : {len(rows)} baris di {len(files)} file")
    print(f"Putusan        : UBAH ia->dia={cnt.get('UBAH ia→dia',0)}, "
          f"UBAH Ia->Dia={cnt.get('UBAH Ia→Dia',0)}, BIARKAN={cnt.get('BIARKAN',0)}")
    print(f"Backup .binu8  : {bkp} file ({BACKUP_DIR.relative_to(ROOT)})")
    print(f"Sudah di-apply : {len(done)} dari {len(files)} file")
    if pending:
        ex = sorted(pending)[:5]
        print(f"Belum di-apply : {len(pending)} file — contoh: {ex}")
    else:
        print("Belum di-apply : tidak ada (semua sudah)")


def do_apply(rows, plan, only_file=None, dry=False):
    files = sorted(plan.keys())
    if only_file:
        if only_file not in plan:
            print(f"[!] '{only_file}' tidak ada di log.")
            sys.exit(1)
        files = [only_file]

    already = applied_set(load_state()) if not only_file else set()
    manifest_rows = []
    tot_changed = tot_files = 0
    fails = []

    for fname in files:
        if fname in already:
            continue
        bf = MOD_DIR / (fname + ".binu8")
        if not bf.exists():
            print(f"  ! {fname}: .binu8 tidak ada, dilewati")
            fails.append((fname, "no binu8"))
            continue
        # 1) Ekstrak segar dari Script_Mod saat ini
        tmp_json = ROOT / "scratch" / "ia_scan" / f"_work_{fname}.json"
        try:
            extract_script(str(bf), str(tmp_json))
        except Exception as e:
            print(f"  ! {fname}: extract gagal ({e}) - dilewati")
            fails.append((fname, f"extract: {e}"))
            continue
        entries = json.load(open(tmp_json, encoding="utf-8"))
        rules = plan[fname]
        n_change = 0
        out_of_range = 0
        for idx, putusans in rules.items():
            if idx >= len(entries):
                out_of_range += 1
                continue
            msg = entries[idx].get("message", "")
            new_msg = msg
            for putusan in putusans:
                if putusan == "BIARKAN":
                    continue
                pair = PUTUSAN_MAP.get(putusan)
                if not pair:
                    continue
                new_msg = apply_regex(new_msg, *pair)
            if new_msg != msg:
                entries[idx]["message"] = new_msg
                n_change += 1
        if out_of_range:
            print(f"  ~ {fname}: {out_of_range} index di luar jangkauan (drift log) - diabaikan")
        if n_change == 0:
            print(f"  = {fname}: tidak ada perubahan (mungkin sudah 'dia' semua)")
            tmp_json.unlink(missing_ok=True)
            manifest_rows.append({"file": fname, "status": "NOCHANGE",
                                  "json_changed": 0, "verify": "-", "note": ""})
            continue
        if dry:
            print(f"  (dry) {fname}: akan mengubah {n_change} baris")
            tmp_json.unlink(missing_ok=True)
            tot_changed += n_change
            tot_files += 1
            continue
        # 2) Tulis hasil edit ke JSON kerja (penting: entries diedit di memori)
        json.dump(entries, open(tmp_json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        # 3) Backup (sekali saja; snapshot lama = pre-apply yang sah)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        bkp = BACKUP_DIR / (fname + ".binu8")
        if not bkp.exists():
            shutil.copy2(bf, bkp)
        # 4) Insert ulang (wrap=0: pertahankan @n terjemahan)
        try:
            insert_script(str(bf), str(tmp_json), str(bf), word_wrap=0)
        except Exception as e:
            print(f"  ! {fname}: insert gagal ({e}) - file TIDAK diubah")
            fails.append((fname, f"insert: {e}"))
            tmp_json.unlink(missing_ok=True)
            manifest_rows.append({"file": fname, "status": "FAILED",
                                  "json_changed": n_change, "verify": "-", "note": str(e)[:120]})
            continue
        # 5) Verifikasi: ekstrak ulang & pastikan 0 sisa + jumlah sama
        chk = ROOT / "scratch" / "ia_scan" / f"_check_{fname}.json"
        extract_script(str(bf), str(chk))
        e2 = json.load(open(chk, encoding="utf-8"))
        remain = sum(len(WORD_RE.findall(it.get("message", ""))) for it in e2)
        ok = (len(e2) == len(entries)) and remain == 0
        chk.unlink(missing_ok=True)
        tmp_json.unlink(missing_ok=True)
        tag = "OK" if ok else "CHECK!"
        print(f"  + {fname}: {n_change} baris, sisa 'ia'={remain} [{tag}]")
        manifest_rows.append({"file": fname, "status": "OK" if ok else "CHECK",
                              "json_changed": n_change, "verify": "OK" if ok else "DRIFT",
                              "note": ""})
        tot_changed += n_change
        tot_files += 1

    if dry:
        print(f"\n[dry-run] {tot_changed} baris akan berubah di {tot_files} file")
        return

    if manifest_rows:
        m = {"timestamp": datetime.now().isoformat(timespec="seconds"),
             "csv": str(LOG_CSV), "mode": "fresh-extract, wrap=0",
             "files": manifest_rows,
             "totals": {"files_ok": sum(1 for r in manifest_rows if r["status"] == "OK"),
                        "files_failed": sum(1 for r in manifest_rows if r["status"] == "FAILED"),
                        "rows_changed": tot_changed}}
        MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")

    # state: tandai semua file yang mencoba sukses (OK/NOCHANGE)
    ok_files = [r["file"] for r in manifest_rows if r["status"] in ("OK", "NOCHANGE")]
    st = load_state()
    st["applied_files"] = sorted(set(st.get("applied_files", [])) | set(ok_files) | set(applied_set(st)))
    save_state(st)

    print(f"\n[+] SELESAI: {tot_changed} baris di {tot_files} file"
          + (f", gagal: {len(fails)}" if fails else ""))
    if fails:
        for f, why in fails:
            print(f"    FAIL {f}: {why}")
    print(f"    Backup pre-apply : {BACKUP_DIR.relative_to(ROOT)}")
    print(f"    Untuk membatalkan: python ia_dia_fix.py deapply")


def do_deapply(only_file=None):
    state = load_state()
    applied = sorted(applied_set(state))
    if only_file:
        applied = [only_file] if only_file in applied else []
        if not applied:
            print(f"[!] '{only_file}' tidak tercatat pernah di-apply.")
            return
    if not applied:
        print("Tidak ada catatan file yang pernah di-apply.")
        return
    restored = 0
    for fname in applied:
        bkp = BACKUP_DIR / (fname + ".binu8")
        bf = MOD_DIR / (fname + ".binu8")
        if not bkp.exists():
            print(f"  ! {fname}: backup tidak ada, dilewati")
            continue
        shutil.copy2(bkp, bf)
        restored += 1
        print(f"  - {fname}: dipulihkan dari backup")
    if restored:
        remain = sorted(set(state.get("applied_files", [])) - set(applied))
        save_state({"applied_files": remain})
        if MANIFEST.exists():
            MANIFEST.rename(MANIFEST.with_suffix(".json.prev-deapply"))
        print(f"\n[-] {restored} file dipulihkan ke kondisi pre-apply.")
    else:
        print("Tidak ada yang dipulihkan.")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    ap = argparse.ArgumentParser(description="Apply/De-Apply ia->dia (CHANGELOG_ia_dia.csv)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="ringkasan state")
    p_app = sub.add_parser("apply", help="terapkan penggantian + reinsert .binu8")
    p_app.add_argument("--only-file", help="batasi ke satu file (tanpa ekstensi)")
    p_app.add_argument("--dry-run", action="store_true")
    p_de = sub.add_parser("deapply", help="pulihkan .binu8 dari backup")
    p_de.add_argument("--only-file", help="pulihkan satu file saja")
    args = ap.parse_args()

    rows, plan = load_log()
    if args.cmd == "status":
        do_status(rows, plan)
    elif args.cmd == "apply":
        do_apply(rows, plan, only_file=args.only_file, dry=args.dry_run)
    elif args.cmd == "deapply":
        do_deapply(only_file=args.only_file)


if __name__ == "__main__":
    main()
