#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeXAS Script Tool GUI
Aplikasi visual khusus engine NeXAS (Da Capo 4 Fortunate Departures, Aquarium, dll)
Mendukung Extract (.binu8 -> .json) dan Insert (.json -> .binu8)
Format JSON:
- Dialog:  {"name": "...", "message": "..."}
- Monolog: {"message": "..."}
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Import engine logic from nexas_tool
import nexas_tool

class NeXASGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NeXAS Script Tool - (D.C.4 FD / Aquarium)")
        self.geometry("780x640")
        self.minsize(700, 550)

        # Style configuration (Modern Dark Theme)
        self.configure(bg="#1e1e24")
        self.setup_styles()

        # Build UI
        self.create_widgets()

        # Set default paths if available in current directory
        base_dir = Path(os.getcwd())
        script_dir = base_dir / "romfs" / "Script"
        if script_dir.exists():
            self.ext_in_var.set(str(script_dir))
            self.ext_out_var.set(str(base_dir / "romfs" / "Json_New"))
            self.ins_base_var.set(str(script_dir))
            self.ins_json_var.set(str(base_dir / "romfs" / "Json_New"))
            self.ins_out_var.set(str(base_dir / "romfs" / "Script_Mod"))

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Dark theme colors
        bg_dark = "#1e1e24"
        bg_panel = "#282932"
        accent = "#5c7cfa"
        accent_hover = "#4c6ef5"
        fg_white = "#f8f9fa"
        fg_muted = "#adb5bd"

        style.configure(".", background=bg_dark, foreground=fg_white, font=("Segoe UI", 9))
        style.configure("TNotebook", background=bg_dark, borderwidth=0)
        style.configure("TNotebook.Tab", background=bg_panel, foreground=fg_muted, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", accent)], foreground=[("selected", "#ffffff")])

        style.configure("TFrame", background=bg_dark)
        style.configure("Panel.TFrame", background=bg_panel, relief="flat")
        style.configure("TLabel", background=bg_panel, foreground=fg_white, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=bg_panel, foreground="#74c0fc", font=("Segoe UI", 11, "bold"))
        style.configure("Title.TLabel", background=bg_dark, foreground="#ffffff", font=("Segoe UI", 16, "bold"))

        style.configure("Primary.TButton", background=accent, foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Primary.TButton", background=[("active", accent_hover), ("disabled", "#495057")])

        style.configure("Browse.TButton", background="#3b3d4a", foreground="#ffffff", font=("Segoe UI", 9), borderwidth=0, padding=4)
        style.map("Browse.TButton", background=[("active", "#4c4f60")])

    def create_widgets(self):
        # Header banner
        top_frame = tk.Frame(self, bg="#1e1e24", pady=12, padx=20)
        top_frame.pack(fill="x")

        title_lbl = tk.Label(top_frame, text="NeXAS Script Tool", font=("Segoe UI", 16, "bold"), fg="#74c0fc", bg="#1e1e24")
        title_lbl.pack(side="left")
        subtitle_lbl = tk.Label(top_frame, text="D.C.4 FD / Circus / GIGA Switch & PC", font=("Segoe UI", 9), fg="#adb5bd", bg="#1e1e24")
        subtitle_lbl.pack(side="left", padx=12, pady=5)

        # Tab Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="x", padx=20, pady=5)

        # Tab 1: Extract
        self.tab_extract = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_extract, text="  Extract (.binu8 -> .json)  ")
        self.setup_extract_tab()

        # Tab 2: Insert
        self.tab_insert = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_insert, text="  Insert (.json -> .binu8)  ")
        self.setup_insert_tab()

        # Log frame
        log_frame = tk.Frame(self, bg="#1e1e24", padx=20, pady=10)
        log_frame.pack(fill="both", expand=True)

        log_header = tk.Frame(log_frame, bg="#1e1e24")
        log_header.pack(fill="x", pady=(0, 4))
        tk.Label(log_header, text="Execution Log / Output:", font=("Segoe UI", 9, "bold"), fg="#adb5bd", bg="#1e1e24").pack(side="left")

        clear_btn = tk.Button(log_header, text="Clear Log", command=self.clear_log, bg="#282932", fg="#adb5bd", font=("Segoe UI", 8), relief="flat", padx=6)
        clear_btn.pack(side="right")

        # Text Area with Scrollbar
        text_container = tk.Frame(log_frame, bg="#121316", bd=1, relief="solid")
        text_container.pack(fill="both", expand=True)

        self.log_text = tk.Text(text_container, bg="#14151a", fg="#d1d5db", font=("Consolas", 9), wrap="word", relief="flat", insertbackground="white")
        scrollbar = ttk.Scrollbar(text_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = tk.Label(self, textvariable=self.status_var, bg="#121316", fg="#adb5bd", font=("Segoe UI", 9), anchor="w", padx=15, pady=4)
        status_bar.pack(fill="x", side="bottom")

    def setup_extract_tab(self):
        panel = ttk.Frame(self.tab_extract, style="Panel.TFrame", padding=15)
        panel.pack(fill="both", expand=True, padx=4, pady=8)

        # Input Row
        ttk.Label(panel, text="Folder Script (.binu8) / File Input:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.ext_in_var = tk.StringVar()
        in_entry = tk.Entry(panel, textvariable=self.ext_in_var, font=("Segoe UI", 9), bg="#1e1e24", fg="#ffffff", insertbackground="white", bd=1, relief="solid")
        in_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(0, 10))

        btn_box1 = tk.Frame(panel, bg="#282932")
        btn_box1.grid(row=1, column=1, sticky="w", pady=(0, 10))
        ttk.Button(btn_box1, text="Folder...", style="Browse.TButton", command=lambda: self.browse_folder(self.ext_in_var)).pack(side="left", padx=2)
        ttk.Button(btn_box1, text="File...", style="Browse.TButton", command=lambda: self.browse_file(self.ext_in_var, [("NeXAS Script", "*.binu8")])).pack(side="left", padx=2)

        # Output Row
        ttk.Label(panel, text="Folder Output (.json):").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.ext_out_var = tk.StringVar()
        out_entry = tk.Entry(panel, textvariable=self.ext_out_var, font=("Segoe UI", 9), bg="#1e1e24", fg="#ffffff", insertbackground="white", bd=1, relief="solid")
        out_entry.grid(row=3, column=0, sticky="ew", padx=(0, 6), pady=(0, 10))

        ttk.Button(panel, text="Folder...", style="Browse.TButton", command=lambda: self.browse_folder(self.ext_out_var)).grid(row=3, column=1, sticky="w", pady=(0, 10))

        # Action button
        self.btn_extract = ttk.Button(panel, text="Gas Extract! (.binu8 -> JSON)", style="Primary.TButton", command=self.run_extract)
        self.btn_extract.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        panel.columnconfigure(0, weight=1)

    def setup_insert_tab(self):
        panel = ttk.Frame(self.tab_insert, style="Panel.TFrame", padding=15)
        panel.pack(fill="both", expand=True, padx=4, pady=8)

        # Base binu8
        ttk.Label(panel, text="Folder Asli (.binu8) Base:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.ins_base_var = tk.StringVar()
        base_entry = tk.Entry(panel, textvariable=self.ins_base_var, font=("Segoe UI", 9), bg="#1e1e24", fg="#ffffff", insertbackground="white", bd=1, relief="solid")
        base_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))

        btn_box2 = tk.Frame(panel, bg="#282932")
        btn_box2.grid(row=1, column=1, sticky="w", pady=(0, 8))
        ttk.Button(btn_box2, text="Folder...", style="Browse.TButton", command=lambda: self.browse_folder(self.ins_base_var)).pack(side="left", padx=2)
        ttk.Button(btn_box2, text="File...", style="Browse.TButton", command=lambda: self.browse_file(self.ins_base_var, [("NeXAS Script", "*.binu8")])).pack(side="left", padx=2)

        # Translated JSON
        ttk.Label(panel, text="Folder JSON Terjemahan (Input):").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.ins_json_var = tk.StringVar()
        json_entry = tk.Entry(panel, textvariable=self.ins_json_var, font=("Segoe UI", 9), bg="#1e1e24", fg="#ffffff", insertbackground="white", bd=1, relief="solid")
        json_entry.grid(row=3, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))

        btn_box3 = tk.Frame(panel, bg="#282932")
        btn_box3.grid(row=3, column=1, sticky="w", pady=(0, 8))
        ttk.Button(btn_box3, text="Folder...", style="Browse.TButton", command=lambda: self.browse_folder(self.ins_json_var)).pack(side="left", padx=2)
        ttk.Button(btn_box3, text="File...", style="Browse.TButton", command=lambda: self.browse_file(self.ins_json_var, [("JSON Files", "*.json")])).pack(side="left", padx=2)

        # Output Mod binu8
        ttk.Label(panel, text="Folder Output (.binu8 Mod / LayeredFS):").grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.ins_out_var = tk.StringVar()
        out_entry = tk.Entry(panel, textvariable=self.ins_out_var, font=("Segoe UI", 9), bg="#1e1e24", fg="#ffffff", insertbackground="white", bd=1, relief="solid")
        out_entry.grid(row=5, column=0, sticky="ew", padx=(0, 6), pady=(0, 10))

        ttk.Button(panel, text="Folder...", style="Browse.TButton", command=lambda: self.browse_folder(self.ins_out_var)).grid(row=5, column=1, sticky="w", pady=(0, 10))

        # Word Wrap Row
        wrap_frame = tk.Frame(panel, bg="#282932")
        wrap_frame.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 14))

        ttk.Label(wrap_frame, text="Panjang WordWrap (0 = Mati / Rekomendasi 56):").pack(side="left", padx=(0, 8))
        self.ins_wrap_var = tk.IntVar(value=56)
        self.wrap_entry = tk.Entry(wrap_frame, textvariable=self.ins_wrap_var, width=8, font=("Segoe UI", 10, "bold"), bg="#14151a", fg="#74c0fc", insertbackground="white", justify="center", bd=1, relief="solid")
        self.wrap_entry.pack(side="left", ipady=2)

        # Quick preset buttons
        tk.Button(wrap_frame, text="56 (Aman / Rekomendasi)", command=lambda: self.ins_wrap_var.set(56), bg="#3b3d4a", fg="#ffffff", font=("Segoe UI", 8), relief="flat", padx=5).pack(side="left", padx=(8, 2))
        tk.Button(wrap_frame, text="52 (Padat)", command=lambda: self.ins_wrap_var.set(52), bg="#3b3d4a", fg="#adb5bd", font=("Segoe UI", 8), relief="flat", padx=5).pack(side="left", padx=2)
        tk.Button(wrap_frame, text="0 (Mati)", command=lambda: self.ins_wrap_var.set(0), bg="#3b3d4a", fg="#adb5bd", font=("Segoe UI", 8), relief="flat", padx=2).pack(side="left", padx=2)

        # Action button
        self.btn_insert = ttk.Button(panel, text="Gas Insert! (JSON -> .binu8)", style="Primary.TButton", command=self.run_insert)
        self.btn_insert.grid(row=7, column=0, columnspan=2, sticky="ew")

        panel.columnconfigure(0, weight=1)

    def browse_folder(self, target_var):
        path = filedialog.askdirectory()
        if path:
            target_var.set(os.path.normpath(path))

    def browse_file(self, target_var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            target_var.set(os.path.normpath(path))

    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def run_extract(self):
        in_path = self.ext_in_var.get().strip()
        out_path = self.ext_out_var.get().strip()

        if not in_path or not os.path.exists(in_path):
            messagebox.showerror("Error", "Path input script (.binu8) tidak valid atau tidak ditemukan!")
            return
        if not out_path:
            messagebox.showerror("Error", "Tentukan path output JSON!")
            return

        self.btn_extract.config(state="disabled")
        self.status_var.set("Extracting script...")

        def task():
            try:
                p_in = Path(in_path)
                p_out = Path(out_path)

                if p_in.is_file():
                    self.log(f"[*] Extracting single file: {p_in.name}...")
                    if p_out.suffix.lower() != '.json':
                        p_out = p_out / (p_in.stem + '.json')
                    cnt = nexas_tool.extract_script(str(p_in), str(p_out))
                    self.log(f"[+] Selesai! Berhasil mengekstrak {cnt} baris ke: {p_out.name}")
                else:
                    files = [f for f in p_in.glob('**/*.binu8') if f.name != '__global.binu8']
                    self.log(f"[*] Menemukan {len(files)} file .binu8 di {p_in}...")
                    total_cnt = 0
                    for f in sorted(files):
                        rel = f.relative_to(p_in)
                        dst = p_out / rel.with_suffix('.json')
                        cnt = nexas_tool.extract_script(str(f), str(dst))
                        total_cnt += cnt
                        self.log(f"  - {f.name}: {cnt} dialog/monolog diekstrak")
                    self.log(f"[+] SELESAI! Total {len(files)} file ({total_cnt} dialog/monolog) tersimpan di:\n    {p_out}")

                self.status_var.set("Extract selesai!")
                messagebox.showinfo("Sukses", "Ekstraksi script selesai dengan sukses!")
            except Exception as e:
                self.log(f"[!] Error saat ekstraksi: {e}")
                self.status_var.set("Error saat ekstraksi.")
                messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
            finally:
                self.btn_extract.config(state="normal")

        threading.Thread(target=task, daemon=True).start()

    def run_insert(self):
        base_path = self.ins_base_var.get().strip()
        json_path = self.ins_json_var.get().strip()
        out_path = self.ins_out_var.get().strip()
        wrap_val = self.ins_wrap_var.get()

        if not base_path or not os.path.exists(base_path):
            messagebox.showerror("Error", "Path base (.binu8 asli) tidak ditemukan!")
            return
        if not json_path or not os.path.exists(json_path):
            messagebox.showerror("Error", "Path JSON terjemahan tidak ditemukan!")
            return
        if not out_path:
            messagebox.showerror("Error", "Tentukan path folder output mod!")
            return

        self.btn_insert.config(state="disabled")
        self.status_var.set("Inserting translated script...")

        def task():
            try:
                b_p = Path(base_path)
                j_p = Path(json_path)
                o_p = Path(out_path)

                if b_p.is_file() and j_p.is_file():
                    self.log(f"[*] Rebuilding single file: {b_p.name} (WordWrap={wrap_val})...")
                    if o_p.suffix.lower() != '.binu8':
                        o_p = o_p / b_p.name
                    cnt = nexas_tool.insert_script(str(b_p), str(j_p), str(o_p), word_wrap=wrap_val)
                    self.log(f"[+] Selesai! {cnt} baris terjemahan berhasil diinjeksi ke: {o_p.name}")
                else:
                    json_files = list(j_p.glob('**/*.json'))
                    self.log(f"[*] Menemukan {len(json_files)} file JSON di {j_p} (WordWrap={wrap_val})...")
                    inserted_cnt = 0
                    for jf in sorted(json_files):
                        rel = jf.relative_to(j_p)
                        bin_orig = b_p / rel.with_suffix('.binu8')
                        if not bin_orig.exists():
                            self.log(f"  [Skip] Base binu8 tidak ditemukan untuk: {jf.name}")
                            continue
                        bin_out = o_p / rel.with_suffix('.binu8')
                        cnt = nexas_tool.insert_script(str(bin_orig), str(jf), str(bin_out), word_wrap=wrap_val)
                        inserted_cnt += 1
                        self.log(f"  - Injected {jf.name} -> {bin_out.name} ({cnt} baris)")
                    self.log(f"[+] SELESAI! Berhasil merekonstruksi {inserted_cnt} file .binu8 ke:\n    {o_p}")

                # Copy custom system.datu8 to mod Config if available
                custom_cfg = Path(os.getcwd()) / "romfs" / "Custom Config" / "system.datu8"
                if custom_cfg.exists():
                    target_cfg_dir = o_p.parent / "Config"
                    target_cfg_dir.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(str(custom_cfg), str(target_cfg_dir / "system.datu8"))
                    self.log(f"[+] Otomatis menyertakan file font Custom Config:\n    -> {target_cfg_dir / 'system.datu8'}")

                self.status_var.set("Insert selesai!")
                messagebox.showinfo("Sukses", "Injeksi script selesai dengan sukses!")
            except Exception as e:
                self.log(f"[!] Error saat insert: {e}")
                self.status_var.set("Error saat insert.")
                messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
            finally:
                self.btn_insert.config(state="normal")

        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    app = NeXASGUI()
    app.mainloop()
