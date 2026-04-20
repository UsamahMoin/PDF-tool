#!/usr/bin/env python3
"""PDF Tool — Split · Merge · Extract · Vector DB"""

import os, math, threading, subprocess, textwrap, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pypdf import PdfReader, PdfWriter

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND  = True
    _Base = TkinterDnD.Tk
except ImportError:
    _DND  = False
    _Base = tk.Tk

# ── Tokens — Anthropic / Claude-inspired ──────────────────────────────────────
BG     = "#0F0F0F"   # near-black window bg
CARD   = "#1A1A1A"   # elevated surfaces
CARD2  = "#252525"   # raised elements / button bg
BORDER = "#333333"   # dividers / subtle borders
FG     = "#EBE5DC"   # primary text — warm off-white
FG2    = "#7A7572"   # secondary / muted text
ACCENT = "#CF5F2A"   # Anthropic coral-orange
A_HOV  = "#DC6D38"   # accent hover
GREEN  = "#4EB87D"   # success
RED    = "#D94040"   # error
FONT   = "SF Pro Display"

# ── Utility ───────────────────────────────────────────────────────────────────

def fmt_size(path):
    b = os.path.getsize(path)
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024

def stem(path): return os.path.splitext(os.path.basename(path))[0]

def reveal(path):
    subprocess.call(["open", path if os.path.isdir(path) else os.path.dirname(path)])

def parse_spec(spec, total):
    pages = set()
    for p in spec.replace(" ","").split(","):
        if not p: continue
        try:
            if "-" in p:
                a,b = p.split("-",1); pages.update(range(int(a)-1,int(b)))
            else: pages.add(int(p)-1)
        except ValueError: pass
    return sorted(x for x in pages if 0<=x<total)

def pdf_info(path): return len(PdfReader(path).pages), fmt_size(path)

def chunk_text(text, size, overlap):
    out, s = [], 0
    while s < len(text):
        out.append(text[s:s+size]); s += size-overlap
    return [c for c in out if c.strip()]

# ── PDF workers ───────────────────────────────────────────────────────────────

def do_split(src, outdir, mode, value, spec, cb):
    r = PdfReader(src); total = len(r.pages); name = stem(src); out = []
    if mode == "custom":
        idx = parse_spec(spec, total)
        if not idx: raise ValueError("No valid pages in custom spec.")
        w = PdfWriter()
        for i in idx: w.add_page(r.pages[i])
        fn = f"{name}_custom_{len(idx)}pages.pdf"; p = os.path.join(outdir,fn)
        with open(p,"wb") as f: w.write(f)
        out.append(p); cb(1,1,fn)
    else:
        cs = value if mode=="pages" else math.ceil(total/value)
        nc = math.ceil(total/cs); s=n=0
        while s < total:
            n+=1; e=min(s+cs,total); w=PdfWriter(); w.append(r,pages=range(s,e))
            fn = f"{name}_part{n:03d}_p{s+1}-{e}.pdf"; p = os.path.join(outdir,fn)
            with open(p,"wb") as f: w.write(f)
            out.append(p); cb(n,nc,fn); s=e
    return out

def do_merge(paths, output, cb):
    w = PdfWriter(); total = 0
    for i,p in enumerate(paths):
        rr = PdfReader(p); w.append(rr); total += len(rr.pages)
        cb(i+1,len(paths),os.path.basename(p))
    with open(output,"wb") as f: w.write(f)
    return total

def do_extract(path, start, end):
    r = PdfReader(path)
    for i in range(start,end): yield i+1,(r.pages[i].extract_text() or "")

def do_vectordb(pdf_paths, outdir, coll, chunk_sz, overlap, cb):
    import chromadb
    os.makedirs(outdir, exist_ok=True)
    client = chromadb.PersistentClient(path=outdir)
    try: client.delete_collection(coll)
    except Exception: pass
    col = client.create_collection(name=coll, metadata={"hnsw:space":"cosine"})
    ids,docs,metas = [],[],[]
    for fi,path in enumerate(pdf_paths):
        r = PdfReader(path); np = len(r.pages); fn = os.path.basename(path)
        for pi,page in enumerate(r.pages):
            cb(fi,len(pdf_paths),fn,pi+1,np)
            for ci,chunk in enumerate(chunk_text(page.extract_text() or "",chunk_sz,overlap)):
                ids.append(f"{stem(path)}_p{pi+1}_c{ci}")
                docs.append(chunk)
                metas.append({"source":fn,"page":pi+1,"chunk":ci})
    for i in range(0,len(ids),100):
        col.upsert(ids=ids[i:i+100],documents=docs[i:i+100],metadatas=metas[i:i+100])
    return len(ids), coll

# ── Shared widgets ────────────────────────────────────────────────────────────

class TabbedPane(tk.Frame):
    """
    Custom tab bar using ttk.Button tabs (single-click reliable on macOS).
    Content switching: grid() / grid_remove() — all frames occupy the same
    cell (row=0,col=0); grid_remove() hides without forgetting grid options
    so grid() alone restores the frame instantly.
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)

        # Tab strip
        self._strip = tk.Frame(self, bg=CARD2)
        self._strip.pack(fill="x")

        # 2-px coral accent underline, repositioned via place on each select()
        self._accent = tk.Frame(self._strip, bg=ACCENT, height=2)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Body — all tab frames grid into cell (0,0); only one is shown at a time
        self._body = tk.Frame(self, bg=BG)
        self._body.pack(fill="both", expand=True)
        self._body.rowconfigure(0, weight=1)
        self._body.columnconfigure(0, weight=1)

        self._tabs: list[tuple[ttk.Button, tk.Frame]] = []

    def add(self, frame, text):
        idx = len(self._tabs)
        btn = ttk.Button(self._strip, text=text,
                         style="Tab.TButton", cursor="hand2",
                         command=lambda i=idx: self.select(i))
        btn.pack(side="left")
        # Place frame in the grid cell but hide it; select() will reveal it
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()
        self._tabs.append((btn, frame))

    def _reposition_accent(self, btn):
        self._strip.update_idletasks()
        self._accent.place(in_=self._strip,
                           x=btn.winfo_x(), rely=1.0, anchor="sw",
                           width=btn.winfo_width(), height=2)
        self._accent.lift()

    def select(self, idx):
        for i, (btn, frame) in enumerate(self._tabs):
            if i == idx:
                btn.configure(style="TabActive.TButton")
                frame.grid()          # restore grid — makes it visible
            else:
                btn.configure(style="Tab.TButton")
                frame.grid_remove()   # hide but remember grid options
        self.after(15, lambda: self._reposition_accent(self._tabs[idx][0]))


class DropZone(tk.Canvas):
    def __init__(self, parent, label, sub, on_click, on_drop=None, **kw):
        super().__init__(parent, height=80, bg=BG, highlightthickness=0, **kw)
        self._label=label; self._sub=sub; self._hover=False
        self.bind("<Button-1>",  lambda _: on_click())
        self.bind("<Enter>",     lambda _: self._hov(True))
        self.bind("<Leave>",     lambda _: self._hov(False))
        self.bind("<Configure>", lambda _: self._draw())
        if on_drop and _DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", on_drop)

    def _hov(self, v):
        self._hover=v; self._draw()
        self.config(cursor="hand2" if v else "")

    def _draw(self):
        self.delete("all")
        W = max(self.winfo_width(), 1); H = max(self.winfo_height(), 1)
        c = ACCENT if self._hover else BORDER
        self.create_rectangle(16, 8, W-16, H-8,
            outline=c, fill=CARD, width=1, dash=(6,4))
        self.create_text(W//2, H//2-9, text=self._label,
            fill=FG, font=(FONT,11,"bold"), anchor="center")
        self.create_text(W//2, H//2+10, text=self._sub,
            fill=ACCENT if self._hover else FG2,
            font=(FONT,9), anchor="center")

    def set(self, label, sub=""):
        self._label=label; self._sub=sub; self._draw()


class Stepper(tk.Frame):
    """[ − ]  value  [ + ] — replaces tiny spinbox arrows."""

    def __init__(self, parent, from_=1, to=9999, initial=1, step=1, width=5, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._from = from_; self._to = to; self._step = step
        self._var = tk.StringVar(value=str(initial))
        ttk.Button(self, text="−", style="Stepper.TButton",
                   command=self._dec).pack(side="left")
        ttk.Entry(self, textvariable=self._var, width=width,
                  justify="center", font=(FONT,12)).pack(side="left", padx=2)
        ttk.Button(self, text="+", style="Stepper.TButton",
                   command=self._inc).pack(side="left")

    def _val(self):
        try: return int(self._var.get())
        except: return self._from

    def _dec(self): self._var.set(str(max(self._from, self._val()-self._step)))
    def _inc(self): self._var.set(str(min(self._to,   self._val()+self._step)))
    def get(self):  return self._val()
    def set(self, v): self._var.set(str(v))


class ProgBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(4,2))
        self._var  = tk.StringVar()
        self._lbl  = tk.Label(row, textvariable=self._var,
                              bg=BG, fg=FG2, font=(FONT,10), anchor="w")
        self._lbl.pack(side="left", fill="x", expand=True)
        self._obtn = ttk.Button(row, text="Open in Finder",
                                style="Secondary.TButton",
                                cursor="hand2", command=self._open)
        self._opath = None
        self._bar = ttk.Progressbar(self, mode="determinate", maximum=100)
        self._bar.pack(fill="x", padx=24, pady=(0,10))

    def working(self, text="Working…"):
        self._obtn.pack_forget()
        self._lbl.configure(fg=FG2); self._var.set(text)
        self._bar.configure(mode="indeterminate"); self._bar.start(10)

    def step(self, done, total, detail=""):
        self._bar.configure(mode="determinate"); self._bar.stop()
        pct = int(done/total*100) if total else 0
        self._bar["value"] = pct
        self._lbl.configure(fg=FG2); self._var.set(f"{detail}    {pct}%")

    def done(self, text, path=None):
        self._bar.configure(mode="determinate"); self._bar.stop()
        self._bar["value"] = 100
        self._lbl.configure(fg=GREEN); self._var.set(text)
        if path: self._opath=path; self._obtn.pack(side="right")

    def error(self, text):
        self._bar.configure(mode="determinate"); self._bar.stop()
        self._bar["value"] = 0
        self._lbl.configure(fg=RED); self._var.set(text)

    def reset(self):
        self._obtn.pack_forget()
        self._bar.configure(mode="determinate"); self._bar.stop()
        self._bar["value"] = 0
        self._var.set(""); self._lbl.configure(fg=FG2)

    def _open(self):
        if self._opath: reveal(self._opath)


def _btn(parent, text, cmd, primary=False, **kw):
    style = "Primary.TButton" if primary else "Secondary.TButton"
    return ttk.Button(parent, text=text, command=cmd,
                      style=style, cursor="hand2", **kw)


def _lbl(parent, text, secondary=False, top=None):
    default_top = 0 if secondary else 18
    tp = top if top is not None else default_top
    tk.Label(parent, text=text, bg=BG,
             fg=FG2 if secondary else FG,
             font=(FONT, 9 if secondary else 10, "bold")
             ).pack(anchor="w", padx=24, pady=(tp, 4))


def _div(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=10)


# ── Main window ───────────────────────────────────────────────────────────────

class App(_Base):

    def __init__(self):
        super().__init__()
        self.title("PDF Tool")
        self.minsize(740, 640)
        self.configure(bg=BG)
        self._apply_styles()
        self._build()
        self.eval("tk::PlaceWindow . center")
        self.after(80, self._activate)

    def _activate(self):
        """Force app to foreground on macOS without triggering accessibility dialogs."""
        self.focus_force()
        self.lift()

    def _apply_styles(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, font=(FONT,11))
        s.configure("TFrame",    background=BG)
        s.configure("TLabel",    background=BG, foreground=FG)
        s.configure("TEntry",
            fieldbackground=CARD, foreground=FG,
            insertcolor=FG, borderwidth=0, relief="flat", padding=8)
        s.configure("TScrollbar",
            background=CARD2, troughcolor=CARD,
            borderwidth=0, arrowcolor=FG2)
        s.configure("TProgressbar",
            troughcolor=CARD2, background=ACCENT,
            borderwidth=0, relief="flat")
        s.configure("TRadiobutton", background=BG, foreground=FG)
        s.configure("Treeview",
            background=CARD, foreground=FG,
            fieldbackground=CARD, rowheight=30, borderwidth=0)
        s.configure("Treeview.Heading",
            background=CARD2, foreground=FG2,
            borderwidth=0, relief="flat", font=(FONT,9,"bold"))
        s.map("Treeview",
            background=[("selected",ACCENT)],
            foreground=[("selected","#ffffff")])
        # Primary button — Anthropic coral
        s.configure("Primary.TButton",
            background=ACCENT, foreground="white",
            font=(FONT,12,"bold"), borderwidth=0, relief="flat",
            padding=[32, 11], anchor="center")
        s.map("Primary.TButton",
            background=[("active",A_HOV),("disabled",CARD2),("pressed",A_HOV)],
            foreground=[("active","white"),("disabled",FG2),("pressed","white")])
        # Secondary button
        s.configure("Secondary.TButton",
            background=CARD2, foreground=FG,
            font=(FONT,10), borderwidth=0, relief="flat",
            padding=[14, 6], anchor="center")
        s.map("Secondary.TButton",
            background=[("active",BORDER),("pressed",BORDER)],
            foreground=[("active",FG),("pressed",FG)])
        # Tab bar buttons — inactive
        s.configure("Tab.TButton",
            background=CARD2, foreground=FG2,
            font=(FONT, 11), borderwidth=0, relief="flat",
            padding=[20, 10], anchor="center")
        s.map("Tab.TButton",
            background=[("active", BORDER), ("pressed", BORDER)],
            foreground=[("active", FG), ("pressed", FG)])
        # Tab bar buttons — active/selected
        s.configure("TabActive.TButton",
            background=BG, foreground=FG,
            font=(FONT, 11, "bold"), borderwidth=0, relief="flat",
            padding=[20, 10], anchor="center")
        s.map("TabActive.TButton",
            background=[("active", BG), ("pressed", BG)],
            foreground=[("active", FG), ("pressed", FG)])
        # Stepper +/- buttons
        s.configure("Stepper.TButton",
            background=CARD2, foreground=FG,
            font=(FONT,13,"bold"), borderwidth=0, relief="flat",
            padding=[10, 5], anchor="center")
        s.map("Stepper.TButton",
            background=[("active",BORDER),("pressed",BORDER)],
            foreground=[("active",FG),("pressed",FG)])

    def _build(self):
        # Custom tabbed pane
        nb = TabbedPane(self)
        nb.pack(fill="both", expand=True)

        for text, builder in [
            ("  Split  ",        self._split_tab),
            ("  Merge  ",        self._merge_tab),
            ("  Extract Text  ", self._extract_tab),
            ("  Vector DB  ",    self._vectordb_tab),
        ]:
            f = tk.Frame(nb._body, bg=BG)
            builder(f)
            nb.add(f, text)

        nb.select(0)  # Start on Split tab

        # Status bar
        sb = tk.Frame(self, bg=CARD, height=26); sb.pack_propagate(False)
        sb.pack(fill="x")
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", side="top")
        self._sb_var = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self._sb_var,
                 bg=CARD, fg=FG2, font=(FONT,9)).pack(side="left", padx=16, pady=4)

    def _sb(self, t): self._sb_var.set(t)
    def _set_busy(self, on): self.config(cursor="watch" if on else "")

    def _run_bg(self, fn, on_ok, on_err):
        def _t():
            try:    self.after(0, on_ok, fn())
            except Exception as e: self.after(0, on_err, e)
        threading.Thread(target=_t, daemon=True).start()

    # ═════════════════════════════════════════════════════════════════════════
    # SPLIT TAB
    # ═════════════════════════════════════════════════════════════════════════

    def _split_tab(self, f):
        self._sp_path = ""

        self._sp_zone = DropZone(f, "Choose a PDF to split",
            "drag & drop  ·  or click to browse",
            on_click=self._sp_pick, on_drop=self._sp_drop)
        self._sp_zone.pack(fill="x", padx=20, pady=(20,0))
        self._sp_info = tk.Label(f, text="", bg=BG, fg=FG2, font=(FONT,10))

        _div(f)

        _lbl(f, "SPLIT MODE", secondary=True)
        mf = tk.Frame(f, bg=BG); mf.pack(anchor="w", padx=24)
        self._sp_mode = tk.StringVar(value="pages")
        for v,t in [("pages","Pages per chunk"),
                    ("parts","Equal parts"),
                    ("custom","Custom page list")]:
            tk.Radiobutton(mf, text=t, variable=self._sp_mode, value=v,
                           command=self._sp_mode_upd,
                           bg=BG, fg=FG, selectcolor=CARD2,
                           activebackground=BG, font=(FONT,11)
                           ).pack(side="left", padx=(0,22))

        self._sp_num_f = tk.Frame(f, bg=BG)
        self._sp_num_f.pack(anchor="w", padx=24, pady=(16,0))
        self._sp_val_lbl = tk.Label(self._sp_num_f, text="PAGES PER CHUNK",
                                    bg=BG, fg=FG2, font=(FONT,9,"bold"))
        self._sp_val_lbl.pack(anchor="w", pady=(0,6))
        self._sp_val = Stepper(self._sp_num_f, from_=1, to=9999, initial=1)
        self._sp_val.pack(anchor="w")

        self._sp_cust_f = tk.Frame(f, bg=BG)
        tk.Label(self._sp_cust_f, text="PAGES TO EXTRACT",
                 bg=BG, fg=FG2, font=(FONT,9,"bold")).pack(anchor="w", pady=(0,6))
        ef = tk.Frame(self._sp_cust_f, bg=BG); ef.pack(anchor="w")
        self._sp_spec = tk.StringVar()
        ttk.Entry(ef, textvariable=self._sp_spec, width=30).pack(side="left")
        tk.Label(ef, text="   e.g.  1, 3, 5-10, 15",
                 bg=BG, fg=FG2, font=(FONT,9)).pack(side="left")

        _div(f)

        _lbl(f, "OUTPUT FOLDER", secondary=True)
        of = tk.Frame(f, bg=BG); of.pack(fill="x", padx=24, pady=(0,6))
        self._sp_outdir = tk.StringVar()
        ttk.Entry(of, textvariable=self._sp_outdir,
                  state="readonly").pack(side="left", fill="x", expand=True)
        _btn(of, "Browse", self._sp_browse_dir).pack(side="left", padx=(8,0))

        _div(f)

        af = tk.Frame(f, bg=BG); af.pack(pady=(2,0))
        self._sp_btn = _btn(af, "Split PDF", self._sp_run, primary=True)
        self._sp_btn.pack()
        self._sp_prog = ProgBar(f); self._sp_prog.pack(fill="x")

    def _sp_mode_upd(self):
        m = self._sp_mode.get()
        if m == "custom":
            self._sp_num_f.pack_forget()
            self._sp_cust_f.pack(anchor="w", padx=24, pady=(16,0))
        else:
            self._sp_cust_f.pack_forget()
            self._sp_num_f.pack(anchor="w", padx=24, pady=(16,0))
            self._sp_val_lbl.configure(
                text="PAGES PER CHUNK" if m=="pages" else "NUMBER OF PARTS")

    def _sp_load(self, path):
        self._sp_path = path
        try:
            pages, sz = pdf_info(path)
            self._sp_info.configure(
                text=f"  {os.path.basename(path)}   ·   {pages} pages   ·   {sz}")
            self._sp_info.pack(anchor="w", padx=24, pady=(6,0))
            self._sp_zone.set(os.path.basename(path), "Click to choose a different file")
            if not self._sp_outdir.get():
                self._sp_outdir.set(os.path.dirname(path))
            self._sp_prog.reset()
            self._sb(f"Loaded  {os.path.basename(path)}  ({pages} pages)")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _sp_pick(self):
        p = filedialog.askopenfilename(title="Select PDF to split",
            filetypes=[("PDF","*.pdf"),("All files","*.*")])
        if p: self._sp_load(p)

    def _sp_drop(self, e):
        p = e.data.strip().strip("{}");
        if p.lower().endswith(".pdf"): self._sp_load(p)

    def _sp_browse_dir(self):
        d = filedialog.askdirectory(title="Output folder")
        if d: self._sp_outdir.set(d)

    def _sp_run(self):
        if not self._sp_path:
            messagebox.showwarning("No file","Choose a PDF to split."); return
        if not self._sp_outdir.get():
            messagebox.showwarning("No folder","Choose an output folder."); return

        self._sp_btn.configure(state="disabled", text="Splitting…")
        self._sp_prog.working("Preparing…")
        self._set_busy(True); self.update()

        path=self._sp_path; outdir=self._sp_outdir.get()
        mode=self._sp_mode.get(); val=self._sp_val.get(); spec=self._sp_spec.get()

        def _cb(done,total,name): self.after(0, self._sp_prog.step, done, total, name)
        def _ok(out):
            def _():
                self._sp_prog.done(f"{len(out)} file(s) created", outdir)
                self._sp_btn.configure(state="normal", text="Split PDF")
                self._set_busy(False); self._sb(f"Split complete — {len(out)} files")
            self.after(0, _)
        def _err(e):
            def _():
                self._sp_prog.error(str(e))
                self._sp_btn.configure(state="normal", text="Split PDF")
                self._set_busy(False); messagebox.showerror("Split failed", str(e))
            self.after(0, _)

        self._run_bg(lambda: do_split(path,outdir,mode,val,spec,_cb), _ok, _err)

    # ═════════════════════════════════════════════════════════════════════════
    # MERGE TAB
    # ═════════════════════════════════════════════════════════════════════════

    def _merge_tab(self, f):
        self._mg_paths: list[str] = []

        _lbl(f, "PDFS TO MERGE", secondary=True, top=20)
        tv_f = tk.Frame(f, bg=CARD); tv_f.pack(fill="both", expand=True, padx=20)
        cols = ("num","name","pages","size")
        self._mg_tv = ttk.Treeview(tv_f, columns=cols, show="headings",
                                    height=9, selectmode="browse")
        for col,lbl,w,a in [("num","#",44,"center"),("name","Filename",330,"w"),
                              ("pages","Pages",74,"center"),("size","Size",90,"e")]:
            self._mg_tv.heading(col,text=lbl,anchor=a)
            self._mg_tv.column(col,width=w,anchor=a,stretch=(col=="name"))
        vsb = ttk.Scrollbar(tv_f, orient="vertical", command=self._mg_tv.yview)
        self._mg_tv.configure(yscrollcommand=vsb.set)
        self._mg_tv.pack(side="left",fill="both",expand=True)
        vsb.pack(side="right",fill="y")

        cf = tk.Frame(f, bg=BG); cf.pack(fill="x", padx=20, pady=(8,0))
        for t,cmd in [("Add PDFs",self._mg_add),("Remove",self._mg_del),
                       ("Move Up",self._mg_up),("Move Down",self._mg_dn),
                       ("Clear All",self._mg_clear)]:
            _btn(cf, t, cmd).pack(side="left", padx=(0,6))
        self._mg_count_var = tk.StringVar()
        tk.Label(cf, textvariable=self._mg_count_var,
                 bg=BG, fg=FG2, font=(FONT,10)).pack(side="right")

        _div(f)

        _lbl(f, "SAVE MERGED FILE AS", secondary=True)
        of = tk.Frame(f, bg=BG); of.pack(fill="x", padx=24, pady=(0,6))
        self._mg_out = tk.StringVar()
        ttk.Entry(of, textvariable=self._mg_out,
                  state="readonly").pack(side="left", fill="x", expand=True)
        _btn(of, "Browse", self._mg_pick_out).pack(side="left", padx=(8,0))

        _div(f)

        af = tk.Frame(f, bg=BG); af.pack(pady=(2,0))
        self._mg_btn = _btn(af, "Merge PDFs", self._mg_run, primary=True)
        self._mg_btn.pack()
        self._mg_prog = ProgBar(f); self._mg_prog.pack(fill="x")

    def _mg_renum(self):
        for i,iid in enumerate(self._mg_tv.get_children()):
            self._mg_tv.set(iid,"num",i+1)
        n = len(self._mg_paths)
        self._mg_count_var.set(f"{n} file{'s' if n!=1 else ''} queued" if n else "")

    def _mg_add(self):
        paths = filedialog.askopenfilenames(title="Add PDFs to merge",
            filetypes=[("PDF","*.pdf"),("All files","*.*")])
        if not paths: return
        if not self._mg_out.get():
            self._mg_out.set(os.path.join(os.path.dirname(paths[0]),"merged.pdf"))
        def _load():
            items = []
            for p in paths:
                try: items.append((p,os.path.basename(p),*pdf_info(p)))
                except Exception: pass
            self.after(0, self._mg_insert, items)
        threading.Thread(target=_load, daemon=True).start()

    def _mg_insert(self, items):
        for path,name,pages,size in items:
            self._mg_paths.append(path)
            self._mg_tv.insert("","end",values=(len(self._mg_paths),name,pages,size))
        self._mg_renum()

    def _mg_del(self):
        sel = self._mg_tv.selection()
        if not sel: return
        idx = self._mg_tv.index(sel[0])
        self._mg_tv.delete(sel[0]); self._mg_paths.pop(idx); self._mg_renum()

    def _mg_up(self):
        sel = self._mg_tv.selection()
        if not sel: return
        iid=sel[0]; idx=self._mg_tv.index(iid)
        if idx==0: return
        self._mg_tv.move(iid,"",idx-1)
        self._mg_paths.insert(idx-1,self._mg_paths.pop(idx))
        self._mg_renum(); self._mg_tv.selection_set(iid)

    def _mg_dn(self):
        sel = self._mg_tv.selection()
        if not sel: return
        iid=sel[0]; idx=self._mg_tv.index(iid)
        if idx>=len(self._mg_paths)-1: return
        self._mg_tv.move(iid,"",idx+1)
        self._mg_paths.insert(idx+1,self._mg_paths.pop(idx))
        self._mg_renum(); self._mg_tv.selection_set(iid)

    def _mg_clear(self):
        self._mg_tv.delete(*self._mg_tv.get_children())
        self._mg_paths.clear(); self._mg_renum(); self._mg_prog.reset()

    def _mg_pick_out(self):
        p = filedialog.asksaveasfilename(title="Save merged PDF as",
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if p: self._mg_out.set(p)

    def _mg_run(self):
        if len(self._mg_paths)<2:
            messagebox.showwarning("Too few files","Add at least 2 PDFs."); return
        out = self._mg_out.get()
        if not out:
            messagebox.showwarning("No output","Choose where to save."); return

        self._mg_btn.configure(state="disabled", text="Merging…")
        self._mg_prog.working("Preparing…")
        self._set_busy(True); self.update()

        paths=list(self._mg_paths)
        def _cb(done,total,name): self.after(0, self._mg_prog.step, done, total, name)
        def _ok(pg):
            def _():
                self._mg_prog.done(f"Merged {len(paths)} PDFs  ({pg} pages total)", out)
                self._mg_btn.configure(state="normal", text="Merge PDFs")
                self._set_busy(False); self._sb(f"Merged → {os.path.basename(out)}")
            self.after(0,_)
        def _err(e):
            def _():
                self._mg_prog.error(str(e))
                self._mg_btn.configure(state="normal", text="Merge PDFs")
                self._set_busy(False); messagebox.showerror("Merge failed",str(e))
            self.after(0,_)

        self._run_bg(lambda: do_merge(paths,out,_cb), _ok, _err)

    # ═════════════════════════════════════════════════════════════════════════
    # EXTRACT TAB
    # ═════════════════════════════════════════════════════════════════════════

    def _extract_tab(self, f):
        self._ex_path = ""

        self._ex_zone = DropZone(f, "Choose a PDF to extract text from",
            "drag & drop  ·  or click to browse",
            on_click=self._ex_pick, on_drop=self._ex_drop)
        self._ex_zone.pack(fill="x", padx=20, pady=(20,0))
        self._ex_info = tk.Label(f, text="", bg=BG, fg=FG2, font=(FONT,10))

        _div(f)

        _lbl(f, "PAGE RANGE", secondary=True)
        pr = tk.Frame(f, bg=BG); pr.pack(anchor="w", padx=24)
        tk.Label(pr, text="From", bg=BG, fg=FG, font=(FONT,11)).pack(side="left", padx=(0,8))
        self._ex_from = Stepper(pr, from_=1, to=9999, initial=1)
        self._ex_from.pack(side="left")
        tk.Label(pr, text="To", bg=BG, fg=FG, font=(FONT,11)).pack(side="left", padx=(16,8))
        self._ex_to = Stepper(pr, from_=1, to=9999, initial=9999)
        self._ex_to.pack(side="left")
        tk.Label(pr, text="  (max = all pages)", bg=BG, fg=FG2,
                 font=(FONT,9)).pack(side="left", padx=(8,0))

        _div(f)

        af = tk.Frame(f, bg=BG); af.pack(pady=(2,0))
        self._ex_btn = _btn(af, "Extract Text", self._ex_run, primary=True)
        self._ex_btn.pack()
        self._ex_status = tk.StringVar()
        tk.Label(af, textvariable=self._ex_status,
                 bg=BG, fg=GREEN, font=(FONT,10)).pack(pady=(4,0))

        _div(f)

        _lbl(f, "EXTRACTED TEXT", secondary=True)
        sf = tk.Frame(f, bg=BG); sf.pack(fill="x", padx=24, pady=(0,8))
        tk.Label(sf, text="Find", bg=BG, fg=FG2, font=(FONT,10)).pack(side="left")
        self._find_var = tk.StringVar()
        self._find_var.trace_add("write", lambda *_: self._find_do())
        ttk.Entry(sf, textvariable=self._find_var, width=26
                  ).pack(side="left", padx=(8,0))
        _btn(sf, "Prev", lambda: self._find_step(-1)).pack(side="left", padx=(8,2))
        _btn(sf, "Next", lambda: self._find_step(1)).pack(side="left")
        self._find_cnt = tk.StringVar()
        tk.Label(sf, textvariable=self._find_cnt,
                 bg=BG, fg=FG2, font=(FONT,10)).pack(side="left", padx=10)

        tw = tk.Frame(f, bg=BG)
        tw.pack(fill="both", expand=True, padx=20, pady=(0,4))
        self._txt = tk.Text(tw, bg=CARD, fg=FG,
                            font=("Menlo",10), relief="flat", bd=0,
                            padx=12, pady=10, wrap="word", state="disabled",
                            selectbackground=ACCENT, selectforeground=FG,
                            insertbackground=FG)
        self._txt.tag_configure("match", background="#E8A87C", foreground="#111111")
        self._txt.tag_configure("cur",   background=ACCENT,   foreground="#ffffff")
        vsb = ttk.Scrollbar(tw, orient="vertical", command=self._txt.yview)
        self._txt.configure(yscrollcommand=vsb.set)
        self._txt.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        ab = tk.Frame(f, bg=BG); ab.pack(fill="x", padx=24, pady=(4,12))
        _btn(ab, "Copy All", self._ex_copy).pack(side="left")
        _btn(ab, "Save as TXT", self._ex_save).pack(side="left", padx=8)
        self._ex_copy_lbl = tk.StringVar()
        tk.Label(ab, textvariable=self._ex_copy_lbl,
                 bg=BG, fg=GREEN, font=(FONT,10)).pack(side="left")

        self._fhits: list[tuple[str,str]] = []; self._fidx = 0

    def _ex_load(self, path):
        self._ex_path = path
        try:
            pages,sz = pdf_info(path)
            self._ex_info.configure(
                text=f"  {os.path.basename(path)}   ·   {pages} pages   ·   {sz}")
            self._ex_info.pack(anchor="w", padx=24, pady=(6,0))
            self._ex_zone.set(os.path.basename(path), "Click to choose a different file")
            self._ex_from.set(1); self._ex_to.set(pages)
            self._ex_status.set("")
            self._sb(f"Loaded  {os.path.basename(path)}  ({pages} pages)")
        except Exception as e:
            messagebox.showerror("Error",str(e))

    def _ex_pick(self):
        p = filedialog.askopenfilename(title="Select PDF",
            filetypes=[("PDF","*.pdf"),("All files","*.*")])
        if p: self._ex_load(p)

    def _ex_drop(self, e):
        p = e.data.strip().strip("{}")
        if p.lower().endswith(".pdf"): self._ex_load(p)

    def _ex_run(self):
        if not self._ex_path:
            messagebox.showwarning("No file","Choose a PDF first."); return
        try:
            total = len(PdfReader(self._ex_path).pages)
        except Exception as e:
            messagebox.showerror("Error",str(e)); return

        frm = max(1, self._ex_from.get()) - 1
        to  = min(total, self._ex_to.get())

        self._ex_btn.configure(state="disabled", text="Extracting…")
        self._ex_status.set("Working…")
        self._set_busy(True)
        self._txt.configure(state="normal"); self._txt.delete("1.0","end")
        self._txt.configure(state="disabled")
        self._find_var.set(""); self._fhits.clear(); self._find_cnt.set("")
        self.update()

        path = self._ex_path
        def _stream():
            found = False
            for pnum,text in do_extract(path,frm,to):
                s = text.strip(); found = found or bool(s)
                self.after(0,self._txt_add,f"Page {pnum}\n{'─'*44}\n{s}\n\n")
            if not found:
                self.after(0,self._txt_add,"(No selectable text — PDF may be scanned/image-based)")
            self.after(0,self._ex_done)
        threading.Thread(target=_stream, daemon=True).start()

    def _txt_add(self, chunk):
        self._txt.configure(state="normal")
        self._txt.insert("end",chunk); self._txt.see("end")
        self._txt.configure(state="disabled")

    def _ex_done(self):
        self._ex_btn.configure(state="normal", text="Extract Text")
        self._ex_status.set("Done"); self._set_busy(False)
        self._sb("Extraction complete")
        self.after(2500, lambda: self._ex_status.set(""))

    def _find_do(self):
        q=self._find_var.get(); w=self._txt
        w.tag_remove("match","1.0","end"); w.tag_remove("cur","1.0","end")
        self._fhits.clear(); self._fidx=0
        if not q: self._find_cnt.set(""); return
        pos="1.0"
        while True:
            idx=w.search(q,pos,nocase=True,stopindex="end")
            if not idx: break
            end=f"{idx}+{len(q)}c"; w.tag_add("match",idx,end)
            self._fhits.append((idx,end)); pos=end
        n=len(self._fhits)
        self._find_cnt.set(f"{n} match{'es' if n!=1 else ''}")
        if n: self._find_step(0)

    def _find_step(self, d):
        if not self._fhits: return
        w=self._txt; s,e=self._fhits[self._fidx]
        w.tag_remove("cur",s,e); w.tag_add("match",s,e)
        self._fidx=(self._fidx+d)%len(self._fhits)
        s,e=self._fhits[self._fidx]
        w.tag_remove("match",s,e); w.tag_add("cur",s,e); w.see(s)
        self._find_cnt.set(f"{self._fidx+1}/{len(self._fhits)}")

    def _ex_copy(self):
        t=self._txt.get("1.0","end").strip()
        if not t: messagebox.showwarning("Empty","Nothing to copy yet."); return
        self.clipboard_clear(); self.clipboard_append(t)
        self._ex_copy_lbl.set("Copied to clipboard")
        self.after(2000,lambda: self._ex_copy_lbl.set(""))

    def _ex_save(self):
        t=self._txt.get("1.0","end").strip()
        if not t: messagebox.showwarning("Empty","Nothing to save yet."); return
        p=filedialog.asksaveasfilename(title="Save text",
            defaultextension=".txt",filetypes=[("Text","*.txt"),("All","*.*")])
        if not p: return
        with open(p,"w",encoding="utf-8") as f: f.write(t)
        self._ex_copy_lbl.set(f"Saved  {os.path.basename(p)}")
        self.after(2500,lambda: self._ex_copy_lbl.set(""))

    # ═════════════════════════════════════════════════════════════════════════
    # VECTOR DB TAB
    # ═════════════════════════════════════════════════════════════════════════

    def _vectordb_tab(self, f):
        self._vdb_paths: list[str] = []

        about = tk.Frame(f, bg=CARD); about.pack(fill="x", padx=20, pady=(20,0))
        tk.Label(about, text="Build a Vector Database from PDFs",
                 bg=CARD, fg=FG, font=(FONT,12,"bold")).pack(anchor="w", padx=16, pady=(12,2))
        tk.Label(about,
            text=("Splits each PDF into text chunks, generates semantic embeddings "
                  "(all-MiniLM-L6-v2), and saves a persistent ChromaDB store "
                  "queryable by any LLM.   First run downloads the model (~80 MB)."),
            bg=CARD, fg=FG2, font=(FONT,10), wraplength=640, justify="left"
            ).pack(anchor="w", padx=16, pady=(0,12))

        _div(f)

        _lbl(f, "PDFS TO INDEX", secondary=True)
        tv_f = tk.Frame(f, bg=CARD); tv_f.pack(fill="x", padx=20)
        vcols = ("name","pages","size")
        self._vdb_tv = ttk.Treeview(tv_f, columns=vcols, show="headings",
                                     height=5, selectmode="browse")
        for col,lbl,w,a in [("name","Filename",360,"w"),
                              ("pages","Pages",74,"center"),("size","Size",90,"e")]:
            self._vdb_tv.heading(col,text=lbl,anchor=a)
            self._vdb_tv.column(col,width=w,anchor=a,stretch=(col=="name"))
        vvsb = ttk.Scrollbar(tv_f, orient="vertical", command=self._vdb_tv.yview)
        self._vdb_tv.configure(yscrollcommand=vvsb.set)
        self._vdb_tv.pack(side="left",fill="both",expand=True)
        vvsb.pack(side="right",fill="y")

        vf = tk.Frame(f, bg=BG); vf.pack(fill="x", padx=20, pady=(8,0))
        for t,cmd in [("Add PDFs",self._vdb_add),("Remove",self._vdb_del),
                       ("Clear",self._vdb_clear)]:
            _btn(vf, t, cmd).pack(side="left", padx=(0,6))

        _div(f)

        _lbl(f, "SETTINGS", secondary=True)
        sg = tk.Frame(f, bg=BG); sg.pack(fill="x", padx=24, pady=(0,8))

        r1 = tk.Frame(sg, bg=BG); r1.pack(fill="x")

        c1 = tk.Frame(r1, bg=BG); c1.pack(side="left", padx=(0,32))
        tk.Label(c1, text="COLLECTION NAME", bg=BG, fg=FG2,
                 font=(FONT,9,"bold")).pack(anchor="w", pady=(0,6))
        self._vdb_coll = tk.StringVar(value="my_documents")
        ttk.Entry(c1, textvariable=self._vdb_coll, width=22).pack(anchor="w")

        c2 = tk.Frame(r1, bg=BG); c2.pack(side="left", padx=(0,32))
        tk.Label(c2, text="CHUNK SIZE (chars)", bg=BG, fg=FG2,
                 font=(FONT,9,"bold")).pack(anchor="w", pady=(0,6))
        self._vdb_chunk_var = Stepper(c2, from_=100, to=4000, initial=800, step=100, width=5)
        self._vdb_chunk_var.pack(anchor="w")

        c3 = tk.Frame(r1, bg=BG); c3.pack(side="left")
        tk.Label(c3, text="OVERLAP (chars)", bg=BG, fg=FG2,
                 font=(FONT,9,"bold")).pack(anchor="w", pady=(0,6))
        self._vdb_overlap_var = Stepper(c3, from_=0, to=500, initial=100, step=25, width=5)
        self._vdb_overlap_var.pack(anchor="w")

        r2 = tk.Frame(sg, bg=BG); r2.pack(fill="x", pady=(18,0))
        tk.Label(r2, text="OUTPUT FOLDER", bg=BG, fg=FG2,
                 font=(FONT,9,"bold")).pack(anchor="w", pady=(0,6))
        ofr = tk.Frame(r2, bg=BG); ofr.pack(fill="x")
        self._vdb_outdir = tk.StringVar()
        ttk.Entry(ofr, textvariable=self._vdb_outdir,
                  state="readonly").pack(side="left", fill="x", expand=True)
        _btn(ofr, "Browse", self._vdb_browse).pack(side="left", padx=(8,0))

        _div(f)

        af = tk.Frame(f, bg=BG); af.pack(pady=(2,0))
        self._vdb_btn = _btn(af, "Build Vector DB", self._vdb_run, primary=True)
        self._vdb_btn.pack()
        self._vdb_prog = ProgBar(f); self._vdb_prog.pack(fill="x")

        self._snip_frame = tk.Frame(f, bg=BG)
        tk.Label(self._snip_frame, text="USAGE SNIPPET",
                 bg=BG, fg=FG2, font=(FONT,9,"bold")).pack(anchor="w", padx=24, pady=(6,4))
        self._snip_txt = tk.Text(self._snip_frame,
            bg=CARD, fg=FG, font=("Menlo",9), height=10,
            relief="flat", bd=0, padx=14, pady=10, state="disabled")
        self._snip_txt.pack(fill="x", padx=20, pady=(0,14))

    def _vdb_add(self):
        paths = filedialog.askopenfilenames(title="Add PDFs to index",
            filetypes=[("PDF","*.pdf"),("All files","*.*")])
        if not paths: return
        if not self._vdb_outdir.get():
            self._vdb_outdir.set(os.path.join(os.path.dirname(paths[0]),"chroma_db"))
        def _load():
            items = []
            for p in paths:
                try: items.append((p,os.path.basename(p),*pdf_info(p)))
                except Exception: pass
            self.after(0,self._vdb_insert,items)
        threading.Thread(target=_load,daemon=True).start()

    def _vdb_insert(self, items):
        for path,name,pages,size in items:
            if path not in self._vdb_paths:
                self._vdb_paths.append(path)
                self._vdb_tv.insert("","end",values=(name,pages,size))

    def _vdb_del(self):
        sel=self._vdb_tv.selection()
        if not sel: return
        idx=self._vdb_tv.index(sel[0])
        self._vdb_tv.delete(sel[0]); self._vdb_paths.pop(idx)

    def _vdb_clear(self):
        self._vdb_tv.delete(*self._vdb_tv.get_children())
        self._vdb_paths.clear(); self._vdb_prog.reset()

    def _vdb_browse(self):
        d=filedialog.askdirectory(title="Vector DB output folder")
        if d: self._vdb_outdir.set(d)

    def _vdb_run(self):
        if not self._vdb_paths:
            messagebox.showwarning("No files","Add at least one PDF."); return
        outdir=self._vdb_outdir.get()
        if not outdir:
            messagebox.showwarning("No folder","Choose where to save the DB."); return

        self._vdb_btn.configure(state="disabled", text="Building…")
        self._vdb_prog.working("Initializing…")
        self._set_busy(True); self.update()

        paths=list(self._vdb_paths); coll=self._vdb_coll.get().strip() or "my_documents"
        csz=self._vdb_chunk_var.get(); ov=self._vdb_overlap_var.get()

        def _cb(fi,ft,fname,pi,pt):
            detail=f"File {fi+1}/{ft}  —  {fname}  page {pi}/{pt}"
            self.after(0,self._vdb_prog.step,fi*pt+pi,max(ft*pt,1),detail)

        def _ok(res):
            n_chunks,coll_name=res
            snippet=textwrap.dedent(f"""\
                import chromadb

                # Connect to the vector store
                client     = chromadb.PersistentClient(path="{outdir}")
                collection = client.get_collection("{coll_name}")

                # Semantic search — returns top-5 most relevant chunks
                results = collection.query(
                    query_texts=["your question here"],
                    n_results=5
                )

                # Access results
                chunks    = results["documents"][0]   # list of text chunks
                sources   = results["metadatas"][0]   # source file + page number
                distances = results["distances"][0]   # similarity scores

                # Pass chunks to an LLM as context (RAG)
                context = "\\n\\n".join(chunks)
                prompt  = f"Answer based on this context:\\n{{context}}\\n\\nQuestion: ..."
            """)
            def _():
                self._vdb_prog.done(f"{n_chunks} chunks indexed and saved", outdir)
                self._vdb_btn.configure(state="normal", text="Build Vector DB")
                self._set_busy(False)
                self._sb(f"Vector DB ready — {n_chunks} chunks in '{coll_name}'")
                self._show_snippet(snippet)
            self.after(0,_)

        def _err(e):
            def _():
                self._vdb_prog.error(str(e))
                self._vdb_btn.configure(state="normal", text="Build Vector DB")
                self._set_busy(False); messagebox.showerror("Failed",str(e))
            self.after(0,_)

        self._run_bg(lambda: do_vectordb(paths,outdir,coll,csz,ov,_cb),_ok,_err)

    def _show_snippet(self, code):
        self._snip_frame.pack(fill="x")
        self._snip_txt.configure(state="normal")
        self._snip_txt.delete("1.0","end")
        self._snip_txt.insert("end", code)
        self._snip_txt.configure(state="disabled")


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().mainloop()
