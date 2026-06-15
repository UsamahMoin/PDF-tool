#!/usr/bin/env python3
"""PDF Tool — Split · Merge · Extract · Vector DB · Rearrange · Compress · Scan  (PyQt6)"""

import os, math, threading, subprocess, textwrap, sys, shutil, time
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

try:
    import cv2
    import numpy as np
    _CV2 = True
except ImportError:
    _CV2 = False

try:
    from PIL import Image as PilImage
    _PIL = True
except ImportError:
    _PIL = False

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QProgressBar, QFileDialog, QMessageBox,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QSizePolicy, QStatusBar, QAbstractItemView,
    QScrollArea, QRadioButton, QButtonGroup, QSplitter,
    QListWidget, QListWidgetItem, QComboBox, QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QMimeData, QUrl, QRectF, QPointF, QSize, QObject
from PyQt6.QtGui import (QFont, QTextCursor, QDragEnterEvent, QDropEvent,
                          QPainter, QPen, QBrush, QPolygonF, QPixmap, QColor,
                          QIcon, QCursor)

# ── Color tokens ───────────────────────────────────────────────────────────────
BG     = "#0F0F0F"
CARD   = "#1A1A1A"
CARD2  = "#252525"
BORDER = "#333333"
FG     = "#EBE5DC"
FG2    = "#7A7572"
ACCENT = "#CF5F2A"
A_HOV  = "#DC6D38"
GREEN  = "#4EB87D"
RED    = "#D94040"

QSS = f"""
* {{
    font-family: "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
}}
QMainWindow, QWidget {{
    background: {BG};
    color: {FG};
}}
/* ── Tabs ──────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {BORDER};
    background: {BG};
}}
QTabBar {{
    background: {BG};
    border: none;
}}
QTabBar::tab {{
    background: {BG};
    color: {FG2};
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 11pt;
    margin: 0;
}}
QTabBar::tab:selected {{
    color: {FG};
    font-weight: bold;
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    color: {FG};
}}
/* ── Buttons ───────────────────────────────────────────────────────── */
QPushButton {{
    background: {CARD2};
    color: {FG};
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    font-size: 10pt;
}}
QPushButton:hover  {{ background: {BORDER}; }}
QPushButton:pressed {{ background: {BORDER}; }}
QPushButton:disabled {{ background: {CARD}; color: {FG2}; }}

QPushButton[cls="primary"] {{
    background: {ACCENT};
    color: white;
    font-size: 12pt;
    font-weight: bold;
    padding: 11px 40px;
    border-radius: 6px;
    min-width: 160px;
}}
QPushButton[cls="primary"]:hover   {{ background: {A_HOV}; }}
QPushButton[cls="primary"]:pressed {{ background: {A_HOV}; }}
QPushButton[cls="primary"]:disabled {{ background: {CARD2}; color: {FG2}; }}

QPushButton[cls="stepper"] {{
    background: {CARD2};
    color: {FG};
    font-size: 15pt;
    font-weight: bold;
    padding: 2px 10px;
    border-radius: 4px;
    min-width: 36px;
    max-width: 36px;
    min-height: 34px;
    max-height: 34px;
}}
QPushButton[cls="stepper"]:hover  {{ background: {BORDER}; }}

/* ── Inputs ────────────────────────────────────────────────────────── */
QLineEdit {{
    background: {CARD};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 10px;
    font-size: 11pt;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit:read-only {{ color: {FG2}; }}

QTextEdit {{
    background: {CARD};
    color: {FG};
    border: none;
    border-radius: 4px;
    padding: 6px;
    font-family: "Menlo", "Monaco", "Courier New", monospace;
    font-size: 10pt;
    selection-background-color: {ACCENT};
}}

/* ── Progress bar ──────────────────────────────────────────────────── */
QProgressBar {{
    background: {CARD2};
    border: none;
    border-radius: 2px;
    max-height: 4px;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 2px;
}}

/* ── Tables ────────────────────────────────────────────────────────── */
QTableWidget {{
    background: {CARD};
    color: {FG};
    border: none;
    border-radius: 4px;
    gridline-color: {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: none;
}}
QTableWidget::item {{ padding: 5px 8px; border: none; }}
QTableWidget::item:selected {{ background: {ACCENT}; }}
QHeaderView::section {{
    background: {CARD2};
    color: {FG2};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
    font-size: 9pt;
    font-weight: bold;
}}
QTableCornerButton::section {{ background: {CARD2}; border: none; }}

/* ── Scrollbars ────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {CARD};
    width: 8px;
    border: none;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {CARD};
    height: 8px;
    border: none;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Radio buttons ─────────────────────────────────────────────────── */
QRadioButton {{
    color: {FG};
    spacing: 8px;
    font-size: 11pt;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid {BORDER};
    background: {CARD};
}}
QRadioButton::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QRadioButton::indicator:hover {{ border-color: {ACCENT}; }}

/* ── Status bar ────────────────────────────────────────────────────── */
QStatusBar {{
    background: {CARD};
    color: {FG2};
    font-size: 9pt;
    border-top: 1px solid {BORDER};
    padding: 2px 12px;
}}

/* ── Misc ──────────────────────────────────────────────────────────── */
QFrame[cls="divider"] {{
    background: {BORDER};
    max-height: 1px;
    min-height: 1px;
}}
QLabel[cls="section"] {{
    color: {FG2};
    font-size: 9pt;
    font-weight: bold;
}}
QLabel[cls="info"] {{
    color: {FG2};
    font-size: 10pt;
}}
QLabel[cls="status-ok"]  {{ color: {GREEN}; font-size: 10pt; }}
QLabel[cls="status-err"] {{ color: {RED};   font-size: 10pt; }}
"""

# ── Utility ────────────────────────────────────────────────────────────────────

def fmt_size(path):
    b = os.path.getsize(path)
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024

def stem(path):  return os.path.splitext(os.path.basename(path))[0]
def reveal(path): subprocess.call(["open", path if os.path.isdir(path) else os.path.dirname(path)])

def parse_spec(spec, total):
    pages = set()
    for p in spec.replace(" ", "").split(","):
        if not p: continue
        try:
            if "-" in p:
                a, b = p.split("-", 1); pages.update(range(int(a)-1, int(b)))
            else: pages.add(int(p)-1)
        except ValueError: pass
    return sorted(x for x in pages if 0 <= x < total)

def pdf_info(path): return len(PdfReader(path).pages), fmt_size(path)

def chunk_text(text, size, overlap):
    out, s = [], 0
    while s < len(text):
        out.append(text[s:s+size]); s += size-overlap
    return [c for c in out if c.strip()]

# ── PDF workers ────────────────────────────────────────────────────────────────

def do_split(src, outdir, mode, value, spec, cb):
    r = PdfReader(src); total = len(r.pages); name = stem(src); out = []
    if mode == "custom":
        idx = parse_spec(spec, total)
        if not idx: raise ValueError("No valid pages in custom spec.")
        w = PdfWriter()
        for i in idx: w.add_page(r.pages[i])
        fn = f"{name}_custom_{len(idx)}pages.pdf"; p = os.path.join(outdir, fn)
        with open(p, "wb") as f: w.write(f)
        out.append(p); cb(1, 1, fn)
    else:
        cs = value if mode == "pages" else math.ceil(total/value)
        nc = math.ceil(total/cs); s = n = 0
        while s < total:
            n += 1; e = min(s+cs, total); w = PdfWriter(); w.append(r, pages=range(s, e))
            fn = f"{name}_part{n:03d}_p{s+1}-{e}.pdf"; p = os.path.join(outdir, fn)
            with open(p, "wb") as f: w.write(f)
            out.append(p); cb(n, nc, fn); s = e
    return out

LETTER_PORTRAIT = (612.0, 792.0)
LETTER_LANDSCAPE = (792.0, 612.0)


def _smart_letter_transform(page):
    """Return target size, transform, and fitting mode for one PDF page."""
    if page.rotation:
        page.transfer_rotation_to_content()

    # Match what PDF viewers display; scanned files commonly use a crop box
    # smaller than their underlying media box.
    visible_box = page.cropbox
    left = float(visible_box.left)
    bottom = float(visible_box.bottom)
    width = float(visible_box.width)
    height = float(visible_box.height)
    if width <= 0 or height <= 0:
        raise ValueError("PDF contains a page with invalid dimensions.")

    target_width, target_height = (
        LETTER_LANDSCAPE if width > height else LETTER_PORTRAIT
    )
    width_delta = abs(width - target_width) / target_width
    height_delta = abs(height - target_height) / target_height

    if width_delta <= 0.001 and height_delta <= 0.001:
        scale_x = target_width / width
        scale_y = target_height / height
        mode = "unchanged"
    elif width_delta <= 0.05 and height_delta <= 0.05:
        # Small enough difference to fill Letter without noticeable distortion.
        scale_x = target_width / width
        scale_y = target_height / height
        mode = "stretched"
    elif width > target_width or height > target_height:
        # Large pages fit proportionally; any remaining area becomes a margin.
        scale_x = scale_y = min(target_width / width, target_height / height)
        mode = "scaled down"
    else:
        # Small pages grow at most 10%, then retain centered margins.
        scale_x = scale_y = min(
            target_width / width,
            target_height / height,
            1.10,
        )
        mode = "scaled up"

    rendered_width = width * scale_x
    rendered_height = height * scale_y
    offset_x = (target_width - rendered_width) / 2
    offset_y = (target_height - rendered_height) / 2
    transform = (
        Transformation()
        .translate(-left, -bottom)
        .scale(scale_x, scale_y)
        .translate(offset_x, offset_y)
    )
    return target_width, target_height, transform, mode


def _smart_letter_page(page):
    target_width, target_height, transform, mode = _smart_letter_transform(page)
    normalized = PageObject.create_blank_page(
        width=target_width,
        height=target_height,
    )
    normalized.merge_transformed_page(page, transform, expand=False)
    return normalized, mode


def do_merge(paths, output, cb, smart_letter=False):
    w = PdfWriter(); total = 0
    fit_counts = {
        "unchanged": 0,
        "stretched": 0,
        "scaled down": 0,
        "scaled up": 0,
    }
    for i, p in enumerate(paths):
        rr = PdfReader(p)
        for page in rr.pages:
            if smart_letter:
                page, mode = _smart_letter_page(page)
                fit_counts[mode] += 1
            w.add_page(page)
            total += 1
        cb(i+1, len(paths), os.path.basename(p))
    with open(output, "wb") as f: w.write(f)
    return total, fit_counts

def do_extract(path, start, end):
    r = PdfReader(path)
    for i in range(start, end): yield i+1, (r.pages[i].extract_text() or "")

def do_vectordb(pdf_paths, outdir, coll, chunk_sz, overlap, cb):
    import chromadb
    os.makedirs(outdir, exist_ok=True)
    client = chromadb.PersistentClient(path=outdir)
    try: client.delete_collection(coll)
    except Exception: pass
    col = client.create_collection(name=coll, metadata={"hnsw:space": "cosine"})
    ids, docs, metas = [], [], []
    for fi, path in enumerate(pdf_paths):
        r = PdfReader(path); np = len(r.pages); fn = os.path.basename(path)
        for pi, page in enumerate(r.pages):
            cb(fi, len(pdf_paths), fn, pi+1, np)
            for ci, chunk in enumerate(chunk_text(page.extract_text() or "", chunk_sz, overlap)):
                ids.append(f"{stem(path)}_p{pi+1}_c{ci}")
                docs.append(chunk)
                metas.append({"source": fn, "page": pi+1, "chunk": ci})
    for i in range(0, len(ids), 100):
        col.upsert(ids=ids[i:i+100], documents=docs[i:i+100], metadatas=metas[i:i+100])
    return len(ids), coll

def do_rearrange(src, outdir, order):
    """Write a new PDF with pages in the given order (0-based indices)."""
    r = PdfReader(src); w = PdfWriter()
    for i in order: w.add_page(r.pages[i])
    fn = f"{stem(src)}_rearranged.pdf"
    p  = os.path.join(outdir, fn)
    with open(p, "wb") as f: w.write(f)
    return p

class CompressionCancelled(Exception):
    pass


def _remove_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _check_compression_cancelled(cancel_event):
    if cancel_event and cancel_event.is_set():
        raise CompressionCancelled("Compression cancelled.")


class _CancellableOutput:
    def __init__(self, handle, cancel_event):
        self._handle = handle
        self._cancel_event = cancel_event

    def write(self, data):
        _check_compression_cancelled(self._cancel_event)
        return self._handle.write(data)

    def __getattr__(self, name):
        return getattr(self._handle, name)


def _prepare_compressed_image(image, max_edge):
    """Return a JPEG-friendly, optionally downsampled Pillow image."""
    image = image.copy()
    image.load()
    if max(image.size) > max_edge:
        image.thumbnail((max_edge, max_edge), PilImage.Resampling.LANCZOS)

    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = PilImage.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    if image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image


def _compress_images_with_pypdf(src, partial, level, cb, cancel_event):
    if not _PIL:
        raise RuntimeError(
            "Pillow is required when Ghostscript is unavailable. "
            "Install it with: pip install Pillow"
        )

    settings = {
        "Screen (smallest)": (900, 45),
        "eBook": (1800, 65),
        "Print": (3500, 82),
        "Prepress (largest)": (4800, 92),
    }
    max_edge, quality = settings.get(level, settings["eBook"])

    writer = PdfWriter()
    writer.append(PdfReader(src))
    total = len(writer.pages)
    replaced = 0
    seen_refs = set()

    for page_index, page in enumerate(writer.pages):
        _check_compression_cancelled(cancel_event)
        for image_file in list(page.images):
            _check_compression_cancelled(cancel_event)
            ref = image_file.indirect_reference
            if ref is None:
                continue
            ref_key = (ref.idnum, ref.generation)
            if ref_key in seen_refs:
                continue
            seen_refs.add(ref_key)

            try:
                image = image_file.image
                if image.width * image.height < 160_000:
                    continue
                compressed = _prepare_compressed_image(image, max_edge)
                image_file.replace(compressed, quality=quality, optimize=True)
                replaced += 1
            except (OSError, TypeError, ValueError):
                # Unsupported and inline image encodings remain unchanged.
                continue

        page.compress_content_streams()
        cb(page_index + 1, total, f"Recompressing page {page_index + 1}/{total}")

    _check_compression_cancelled(cancel_event)
    writer.compress_identical_objects()
    with open(partial, "wb") as handle:
        writer.write(_CancellableOutput(handle, cancel_event))
    _check_compression_cancelled(cancel_event)
    return replaced


def do_compress(src, out, level, cb, cancel_event=None, process_control=None):
    """Compress to a partial file, then atomically publish only on success."""
    if os.path.realpath(src) == os.path.realpath(out):
        raise ValueError("Choose an output file different from the source PDF.")

    partial = out + ".part"
    _remove_file(partial)
    control = process_control if process_control is not None else {}
    original_size = os.path.getsize(src)

    try:
        _check_compression_cancelled(cancel_event)
        gs_cmd = next(
            (cmd for cmd in ("gs", "gswin64c", "gswin32c") if shutil.which(cmd)),
            None,
        )
        if gs_cmd:
            cb(0, 0, "Compressing with Ghostscript…")
            gs_map = {
                "Screen (smallest)": "/screen",
                "eBook": "/ebook",
                "Print": "/printer",
                "Prepress (largest)": "/prepress",
            }
            process = subprocess.Popen(
                [gs_cmd, "-dBATCH", "-dNOPAUSE", "-dQUIET",
                 "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS={gs_map.get(level, '/ebook')}",
                 f"-sOutputFile={partial}", src],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            control["process"] = process
            started = time.monotonic()
            while process.poll() is None:
                if cancel_event and cancel_event.wait(0.1):
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise CompressionCancelled("Compression cancelled.")
                if time.monotonic() - started > 300:
                    process.kill()
                    raise RuntimeError("Ghostscript compression timed out.")
            control["process"] = None

            if (process.returncode == 0 and os.path.exists(partial)
                    and os.path.getsize(partial) < original_size):
                _check_compression_cancelled(cancel_event)
                os.replace(partial, out)
                return out, "Ghostscript"
            _remove_file(partial)

        cb(0, 0, "Recompressing embedded images…")
        replaced = _compress_images_with_pypdf(
            src, partial, level, cb, cancel_event
        )
        if os.path.getsize(partial) >= original_size:
            raise RuntimeError(
                "This PDF could not be made smaller with the selected level. "
                "Try a stronger level or install Ghostscript."
            )

        _check_compression_cancelled(cancel_event)
        os.replace(partial, out)
        return out, f"Pillow image recompression ({replaced} images)"
    finally:
        control["process"] = None
        _remove_file(partial)

def do_scan_pages_to_pdf(pages, out_path, output_size, grayscale, cb):
    """
    pages: list of (image_path, [(x,y) * 4]) — corners in IMAGE-pixel coords,
                                              order TL, TR, BR, BL.
    output_size: "Auto" | "A4" | "Letter"
    """
    if not _CV2:
        raise RuntimeError("Install opencv-python:  pip install opencv-python")
    if not _PIL:
        raise RuntimeError("Install Pillow:  pip install Pillow")

    pil_pages = []
    for i, (path, corners) in enumerate(pages):
        cb(i+1, len(pages), os.path.basename(path))

        # numpy 2.x compat: use np.asarray rather than passing tuples to np.float32
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Cannot load image: {path}")

        src = np.asarray(corners, dtype=np.float32)         # shape (4, 2)
        if src.shape != (4, 2):
            raise ValueError(f"Bad corner data for {os.path.basename(path)}")

        if output_size == "A4":
            ow, oh = 1240, 1754                             # ~150 dpi
        elif output_size == "Letter":
            ow, oh = 1275, 1650
        else:                                               # Auto
            tl, tr, br, bl = src
            w = max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl))
            h = max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl))
            # Cap output at ~3000 px on the long side to keep things fast
            ow, oh = max(2, int(round(w))), max(2, int(round(h)))
            cap = 3000
            if max(ow, oh) > cap:
                s = cap / max(ow, oh)
                ow, oh = max(2, int(ow*s)), max(2, int(oh*s))

        dst = np.array([[0, 0], [ow-1, 0], [ow-1, oh-1], [0, oh-1]], dtype=np.float32)

        M      = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(img, M, (ow, oh))

        if grayscale:
            warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            pil_img = PilImage.fromarray(warped).convert("L")
        else:
            warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
            pil_img = PilImage.fromarray(warped).convert("RGB")
        pil_pages.append(pil_img)

    if not pil_pages:
        raise ValueError("No pages to convert")

    pil_pages[0].save(out_path, "PDF",
                      save_all=True,
                      append_images=pil_pages[1:],
                      resolution=150.0)
    return out_path, len(pil_pages)

# ── Shared widgets ─────────────────────────────────────────────────────────────

class DropZone(QFrame):
    """Dashed-border drop target that also responds to click."""
    clicked      = pyqtSignal()
    file_dropped = pyqtSignal(str)

    def __init__(self, label, sub, parent=None):
        super().__init__(parent)
        self._label_text = label
        self._sub_text   = sub
        self._hover      = False
        self.setAcceptDrops(True)
        self.setFixedHeight(88)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(5)
        lay.setContentsMargins(16, 12, 16, 12)

        self._top = QLabel(label)
        self._top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = self._top.font(); f.setBold(True); f.setPointSize(11); self._top.setFont(f)

        self._bot = QLabel(sub)
        self._bot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bot.setStyleSheet(f"font-size: 9pt;")

        lay.addWidget(self._top)
        lay.addWidget(self._bot)
        self._refresh()

    def _refresh(self):
        bc = ACCENT if self._hover else BORDER
        tc = ACCENT if self._hover else FG2
        self.setStyleSheet(f"""
            DropZone {{
                background: {CARD};
                border: 1px dashed {bc};
                border-radius: 6px;
            }}
        """)
        self._top.setStyleSheet(f"color: {FG}; background: transparent;")
        self._bot.setStyleSheet(f"color: {tc}; font-size: 9pt; background: transparent;")

    def set(self, label, sub=""):
        self._top.setText(label)
        self._bot.setText(sub or self._sub_text)

    def enterEvent(self, e):     self._hover = True;  self._refresh()
    def leaveEvent(self, e):     self._hover = False; self._refresh()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit()

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            if any(u.toLocalFile().lower().endswith(".pdf")
                   for u in e.mimeData().urls()):
                e.acceptProposedAction()
                self._hover = True; self._refresh()

    def dragLeaveEvent(self, e):
        self._hover = False; self._refresh()

    def dropEvent(self, e: QDropEvent):
        self._hover = False; self._refresh()
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith(".pdf"):
                self.file_dropped.emit(p); break


class Stepper(QWidget):
    """[ − ]  [value]  [ + ] — cleaner than spinbox arrows."""

    def __init__(self, from_=1, to=9999, initial=1, step=1, parent=None):
        super().__init__(parent)
        self._from = from_; self._to = to; self._step = step

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._dec = QPushButton("−"); self._dec.setProperty("cls", "stepper")
        self._dec.style().unpolish(self._dec); self._dec.style().polish(self._dec)
        self._dec.setCursor(Qt.CursorShape.PointingHandCursor)

        self._entry = QLineEdit(str(initial))
        self._entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._entry.setFixedWidth(64); self._entry.setFixedHeight(34)

        self._inc = QPushButton("+"); self._inc.setProperty("cls", "stepper")
        self._inc.style().unpolish(self._inc); self._inc.style().polish(self._inc)
        self._inc.setCursor(Qt.CursorShape.PointingHandCursor)

        lay.addWidget(self._dec)
        lay.addWidget(self._entry)
        lay.addWidget(self._inc)

        self._dec.clicked.connect(self._do_dec)
        self._inc.clicked.connect(self._do_inc)

    def _val(self):
        try: return int(self._entry.text())
        except: return self._from

    def _do_dec(self): self._entry.setText(str(max(self._from, self._val()-self._step)))
    def _do_inc(self): self._entry.setText(str(min(self._to,   self._val()+self._step)))
    def get(self):     return self._val()
    def set(self, v):  self._entry.setText(str(v))


class ProgBar(QWidget):
    """Label + 4-px progress bar + optional 'Open in Finder' button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 12)
        lay.setSpacing(6)

        row = QWidget(); rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)

        self._lbl = QLabel("")
        self._open_btn = QPushButton("Open in Finder")
        self._open_btn.hide()
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self._open)
        self._opath = None

        rl.addWidget(self._lbl, 1)
        rl.addWidget(self._open_btn)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100); self._bar.setValue(0)
        self._bar.setTextVisible(False); self._bar.setFixedHeight(4)

        lay.addWidget(row)
        lay.addWidget(self._bar)

    def working(self, text="Working…"):
        self._open_btn.hide()
        self._lbl.setStyleSheet(f"color: {FG2};"); self._lbl.setText(text)
        self._bar.setRange(0, 0)

    def step(self, done, total, detail=""):
        pct = int(done/total*100) if total else 0
        self._bar.setRange(0, 100); self._bar.setValue(pct)
        self._lbl.setStyleSheet(f"color: {FG2};")
        self._lbl.setText(f"{detail}    {pct}%")

    def done(self, text, path=None):
        self._bar.setRange(0, 100); self._bar.setValue(100)
        self._lbl.setStyleSheet(f"color: {GREEN};"); self._lbl.setText(text)
        if path: self._opath = path; self._open_btn.show()

    def error(self, text):
        self._bar.setRange(0, 100); self._bar.setValue(0)
        self._lbl.setStyleSheet(f"color: {RED};"); self._lbl.setText(text)

    def reset(self):
        self._open_btn.hide()
        self._bar.setRange(0, 100); self._bar.setValue(0)
        self._lbl.setText(""); self._lbl.setStyleSheet(f"color: {FG2};")

    def _open(self):
        if self._opath: reveal(self._opath)


# ── UI helpers ─────────────────────────────────────────────────────────────────

def _section(text):
    """Small all-caps muted section label."""
    lbl = QLabel(text)
    lbl.setProperty("cls", "section")
    lbl.style().unpolish(lbl); lbl.style().polish(lbl)
    return lbl

def _divider():
    """1-px horizontal rule."""
    f = QFrame(); f.setProperty("cls", "divider")
    f.style().unpolish(f); f.style().polish(f)
    return f

def _primary(text):
    btn = QPushButton(text)
    btn.setProperty("cls", "primary")
    btn.style().unpolish(btn); btn.style().polish(btn)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def _secondary(text):
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def _vspace(n=12):
    w = QWidget(); w.setFixedHeight(n); return w

def _hbox(*widgets, spacing=8):
    w = QWidget(); l = QHBoxLayout(w)
    l.setContentsMargins(0, 0, 0, 0); l.setSpacing(spacing)
    for x in widgets:
        if x is None: l.addStretch()
        elif isinstance(x, int): l.addSpacing(x)
        else: l.addWidget(x)
    return w


class ImageCropWidget(QWidget):
    """
    Shows an image with 4 draggable orange corner handles.
    Corners are stored in IMAGE-PIXEL coordinates so they survive resize
    and can be persisted / restored across page switches.
    """
    HANDLE_R = 10
    image_loaded = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.setAcceptDrops(True)
        self._pixmap:  QPixmap | None = None
        self._path:    str     | None = None
        self._corners_img: list[QPointF] = []   # IMAGE-pixel coords
        self._drag_idx = -1
        self.setMouseTracking(True)
        self._labels = ["TL", "TR", "BR", "BL"]

    # ── public ──────────────────────────────────────────────────────────────
    def load(self, path: str):
        self._path = path
        self._pixmap = QPixmap(path)
        self._reset_corners()
        self.update()

    def clear(self):
        self._pixmap = None; self._path = None
        self._corners_img = []; self.update()

    def reset_corners(self):
        self._reset_corners(); self.update()

    def image_corners_px(self) -> list[tuple[float, float]] | None:
        if len(self._corners_img) != 4 or self._pixmap is None:
            return None
        return [(p.x(), p.y()) for p in self._corners_img]

    def set_image_corners_px(self, corners_px):
        if not corners_px or len(corners_px) != 4: return
        self._corners_img = [QPointF(float(x), float(y)) for x, y in corners_px]
        self.update()

    # ── coord transforms ────────────────────────────────────────────────────
    def _img_rect(self) -> QRectF:
        if self._pixmap is None: return QRectF()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        ww, wh = self.width(), self.height()
        s = min(ww/pw, wh/ph) * 0.93
        sw, sh = pw*s, ph*s
        return QRectF((ww-sw)/2, (wh-sh)/2, sw, sh)

    def _to_widget(self, p_img: QPointF) -> QPointF:
        if self._pixmap is None: return p_img
        r = self._img_rect()
        sx = r.width()  / self._pixmap.width()
        sy = r.height() / self._pixmap.height()
        return QPointF(r.x() + p_img.x()*sx, r.y() + p_img.y()*sy)

    def _to_image(self, p_w: QPointF) -> QPointF:
        if self._pixmap is None: return p_w
        r = self._img_rect()
        if r.width() == 0 or r.height() == 0: return p_w
        sx = self._pixmap.width()  / r.width()
        sy = self._pixmap.height() / r.height()
        ix = max(0.0, min(float(self._pixmap.width()),  (p_w.x() - r.x()) * sx))
        iy = max(0.0, min(float(self._pixmap.height()), (p_w.y() - r.y()) * sy))
        return QPointF(ix, iy)

    def _reset_corners(self):
        if self._pixmap is None: self._corners_img = []; return
        w = float(self._pixmap.width())
        h = float(self._pixmap.height())
        m = min(w, h) * 0.05    # 5% inset from edges
        self._corners_img = [
            QPointF(m,    m),
            QPointF(w-m,  m),
            QPointF(w-m,  h-m),
            QPointF(m,    h-m),
        ]

    # ── paint ───────────────────────────────────────────────────────────────
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(CARD))

        if self._pixmap is None:
            p.setPen(QColor(FG2))
            f = p.font(); f.setPointSize(12); p.setFont(f)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No image loaded\n\nClick + Add  ·  or drag an image here")
            return

        r = self._img_rect()
        p.drawPixmap(int(r.x()), int(r.y()), int(r.width()), int(r.height()), self._pixmap)

        widget_corners = [self._to_widget(c) for c in self._corners_img]

        if len(widget_corners) >= 2:
            pen = QPen(QColor(ACCENT)); pen.setWidth(2); p.setPen(pen)
            if len(widget_corners) == 4:
                poly = QPolygonF(widget_corners)
                p.save(); p.setOpacity(0.18)
                p.setBrush(QBrush(QColor(ACCENT))); p.setPen(Qt.PenStyle.NoPen)
                p.drawPolygon(poly); p.restore()
                p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPolygon(poly)
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                for i in range(len(widget_corners)-1):
                    p.drawLine(widget_corners[i].toPoint(), widget_corners[i+1].toPoint())

        for i, pt in enumerate(widget_corners):
            p.setPen(QPen(QColor("white"), 2))
            p.setBrush(QBrush(QColor(ACCENT)))
            p.drawEllipse(pt, self.HANDLE_R, self.HANDLE_R)
            if i < len(self._labels):
                p.setPen(QColor("white"))
                f = p.font(); f.setPointSize(7); f.setBold(True); p.setFont(f)
                fm  = p.fontMetrics()
                lbl = self._labels[i]
                p.drawText(int(pt.x() - fm.horizontalAdvance(lbl)/2),
                           int(pt.y() + fm.ascent()/2), lbl)

    # ── mouse ───────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        pos_w = QPointF(e.position())
        for i, c_img in enumerate(self._corners_img):
            c_w = self._to_widget(c_img)
            if (pos_w - c_w).manhattanLength() < self.HANDLE_R * 2.5:
                self._drag_idx = i; return

    def mouseMoveEvent(self, e):
        if self._drag_idx >= 0:
            self._corners_img[self._drag_idx] = self._to_image(QPointF(e.position()))
            self.update()

    def mouseReleaseEvent(self, e):
        self._drag_idx = -1

    # ── drag-drop image onto widget ─────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            exts = (".png",".jpg",".jpeg",".bmp",".tiff",".tif",".webp")
            if any(u.toLocalFile().lower().endswith(exts) for u in e.mimeData().urls()):
                e.acceptProposedAction()

    def dropEvent(self, e):
        exts = (".png",".jpg",".jpeg",".bmp",".tiff",".tif",".webp")
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if any(p.lower().endswith(x) for x in exts):
                self.load(p)
                self.image_loaded.emit(p)
                break


# ── Main window ────────────────────────────────────────────────────────────────

class App(QMainWindow):

    # Signals so worker threads can deliver results to the GUI thread safely.
    _bg_done   = pyqtSignal(object, object)   # (callback, result)
    _bg_failed = pyqtSignal(object, object)   # (callback, exception)
    _bg_cb     = pyqtSignal(object, tuple)    # (callback, args)  — for progress

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tool")
        self.setMinimumSize(760, 660)
        self._bg_done.connect(lambda cb, r: cb(r))
        self._bg_failed.connect(lambda cb, e: cb(e))
        self._bg_cb.connect(lambda cb, args: cb(*args))
        self._build()
        self._top_guard_timer = QTimer(self)
        self._top_guard_timer.timeout.connect(self._sync_fullscreen_top_guard)
        self._top_guard_timer.start(100)

    def _run_bg(self, fn, on_ok, on_err):
        """Run fn() in a worker thread; deliver result/exception to main thread via signals."""
        def _t():
            try:
                self._bg_done.emit(on_ok, fn())
            except Exception as e:
                self._bg_failed.emit(on_err, e)
        threading.Thread(target=_t, daemon=True).start()

    def _post(self, cb, *args):
        """Call cb(*args) on the GUI thread from any thread."""
        self._bg_cb.emit(cb, args)

    def _build(self):
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.tabBar().setExpanding(True)
        tabs.tabBar().setUsesScrollButtons(True)
        tabs.tabBar().setElideMode(Qt.TextElideMode.ElideNone)
        self.setCentralWidget(tabs)

        tabs.addTab(self._split_tab(),      "  Split  ")
        tabs.addTab(self._merge_tab(),      "  Merge  ")
        tabs.addTab(self._rearrange_tab(),  "  Rearrange  ")
        tabs.addTab(self._compress_tab(),   "  Compress  ")
        tabs.addTab(self._extract_tab(),    "  Extract Text  ")
        tabs.addTab(self._vectordb_tab(),   "  Vector DB  ")
        tabs.addTab(self._scan_tab(),       "  Scan to PDF  ")

        self._sb = QStatusBar(); self.setStatusBar(self._sb)
        self._sb.showMessage("Ready")

    def _sync_fullscreen_top_guard(self):
        """Keep tabs below the macOS menu/title overlay while it is visible."""
        inset = 0
        if sys.platform == "darwin" and self.isFullScreen():
            screen = self.screen()
            screen_top = screen.geometry().top() if screen else 0
            cursor_y = QCursor.pos().y()
            current_inset = self.contentsMargins().top()
            near_top = cursor_y <= screen_top + 64
            moving_to_tabs = current_inset > 0 and cursor_y <= screen_top + 110
            if near_top or moving_to_tabs:
                inset = 58

        if self.contentsMargins().top() != inset:
            self.setContentsMargins(0, inset, 0, 0)

    # ──────────────────────────────────────────────────────────────────────────
    # SPLIT TAB
    # ──────────────────────────────────────────────────────────────────────────

    def _split_tab(self):
        self._sp_path = ""
        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 16); lay.setSpacing(0)

        # ── Drop zone ────────────────────────────────────────────────────────
        self._sp_zone = DropZone("Choose a PDF to split",
                                 "drag & drop  ·  or click to browse")
        self._sp_zone.clicked.connect(self._sp_pick)
        self._sp_zone.file_dropped.connect(self._sp_load)
        lay.addWidget(self._sp_zone)

        self._sp_info = QLabel("")
        self._sp_info.setProperty("cls", "info")
        self._sp_info.style().unpolish(self._sp_info)
        self._sp_info.style().polish(self._sp_info)
        self._sp_info.hide()
        lay.addWidget(self._sp_info)
        lay.addWidget(_vspace(8))

        # ── Split mode ───────────────────────────────────────────────────────
        lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("SPLIT MODE")); lay.addWidget(_vspace(8))

        self._sp_mode_grp = QButtonGroup(self)
        mode_row = QWidget(); ml = QHBoxLayout(mode_row)
        ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(24)
        for v, t in [("pages", "Pages per chunk"),
                     ("parts", "Equal parts"),
                     ("custom", "Custom page list")]:
            rb = QRadioButton(t); self._sp_mode_grp.addButton(rb)
            rb.setProperty("_val", v)
            if v == "pages": rb.setChecked(True)
            rb.toggled.connect(self._sp_mode_upd)
            ml.addWidget(rb)
        ml.addStretch()
        lay.addWidget(mode_row)
        lay.addWidget(_vspace(14))

        # ── Value (pages/parts) ──────────────────────────────────────────────
        self._sp_val_block = QWidget(); vbl = QVBoxLayout(self._sp_val_block)
        vbl.setContentsMargins(0, 0, 0, 0); vbl.setSpacing(6)
        self._sp_val_lbl = _section("PAGES PER CHUNK"); vbl.addWidget(self._sp_val_lbl)
        self._sp_val = Stepper(from_=1, to=9999, initial=1)
        vbl.addWidget(self._sp_val)
        lay.addWidget(self._sp_val_block)

        # ── Custom spec (hidden initially) ───────────────────────────────────
        self._sp_cust_block = QWidget(); cbl = QVBoxLayout(self._sp_cust_block)
        cbl.setContentsMargins(0, 0, 0, 0); cbl.setSpacing(6)
        cbl.addWidget(_section("PAGES TO EXTRACT"))
        cust_row = QWidget(); cl = QHBoxLayout(cust_row)
        cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(8)
        self._sp_spec = QLineEdit(); self._sp_spec.setPlaceholderText("e.g.  1, 3, 5-10, 15")
        self._sp_spec.setFixedWidth(260)
        cl.addWidget(self._sp_spec); cl.addStretch()
        cbl.addWidget(cust_row)
        self._sp_cust_block.hide()
        lay.addWidget(self._sp_cust_block)
        lay.addWidget(_vspace(14))

        # ── Output folder ────────────────────────────────────────────────────
        lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("OUTPUT FOLDER")); lay.addWidget(_vspace(8))
        of_row = QWidget(); of_l = QHBoxLayout(of_row)
        of_l.setContentsMargins(0, 0, 0, 0); of_l.setSpacing(8)
        self._sp_outdir = QLineEdit(); self._sp_outdir.setReadOnly(True)
        self._sp_outdir.setPlaceholderText("Choose output folder…")
        browse_btn = _secondary("Browse"); browse_btn.clicked.connect(self._sp_browse_dir)
        of_l.addWidget(self._sp_outdir, 1); of_l.addWidget(browse_btn)
        lay.addWidget(of_row)

        # ── Action ───────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8))
        lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addStretch()
        self._sp_btn = _primary("Split PDF"); self._sp_btn.clicked.connect(self._sp_run)
        lay.addWidget(self._sp_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(_vspace(4))
        self._sp_prog = ProgBar(); lay.addWidget(self._sp_prog)

        return page

    def _sp_mode_upd(self):
        checked = self._sp_mode_grp.checkedButton()
        if checked is None: return
        m = checked.property("_val")
        self._sp_cust_block.setVisible(m == "custom")
        self._sp_val_block.setVisible(m != "custom")
        if m == "pages": self._sp_val_lbl.setText("PAGES PER CHUNK")
        elif m == "parts": self._sp_val_lbl.setText("NUMBER OF PARTS")

    def _sp_load(self, path):
        self._sp_path = path
        try:
            pages, sz = pdf_info(path)
            self._sp_info.setText(
                f"  {os.path.basename(path)}   ·   {pages} pages   ·   {sz}")
            self._sp_info.show()
            self._sp_zone.set(os.path.basename(path), "Click to choose a different file")
            if not self._sp_outdir.text():
                self._sp_outdir.setText(os.path.dirname(path))
            self._sp_prog.reset()
            self._sb.showMessage(f"Loaded  {os.path.basename(path)}  ({pages} pages)")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _sp_pick(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PDF to split",
                   filter="PDF Files (*.pdf);;All Files (*)")
        if p: self._sp_load(p)

    def _sp_browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Output folder")
        if d: self._sp_outdir.setText(d)

    def _sp_run(self):
        if not self._sp_path:
            QMessageBox.warning(self, "No file", "Choose a PDF to split."); return
        if not self._sp_outdir.text():
            QMessageBox.warning(self, "No folder", "Choose an output folder."); return

        self._sp_btn.setDisabled(True); self._sp_btn.setText("Splitting…")
        self._sp_prog.working("Preparing…")

        path = self._sp_path; outdir = self._sp_outdir.text()
        checked = self._sp_mode_grp.checkedButton()
        mode = checked.property("_val") if checked else "pages"
        val = self._sp_val.get(); spec = self._sp_spec.text()

        def _cb(done, total, name):
            self._post(self._sp_prog.step, done, total, name)
        def _ok(out):
            self._sp_prog.done(f"{len(out)} file(s) created", outdir)
            self._sp_btn.setDisabled(False); self._sp_btn.setText("Split PDF")
            self._sb.showMessage(f"Split complete — {len(out)} files")
        def _err(e):
            self._sp_prog.error(str(e))
            self._sp_btn.setDisabled(False); self._sp_btn.setText("Split PDF")
            QMessageBox.critical(self, "Split failed", str(e))

        self._run_bg(
            lambda: do_split(path, outdir, mode, val, spec, _cb),
            _ok, _err)

    # ──────────────────────────────────────────────────────────────────────────
    # MERGE TAB
    # ──────────────────────────────────────────────────────────────────────────

    def _merge_tab(self):
        self._mg_paths: list[str] = []
        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 16); lay.setSpacing(0)

        # ── File list ────────────────────────────────────────────────────────
        lay.addWidget(_section("PDFS TO MERGE")); lay.addWidget(_vspace(8))

        self._mg_tv = QTableWidget(0, 4)
        self._mg_tv.setHorizontalHeaderLabels(["#", "Filename", "Pages", "Size"])
        self._mg_tv.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i, w in [(0, 44), (2, 74), (3, 90)]:
            self._mg_tv.setHorizontalHeader(self._mg_tv.horizontalHeader())
            self._mg_tv.setColumnWidth(i, w)
        self._mg_tv.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._mg_tv.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._mg_tv.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._mg_tv.setColumnWidth(0, 44); self._mg_tv.setColumnWidth(2, 74)
        self._mg_tv.setColumnWidth(3, 90)
        self._mg_tv.verticalHeader().hide()
        self._mg_tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._mg_tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._mg_tv.setAlternatingRowColors(False)
        lay.addWidget(self._mg_tv, 1)   # stretch=1 → takes available space
        lay.addWidget(_vspace(8))

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = QWidget(); bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(6)
        for t, fn in [("Add PDFs", self._mg_add), ("Remove", self._mg_del),
                      ("Move Up", self._mg_up), ("Move Down", self._mg_dn),
                      ("Clear All", self._mg_clear)]:
            b = _secondary(t); b.clicked.connect(fn); bl.addWidget(b)
        bl.addStretch()
        self._mg_count_lbl = QLabel("")
        self._mg_count_lbl.setStyleSheet(f"color: {FG2}; font-size: 10pt;")
        bl.addWidget(self._mg_count_lbl)
        lay.addWidget(btn_row)

        lay.addWidget(_vspace(10))
        self._mg_letter = QCheckBox("Smart fit pages to US Letter")
        self._mg_letter.setChecked(True)
        self._mg_letter.setStyleSheet(f"""
            QCheckBox {{ color:{FG}; spacing:6px; font-size:10pt; }}
            QCheckBox::indicator {{ width:16px; height:16px; border-radius:3px;
                                    border:2px solid {BORDER}; background:{CARD}; }}
            QCheckBox::indicator:checked {{ background:{ACCENT}; border-color:{ACCENT}; }}
        """)
        lay.addWidget(self._mg_letter)
        letter_hint = QLabel(
            "Near-Letter pages fill the sheet · large pages scale down · "
            "small pages grow up to 10% and keep centered margins"
        )
        letter_hint.setWordWrap(True)
        letter_hint.setStyleSheet(f"color:{FG2}; font-size:9pt; padding-left:24px;")
        lay.addWidget(letter_hint)

        # ── Save path ────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("SAVE MERGED FILE AS")); lay.addWidget(_vspace(8))
        of_row = QWidget(); of_l = QHBoxLayout(of_row)
        of_l.setContentsMargins(0, 0, 0, 0); of_l.setSpacing(8)
        self._mg_out = QLineEdit(); self._mg_out.setReadOnly(True)
        self._mg_out.setPlaceholderText("Choose save location…")
        browse_btn = _secondary("Browse"); browse_btn.clicked.connect(self._mg_pick_out)
        of_l.addWidget(self._mg_out, 1); of_l.addWidget(browse_btn)
        lay.addWidget(of_row)

        # ── Action ───────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        self._mg_btn = _primary("Merge PDFs"); self._mg_btn.clicked.connect(self._mg_run)
        lay.addWidget(self._mg_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(_vspace(4))
        self._mg_prog = ProgBar(); lay.addWidget(self._mg_prog)

        return page

    def _mg_renum(self):
        for i in range(self._mg_tv.rowCount()):
            self._mg_tv.item(i, 0).setText(str(i+1))
        n = self._mg_tv.rowCount()
        self._mg_count_lbl.setText(f"{n} file{'s' if n!=1 else ''} queued" if n else "")

    def _mg_add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add PDFs",
                       filter="PDF Files (*.pdf);;All Files (*)")
        if not paths: return
        if not self._mg_out.text():
            self._mg_out.setText(os.path.join(os.path.dirname(paths[0]), "merged.pdf"))

        def _load():
            items = []
            for p in paths:
                try: items.append((p, os.path.basename(p), *pdf_info(p)))
                except Exception: pass
            self._post(self._mg_insert, items)
        threading.Thread(target=_load, daemon=True).start()

    def _mg_insert(self, items):
        for path, name, pages, size in items:
            self._mg_paths.append(path)
            r = self._mg_tv.rowCount(); self._mg_tv.insertRow(r)
            for c, v in enumerate([str(r+1), name, str(pages), size]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if c != 1 else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._mg_tv.setItem(r, c, item)
        self._mg_renum()

    def _mg_del(self):
        rows = sorted({i.row() for i in self._mg_tv.selectedItems()}, reverse=True)
        for r in rows:
            self._mg_tv.removeRow(r); self._mg_paths.pop(r)
        self._mg_renum()

    def _mg_up(self):
        r = self._mg_tv.currentRow()
        if r <= 0: return
        self._mg_paths.insert(r-1, self._mg_paths.pop(r))
        self._mg_tv.insertRow(r-1)
        for c in range(self._mg_tv.columnCount()):
            item = self._mg_tv.takeItem(r+1, c)
            self._mg_tv.setItem(r-1, c, item)
        self._mg_tv.removeRow(r+1)
        self._mg_renum(); self._mg_tv.selectRow(r-1)

    def _mg_dn(self):
        r = self._mg_tv.currentRow()
        if r < 0 or r >= self._mg_tv.rowCount()-1: return
        self._mg_paths.insert(r+1, self._mg_paths.pop(r))
        self._mg_tv.insertRow(r+2)
        for c in range(self._mg_tv.columnCount()):
            item = self._mg_tv.takeItem(r, c)
            self._mg_tv.setItem(r+2, c, item)
        self._mg_tv.removeRow(r)
        self._mg_renum(); self._mg_tv.selectRow(r+1)

    def _mg_clear(self):
        self._mg_tv.setRowCount(0); self._mg_paths.clear()
        self._mg_renum(); self._mg_prog.reset()

    def _mg_pick_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save merged PDF as",
                   filter="PDF Files (*.pdf)")
        if p: self._mg_out.setText(p if p.endswith(".pdf") else p+".pdf")

    def _mg_run(self):
        if len(self._mg_paths) < 2:
            QMessageBox.warning(self, "Too few files", "Add at least 2 PDFs."); return
        out = self._mg_out.text()
        if not out:
            QMessageBox.warning(self, "No output", "Choose where to save."); return

        self._mg_btn.setDisabled(True); self._mg_btn.setText("Merging…")
        self._mg_prog.working("Preparing…")

        paths = list(self._mg_paths)
        smart_letter = self._mg_letter.isChecked()

        def _cb(done, total, name):
            self._post(self._mg_prog.step, done, total, name)
        def _ok(result):
            pages, fit_counts = result
            fit_note = ""
            if smart_letter:
                fit_note = (
                    f" · Letter fit: {fit_counts['unchanged']} unchanged, "
                    f"{fit_counts['stretched']} stretched, "
                    f"{fit_counts['scaled down']} reduced, "
                    f"{fit_counts['scaled up']} enlarged"
                )
            self._mg_prog.done(
                f"Merged {len(paths)} PDFs  ({pages} pages total){fit_note}",
                out,
            )
            self._mg_btn.setDisabled(False); self._mg_btn.setText("Merge PDFs")
            self._sb.showMessage(f"Merged → {os.path.basename(out)}")
        def _err(e):
            self._mg_prog.error(str(e))
            self._mg_btn.setDisabled(False); self._mg_btn.setText("Merge PDFs")
            QMessageBox.critical(self, "Merge failed", str(e))

        self._run_bg(
            lambda: do_merge(paths, out, _cb, smart_letter),
            _ok, _err)

    # ──────────────────────────────────────────────────────────────────────────
    # EXTRACT TEXT TAB
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_tab(self):
        self._ex_path = ""
        self._fhits: list[tuple[int, int]] = []   # (start, end) char positions
        self._fidx = 0

        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 16); lay.setSpacing(0)

        # ── Drop zone ────────────────────────────────────────────────────────
        self._ex_zone = DropZone("Choose a PDF to extract text from",
                                 "drag & drop  ·  or click to browse")
        self._ex_zone.clicked.connect(self._ex_pick)
        self._ex_zone.file_dropped.connect(self._ex_load)
        lay.addWidget(self._ex_zone)

        self._ex_info = QLabel("")
        self._ex_info.setProperty("cls", "info")
        self._ex_info.style().unpolish(self._ex_info)
        self._ex_info.style().polish(self._ex_info)
        self._ex_info.hide()
        lay.addWidget(self._ex_info); lay.addWidget(_vspace(8))

        # ── Page range ───────────────────────────────────────────────────────
        lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("PAGE RANGE")); lay.addWidget(_vspace(8))
        pr = QWidget(); pl = QHBoxLayout(pr)
        pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(12)
        pl.addWidget(QLabel("From"))
        self._ex_from = Stepper(from_=1, to=9999, initial=1); pl.addWidget(self._ex_from)
        pl.addSpacing(8); pl.addWidget(QLabel("To"))
        self._ex_to = Stepper(from_=1, to=9999, initial=9999); pl.addWidget(self._ex_to)
        hint = QLabel("  (9999 = all pages)")
        hint.setStyleSheet(f"color: {FG2}; font-size: 9pt;"); pl.addWidget(hint)
        pl.addStretch()
        lay.addWidget(pr)

        # ── Action ───────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        act_row = QWidget(); al = QHBoxLayout(act_row)
        al.setContentsMargins(0, 0, 0, 0)
        self._ex_btn = _primary("Extract Text"); self._ex_btn.clicked.connect(self._ex_run)
        self._ex_status = QLabel(""); self._ex_status.setStyleSheet(f"color: {GREEN}; font-size: 10pt;")
        al.addStretch(); al.addWidget(self._ex_btn); al.addSpacing(16)
        al.addWidget(self._ex_status); al.addStretch()
        lay.addWidget(act_row)

        # ── Results ──────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("EXTRACTED TEXT")); lay.addWidget(_vspace(8))

        find_row = QWidget(); fl = QHBoxLayout(find_row)
        fl.setContentsMargins(0, 0, 0, 0); fl.setSpacing(8)
        fl.addWidget(QLabel("Find"))
        self._find_edit = QLineEdit(); self._find_edit.setFixedWidth(220)
        self._find_edit.setPlaceholderText("Search…")
        self._find_edit.textChanged.connect(self._find_do)
        prev_btn = _secondary("Prev"); prev_btn.clicked.connect(lambda: self._find_step(-1))
        next_btn = _secondary("Next"); next_btn.clicked.connect(lambda: self._find_step(1))
        self._find_cnt = QLabel("")
        self._find_cnt.setStyleSheet(f"color: {FG2}; font-size: 10pt;")
        fl.addWidget(self._find_edit); fl.addWidget(prev_btn); fl.addWidget(next_btn)
        fl.addWidget(self._find_cnt); fl.addStretch()
        lay.addWidget(find_row); lay.addWidget(_vspace(6))

        self._txt = QTextEdit(); self._txt.setReadOnly(True)
        lay.addWidget(self._txt, 1)   # stretch=1
        lay.addWidget(_vspace(6))

        copy_row = QWidget(); cl = QHBoxLayout(copy_row)
        cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(8)
        copy_btn = _secondary("Copy All"); copy_btn.clicked.connect(self._ex_copy)
        save_btn = _secondary("Save as TXT"); save_btn.clicked.connect(self._ex_save)
        self._ex_copy_lbl = QLabel("")
        self._ex_copy_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10pt;")
        cl.addWidget(copy_btn); cl.addWidget(save_btn)
        cl.addWidget(self._ex_copy_lbl); cl.addStretch()
        lay.addWidget(copy_row)

        return page

    def _ex_load(self, path):
        self._ex_path = path
        try:
            pages, sz = pdf_info(path)
            self._ex_info.setText(
                f"  {os.path.basename(path)}   ·   {pages} pages   ·   {sz}")
            self._ex_info.show()
            self._ex_zone.set(os.path.basename(path), "Click to choose a different file")
            self._ex_from.set(1); self._ex_to.set(pages)
            self._ex_status.setText("")
            self._sb.showMessage(f"Loaded  {os.path.basename(path)}  ({pages} pages)")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _ex_pick(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PDF",
                   filter="PDF Files (*.pdf);;All Files (*)")
        if p: self._ex_load(p)

    def _ex_run(self):
        if not self._ex_path:
            QMessageBox.warning(self, "No file", "Choose a PDF first."); return
        try:
            total = len(PdfReader(self._ex_path).pages)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e)); return

        frm = max(1, self._ex_from.get()) - 1
        to  = min(total, self._ex_to.get())

        self._ex_btn.setDisabled(True); self._ex_btn.setText("Extracting…")
        self._ex_status.setText("Working…")
        self._txt.clear()
        self._find_edit.clear(); self._fhits.clear(); self._find_cnt.setText("")

        path = self._ex_path
        def _stream():
            found = False
            for pnum, text in do_extract(path, frm, to):
                s = text.strip(); found = found or bool(s)
                self._post(
                    self._txt_add,
                    f"Page {pnum}\n{'─'*44}\n{s}\n\n",
                )
            if not found:
                self._post(
                    self._txt_add,
                    "(No selectable text — PDF may be scanned/image-based)",
                )
            self._post(self._ex_done)
        threading.Thread(target=_stream, daemon=True).start()

    def _txt_add(self, chunk):
        self._txt.moveCursor(QTextCursor.MoveOperation.End)
        self._txt.insertPlainText(chunk)
        self._txt.moveCursor(QTextCursor.MoveOperation.End)

    def _ex_done(self):
        self._ex_btn.setDisabled(False); self._ex_btn.setText("Extract Text")
        self._ex_status.setText("Done"); self._sb.showMessage("Extraction complete")
        QTimer.singleShot(2500, lambda: self._ex_status.setText(""))

    def _find_do(self, q=""):
        q = self._find_edit.text()
        fmt_clear = self._txt.document().find("")  # reset
        cursor = self._txt.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self._txt.setTextCursor(cursor)
        # Reset all highlighting
        fmt_plain = self._txt.currentCharFormat()
        fmt_plain.setBackground(self._txt.palette().base())
        cursor.setCharFormat(fmt_plain)
        cursor.clearSelection(); self._txt.setTextCursor(cursor)

        self._fhits.clear(); self._fidx = 0
        if not q: self._find_cnt.setText(""); return

        from PyQt6.QtGui import QTextCharFormat, QColor
        fmt_hit = QTextCharFormat(); fmt_hit.setBackground(QColor("#E8A87C")); fmt_hit.setForeground(QColor("#111"))

        doc = self._txt.document(); c = doc.find(q, 0)
        while not c.isNull():
            c.mergeCharFormat(fmt_hit)
            self._fhits.append((c.selectionStart(), c.selectionEnd()))
            c = doc.find(q, c)

        n = len(self._fhits)
        self._find_cnt.setText(f"{n} match{'es' if n!=1 else ''}")
        if n: self._find_step(0)

    def _find_step(self, d):
        if not self._fhits: return
        from PyQt6.QtGui import QTextCharFormat, QColor
        fmt_cur = QTextCharFormat(); fmt_cur.setBackground(QColor(ACCENT)); fmt_cur.setForeground(QColor("white"))
        fmt_hit = QTextCharFormat(); fmt_hit.setBackground(QColor("#E8A87C")); fmt_hit.setForeground(QColor("#111"))

        # De-highlight current
        s, e = self._fhits[self._fidx]
        cur = self._txt.textCursor(); cur.setPosition(s); cur.setPosition(e, QTextCursor.MoveMode.KeepAnchor)
        cur.mergeCharFormat(fmt_hit)

        self._fidx = (self._fidx + d) % len(self._fhits)
        s, e = self._fhits[self._fidx]
        cur.setPosition(s); cur.setPosition(e, QTextCursor.MoveMode.KeepAnchor)
        cur.mergeCharFormat(fmt_cur)
        self._txt.setTextCursor(cur); self._txt.ensureCursorVisible()
        self._find_cnt.setText(f"{self._fidx+1}/{len(self._fhits)}")

    def _ex_copy(self):
        t = self._txt.toPlainText().strip()
        if not t: QMessageBox.warning(self, "Empty", "Nothing to copy yet."); return
        QApplication.clipboard().setText(t)
        self._ex_copy_lbl.setText("Copied to clipboard")
        QTimer.singleShot(2000, lambda: self._ex_copy_lbl.setText(""))

    def _ex_save(self):
        t = self._txt.toPlainText().strip()
        if not t: QMessageBox.warning(self, "Empty", "Nothing to save yet."); return
        p, _ = QFileDialog.getSaveFileName(self, "Save text",
                   filter="Text Files (*.txt);;All Files (*)")
        if not p: return
        with open(p, "w", encoding="utf-8") as f: f.write(t)
        self._ex_copy_lbl.setText(f"Saved  {os.path.basename(p)}")
        QTimer.singleShot(2500, lambda: self._ex_copy_lbl.setText(""))

    # ──────────────────────────────────────────────────────────────────────────
    # VECTOR DB TAB
    # ──────────────────────────────────────────────────────────────────────────

    def _vectordb_tab(self):
        self._vdb_paths: list[str] = []

        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 16); lay.setSpacing(0)

        # ── Info card ────────────────────────────────────────────────────────
        card = QFrame(); card.setStyleSheet(f"background: {CARD}; border-radius: 6px;")
        cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 12); cl.setSpacing(4)
        title = QLabel("Build a Vector Database from PDFs")
        title.setStyleSheet(f"color: {FG}; font-size: 12pt; font-weight: bold; background: transparent;")
        desc = QLabel("Splits each PDF into text chunks, generates semantic embeddings "
                      "(all-MiniLM-L6-v2), and saves a persistent ChromaDB store "
                      "queryable by any LLM.   First run downloads the model (~80 MB).")
        desc.setStyleSheet(f"color: {FG2}; font-size: 10pt; background: transparent;")
        desc.setWordWrap(True)
        cl.addWidget(title); cl.addWidget(desc)
        lay.addWidget(card)

        # ── File list ────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("PDFS TO INDEX")); lay.addWidget(_vspace(8))

        self._vdb_tv = QTableWidget(0, 3)
        self._vdb_tv.setHorizontalHeaderLabels(["Filename", "Pages", "Size"])
        self._vdb_tv.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._vdb_tv.setColumnWidth(1, 74); self._vdb_tv.setColumnWidth(2, 90)
        self._vdb_tv.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._vdb_tv.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._vdb_tv.verticalHeader().hide()
        self._vdb_tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._vdb_tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._vdb_tv.setFixedHeight(160)
        lay.addWidget(self._vdb_tv)
        lay.addWidget(_vspace(8))

        vbtn_row = QWidget(); vbl = QHBoxLayout(vbtn_row)
        vbl.setContentsMargins(0, 0, 0, 0); vbl.setSpacing(6)
        for t, fn in [("Add PDFs", self._vdb_add), ("Remove", self._vdb_del),
                      ("Clear", self._vdb_clear)]:
            b = _secondary(t); b.clicked.connect(fn); vbl.addWidget(b)
        vbl.addStretch()
        lay.addWidget(vbtn_row)

        # ── Settings ─────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("SETTINGS")); lay.addWidget(_vspace(10))

        settings_row = QWidget(); sl = QHBoxLayout(settings_row)
        sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(32)

        col1 = QWidget(); c1l = QVBoxLayout(col1); c1l.setContentsMargins(0,0,0,0); c1l.setSpacing(6)
        c1l.addWidget(_section("COLLECTION NAME"))
        self._vdb_coll = QLineEdit("my_documents"); self._vdb_coll.setFixedWidth(200)
        c1l.addWidget(self._vdb_coll)

        col2 = QWidget(); c2l = QVBoxLayout(col2); c2l.setContentsMargins(0,0,0,0); c2l.setSpacing(6)
        c2l.addWidget(_section("CHUNK SIZE (chars)"))
        self._vdb_chunk = Stepper(from_=100, to=4000, initial=800, step=100)
        c2l.addWidget(self._vdb_chunk)

        col3 = QWidget(); c3l = QVBoxLayout(col3); c3l.setContentsMargins(0,0,0,0); c3l.setSpacing(6)
        c3l.addWidget(_section("OVERLAP (chars)"))
        self._vdb_overlap = Stepper(from_=0, to=500, initial=100, step=25)
        c3l.addWidget(self._vdb_overlap)

        sl.addWidget(col1); sl.addWidget(col2); sl.addWidget(col3); sl.addStretch()
        lay.addWidget(settings_row)
        lay.addWidget(_vspace(14))

        lay.addWidget(_section("OUTPUT FOLDER")); lay.addWidget(_vspace(8))
        of_row = QWidget(); of_l = QHBoxLayout(of_row)
        of_l.setContentsMargins(0, 0, 0, 0); of_l.setSpacing(8)
        self._vdb_outdir = QLineEdit(); self._vdb_outdir.setReadOnly(True)
        self._vdb_outdir.setPlaceholderText("Choose folder for ChromaDB store…")
        vbrowse = _secondary("Browse"); vbrowse.clicked.connect(self._vdb_browse)
        of_l.addWidget(self._vdb_outdir, 1); of_l.addWidget(vbrowse)
        lay.addWidget(of_row)

        # ── Action ───────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addStretch()
        self._vdb_btn = _primary("Build Vector DB"); self._vdb_btn.clicked.connect(self._vdb_run)
        lay.addWidget(self._vdb_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(_vspace(4))
        self._vdb_prog = ProgBar(); lay.addWidget(self._vdb_prog)

        # ── Snippet (shown after build) ───────────────────────────────────
        self._snip_block = QWidget(); snl = QVBoxLayout(self._snip_block)
        snl.setContentsMargins(0, 8, 0, 0); snl.setSpacing(8)
        snl.addWidget(_section("USAGE SNIPPET"))
        self._snip_txt = QTextEdit(); self._snip_txt.setReadOnly(True)
        self._snip_txt.setFixedHeight(200)
        snl.addWidget(self._snip_txt)
        self._snip_block.hide()
        lay.addWidget(self._snip_block)

        return page

    def _vdb_add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add PDFs to index",
                       filter="PDF Files (*.pdf);;All Files (*)")
        if not paths: return
        if not self._vdb_outdir.text():
            self._vdb_outdir.setText(os.path.join(os.path.dirname(paths[0]), "chroma_db"))

        def _load():
            items = []
            for p in paths:
                try: items.append((p, os.path.basename(p), *pdf_info(p)))
                except Exception: pass
            self._post(self._vdb_insert, items)
        threading.Thread(target=_load, daemon=True).start()

    def _vdb_insert(self, items):
        for path, name, pages, size in items:
            if path not in self._vdb_paths:
                self._vdb_paths.append(path)
                r = self._vdb_tv.rowCount(); self._vdb_tv.insertRow(r)
                for c, v in enumerate([name, str(pages), size]):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if c != 0
                                          else Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self._vdb_tv.setItem(r, c, item)

    def _vdb_del(self):
        rows = sorted({i.row() for i in self._vdb_tv.selectedItems()}, reverse=True)
        for r in rows:
            self._vdb_tv.removeRow(r); self._vdb_paths.pop(r)

    def _vdb_clear(self):
        self._vdb_tv.setRowCount(0); self._vdb_paths.clear(); self._vdb_prog.reset()

    def _vdb_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Vector DB output folder")
        if d: self._vdb_outdir.setText(d)

    def _vdb_run(self):
        if not self._vdb_paths:
            QMessageBox.warning(self, "No files", "Add at least one PDF."); return
        outdir = self._vdb_outdir.text()
        if not outdir:
            QMessageBox.warning(self, "No folder", "Choose where to save the DB."); return

        self._vdb_btn.setDisabled(True); self._vdb_btn.setText("Building…")
        self._vdb_prog.working("Initializing…")

        paths = list(self._vdb_paths)
        coll = self._vdb_coll.text().strip() or "my_documents"
        csz = self._vdb_chunk.get(); ov = self._vdb_overlap.get()

        def _cb(fi, ft, fname, pi, pt):
            detail = f"File {fi+1}/{ft}  —  {fname}  page {pi}/{pt}"
            self._post(
                self._vdb_prog.step,
                fi * pt + pi,
                max(ft * pt, 1),
                detail,
            )

        def _ok(res):
            n_chunks, coll_name = res
            snippet = textwrap.dedent(f"""\
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
            self._vdb_prog.done(f"{n_chunks} chunks indexed and saved", outdir)
            self._vdb_btn.setDisabled(False); self._vdb_btn.setText("Build Vector DB")
            self._sb.showMessage(f"Vector DB ready — {n_chunks} chunks in '{coll_name}'")
            self._snip_txt.setPlainText(snippet)
            self._snip_block.show()

        def _err(e):
            self._vdb_prog.error(str(e))
            self._vdb_btn.setDisabled(False); self._vdb_btn.setText("Build Vector DB")
            QMessageBox.critical(self, "Failed", str(e))

        self._run_bg(
            lambda: do_vectordb(paths, outdir, coll, csz, ov, _cb),
            _ok, _err)

    # ──────────────────────────────────────────────────────────────────────────
    # REARRANGE TAB
    # ──────────────────────────────────────────────────────────────────────────

    def _rearrange_tab(self):
        self._ra_path = ""
        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 16); lay.setSpacing(0)

        self._ra_zone = DropZone("Choose a PDF to rearrange",
                                 "drag & drop  ·  or click to browse")
        self._ra_zone.clicked.connect(self._ra_pick)
        self._ra_zone.file_dropped.connect(self._ra_load)
        lay.addWidget(self._ra_zone)

        self._ra_info = QLabel(""); self._ra_info.setProperty("cls", "info")
        self._ra_info.style().unpolish(self._ra_info); self._ra_info.style().polish(self._ra_info)
        self._ra_info.hide(); lay.addWidget(self._ra_info); lay.addWidget(_vspace(8))

        lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("PAGE ORDER  —  drag rows to reorder  ·  select and delete to remove"))
        lay.addWidget(_vspace(8))

        self._ra_list = QListWidget()
        self._ra_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._ra_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._ra_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._ra_list.setAlternatingRowColors(False)
        self._ra_list.setStyleSheet(f"""
            QListWidget {{ background:{CARD}; border:none; border-radius:4px;
                           color:{FG}; font-size:11pt; outline:none; }}
            QListWidget::item {{ padding:7px 14px; }}
            QListWidget::item:selected {{ background:{ACCENT}; color:white; }}
            QListWidget::item:hover:!selected {{ background:{CARD2}; }}
        """)
        lay.addWidget(self._ra_list, 1)
        lay.addWidget(_vspace(8))

        btn_row = QWidget(); bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0,0,0,0); bl.setSpacing(6)
        for t, fn in [("Move Up",   self._ra_up),   ("Move Down", self._ra_dn),
                      ("Delete Page", self._ra_del), ("Reverse All", self._ra_rev),
                      ("Reset",       self._ra_reset)]:
            b = _secondary(t); b.clicked.connect(fn); bl.addWidget(b)
        bl.addStretch()
        lay.addWidget(btn_row)

        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("OUTPUT FOLDER")); lay.addWidget(_vspace(8))
        of = QWidget(); ol = QHBoxLayout(of); ol.setContentsMargins(0,0,0,0); ol.setSpacing(8)
        self._ra_outdir = QLineEdit(); self._ra_outdir.setReadOnly(True)
        self._ra_outdir.setPlaceholderText("Choose output folder…")
        br2 = _secondary("Browse"); br2.clicked.connect(self._ra_browse)
        ol.addWidget(self._ra_outdir, 1); ol.addWidget(br2)
        lay.addWidget(of)

        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addStretch()
        self._ra_btn = _primary("Save Rearranged PDF"); self._ra_btn.clicked.connect(self._ra_run)
        lay.addWidget(self._ra_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(_vspace(4))
        self._ra_prog = ProgBar(); lay.addWidget(self._ra_prog)
        return page

    def _ra_pick(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PDF",
                   filter="PDF Files (*.pdf);;All Files (*)")
        if p: self._ra_load(p)

    def _ra_load(self, path):
        self._ra_path = path
        try:
            pages, sz = pdf_info(path)
            self._ra_info.setText(f"  {os.path.basename(path)}   ·   {pages} pages   ·   {sz}")
            self._ra_info.show()
            self._ra_zone.set(os.path.basename(path), "Click to choose a different file")
            self._ra_list.clear()
            for i in range(pages):
                self._ra_list.addItem(f"  Page {i+1}")
            if not self._ra_outdir.text():
                self._ra_outdir.setText(os.path.dirname(path))
            self._ra_prog.reset()
            self._sb.showMessage(f"Loaded  {os.path.basename(path)}  ({pages} pages)")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _ra_up(self):
        r = self._ra_list.currentRow()
        if r <= 0: return
        item = self._ra_list.takeItem(r)
        self._ra_list.insertItem(r-1, item); self._ra_list.setCurrentRow(r-1)

    def _ra_dn(self):
        r = self._ra_list.currentRow()
        if r < 0 or r >= self._ra_list.count()-1: return
        item = self._ra_list.takeItem(r)
        self._ra_list.insertItem(r+1, item); self._ra_list.setCurrentRow(r+1)

    def _ra_del(self):
        r = self._ra_list.currentRow()
        if r >= 0: self._ra_list.takeItem(r)

    def _ra_rev(self):
        items = [self._ra_list.item(i).text() for i in range(self._ra_list.count())]
        self._ra_list.clear()
        for t in reversed(items): self._ra_list.addItem(t)

    def _ra_reset(self):
        if not self._ra_path: return
        self._ra_list.clear()
        try:
            pages = len(PdfReader(self._ra_path).pages)
            for i in range(pages): self._ra_list.addItem(f"  Page {i+1}")
        except Exception: pass

    def _ra_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Output folder")
        if d: self._ra_outdir.setText(d)

    def _ra_run(self):
        if not self._ra_path:
            QMessageBox.warning(self, "No file", "Choose a PDF first."); return
        if not self._ra_outdir.text():
            QMessageBox.warning(self, "No folder", "Choose output folder."); return
        if self._ra_list.count() == 0:
            QMessageBox.warning(self, "Empty", "No pages in list."); return

        # Build 0-based order from list labels ("  Page N")
        total = len(PdfReader(self._ra_path).pages)
        order = []
        for i in range(self._ra_list.count()):
            txt = self._ra_list.item(i).text().strip()
            try:
                n = int(txt.split()[-1]) - 1
                if 0 <= n < total: order.append(n)
            except ValueError: pass
        if not order:
            QMessageBox.warning(self, "Bad order", "Could not parse page list."); return

        self._ra_btn.setDisabled(True); self._ra_btn.setText("Saving…")
        self._ra_prog.working("Writing pages…")
        path = self._ra_path; outdir = self._ra_outdir.text()

        def _ok(out):
            self._ra_prog.done(f"Saved  {os.path.basename(out)}", out)
            self._ra_btn.setDisabled(False); self._ra_btn.setText("Save Rearranged PDF")
            self._sb.showMessage(f"Rearranged → {os.path.basename(out)}")
        def _err(e):
            self._ra_prog.error(str(e))
            self._ra_btn.setDisabled(False); self._ra_btn.setText("Save Rearranged PDF")
            QMessageBox.critical(self, "Error", str(e))

        self._run_bg(lambda: do_rearrange(path, outdir, order), _ok, _err)

    # ──────────────────────────────────────────────────────────────────────────
    # COMPRESS TAB
    # ──────────────────────────────────────────────────────────────────────────

    def _compress_tab(self):
        self._co_path = ""
        self._co_cancel_event = None
        self._co_control = None
        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 20, 24, 16); lay.setSpacing(0)

        self._co_zone = DropZone("Choose a PDF to compress",
                                 "drag & drop  ·  or click to browse")
        self._co_zone.clicked.connect(self._co_pick)
        self._co_zone.file_dropped.connect(self._co_load)
        lay.addWidget(self._co_zone)

        self._co_info = QLabel(""); self._co_info.setProperty("cls", "info")
        self._co_info.style().unpolish(self._co_info); self._co_info.style().polish(self._co_info)
        self._co_info.hide(); lay.addWidget(self._co_info); lay.addWidget(_vspace(8))

        lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("COMPRESSION LEVEL")); lay.addWidget(_vspace(10))

        levels = [
            ("Screen (smallest)", "72 dpi images — best for screen / email"),
            ("eBook",             "150 dpi images — good balance (recommended)"),
            ("Print",             "300 dpi images — suitable for printing"),
            ("Prepress (largest)","300+ dpi, colour-managed — prepress quality"),
        ]
        self._co_grp = QButtonGroup(self)
        for i, (name, desc) in enumerate(levels):
            row = QWidget(); rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(10)
            rb = QRadioButton(name); rb.setProperty("_val", name)
            if i == 1: rb.setChecked(True)
            self._co_grp.addButton(rb)
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color:{FG2}; font-size:9pt;")
            rl.addWidget(rb); rl.addWidget(desc_lbl); rl.addStretch()
            lay.addWidget(row)
            if i < len(levels) - 1:
                lay.addSpacing(5)

        note = QLabel("ℹ  Ghostscript gives the broadest compression support. "
                      "Without it, embedded images are downsampled and recompressed with Pillow.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{FG2}; font-size:9pt; padding-top:8px;")
        lay.addWidget(note)

        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addWidget(_section("OUTPUT FILE")); lay.addWidget(_vspace(8))
        of = QWidget(); ol = QHBoxLayout(of); ol.setContentsMargins(0,0,0,0); ol.setSpacing(8)
        self._co_out = QLineEdit(); self._co_out.setReadOnly(True)
        self._co_out.setPlaceholderText("Choose save location…")
        br2 = _secondary("Browse"); br2.clicked.connect(self._co_browse)
        ol.addWidget(self._co_out, 1); ol.addWidget(br2)
        lay.addWidget(of)

        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(12))
        lay.addStretch()
        self._co_btn = _primary("Compress PDF"); self._co_btn.clicked.connect(self._co_run)
        self._co_cancel_btn = _secondary("Cancel")
        self._co_cancel_btn.clicked.connect(self._co_cancel)
        self._co_cancel_btn.hide()
        actions = _hbox(None, self._co_btn, self._co_cancel_btn, None, spacing=10)
        lay.addWidget(actions)
        lay.addWidget(_vspace(4))
        self._co_prog = ProgBar(); lay.addWidget(self._co_prog)
        return page

    def _co_pick(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PDF",
                   filter="PDF Files (*.pdf);;All Files (*)")
        if p: self._co_load(p)

    def _co_load(self, path):
        self._co_path = path
        try:
            pages, sz = pdf_info(path)
            self._co_info.setText(f"  {os.path.basename(path)}   ·   {pages} pages   ·   {sz}")
            self._co_info.show()
            self._co_zone.set(os.path.basename(path), "Click to choose a different file")
            base = os.path.splitext(path)[0]
            self._co_out.setText(base + "_compressed.pdf")
            self._co_prog.reset()
            self._sb.showMessage(f"Loaded  {os.path.basename(path)}  —  {sz}")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _co_browse(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save compressed PDF as",
                   filter="PDF Files (*.pdf)")
        if p: self._co_out.setText(p if p.endswith(".pdf") else p+".pdf")

    def _co_run(self):
        if not self._co_path:
            QMessageBox.warning(self, "No file", "Choose a PDF first."); return
        out = self._co_out.text()
        if not out:
            QMessageBox.warning(self, "No output", "Choose where to save."); return
        checked = self._co_grp.checkedButton()
        level = checked.property("_val") if checked else "eBook"

        orig_size = os.path.getsize(self._co_path)
        self._co_btn.setDisabled(True); self._co_btn.setText("Compressing…")
        self._co_cancel_btn.setDisabled(False)
        self._co_cancel_btn.setText("Cancel")
        self._co_cancel_btn.show()
        self._co_prog.working("Compressing…")

        src = self._co_path
        self._co_cancel_event = threading.Event()
        self._co_control = {}

        def _restore_controls():
            self._co_btn.setDisabled(False)
            self._co_btn.setText("Compress PDF")
            self._co_cancel_btn.hide()
            self._co_cancel_btn.setDisabled(False)
            self._co_cancel_btn.setText("Cancel")
            self._co_cancel_event = None
            self._co_control = None

        def _progress(done, total, detail):
            if total:
                self._post(self._co_prog.step, done, total, detail)
            else:
                self._post(self._co_prog.working, detail)

        def _ok(res):
            out_path, method = res
            new_size = os.path.getsize(out_path)
            ratio = (1 - new_size/orig_size)*100 if orig_size else 0
            orig_fmt = fmt_size(src); new_fmt = fmt_size(out_path)
            self._co_prog.done(
                f"{orig_fmt}  →  {new_fmt}   ({ratio:.1f}% smaller)   via {method}",
                out_path)
            _restore_controls()
            self._sb.showMessage(f"Compressed → {os.path.basename(out_path)}")
        def _err(e):
            _restore_controls()
            if isinstance(e, CompressionCancelled):
                self._co_prog.error("Compression cancelled. Partial output removed.")
                self._sb.showMessage("Compression cancelled")
                return
            self._co_prog.error(str(e))
            QMessageBox.critical(self, "Compression failed", str(e))

        self._run_bg(
            lambda: do_compress(
                src, out, level, _progress,
                self._co_cancel_event, self._co_control,
            ),
            _ok, _err)

    def _co_cancel(self):
        if not self._co_cancel_event:
            return
        self._co_cancel_event.set()
        process = (self._co_control or {}).get("process")
        if process and process.poll() is None:
            process.terminate()
        self._co_cancel_btn.setDisabled(True)
        self._co_cancel_btn.setText("Cancelling…")
        self._co_prog.working("Cancelling and removing partial output…")

    # ──────────────────────────────────────────────────────────────────────────
    # SCAN TO PDF TAB  (Microsoft Lens-style)
    # ──────────────────────────────────────────────────────────────────────────

    def _scan_tab(self):
        # Track the currently-edited page by item reference (stable across reorders).
        self._sc_cur_item: QListWidgetItem | None = None

        page = QWidget(); lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 16, 24, 12); lay.setSpacing(0)

        # ── Info line ─────────────────────────────────────────────────────────
        self._sc_info_lbl = QLabel(
            "Add document photos, drag the orange corners on each, "
            "then convert into a multi-page PDF.")
        self._sc_info_lbl.setStyleSheet(f"color:{FG2}; font-size:10pt;")
        self._sc_info_lbl.setWordWrap(True)
        lay.addWidget(self._sc_info_lbl); lay.addWidget(_vspace(8))

        # ── Crop area (the active page) ───────────────────────────────────────
        self._sc_crop = ImageCropWidget()
        self._sc_crop.image_loaded.connect(lambda p: self._sc_add_paths([p]))
        lay.addWidget(self._sc_crop, 1)
        lay.addWidget(_vspace(8))

        # ── Page strip with thumbnails + Add button ───────────────────────────
        strip_row = QWidget(); srl = QHBoxLayout(strip_row)
        srl.setContentsMargins(0, 0, 0, 0); srl.setSpacing(8)

        self._sc_strip = QListWidget()
        self._sc_strip.setViewMode(QListWidget.ViewMode.IconMode)
        self._sc_strip.setFlow(QListWidget.Flow.LeftToRight)
        self._sc_strip.setWrapping(False)
        self._sc_strip.setMovement(QListWidget.Movement.Snap)
        self._sc_strip.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._sc_strip.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._sc_strip.setIconSize(QSize(70, 90))
        self._sc_strip.setGridSize(QSize(86, 128))
        self._sc_strip.setFixedHeight(140)
        self._sc_strip.setSpacing(2)
        self._sc_strip.setUniformItemSizes(True)
        self._sc_strip.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._sc_strip.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._sc_strip.setStyleSheet(f"""
            QListWidget {{ background:{CARD}; border:none; border-radius:4px;
                           color:{FG}; font-size:9pt; outline:none; padding:6px; }}
            QListWidget::item {{ padding:4px; border-radius:4px; }}
            QListWidget::item:selected {{ background:{ACCENT}; color:white; }}
        """)
        self._sc_strip.itemSelectionChanged.connect(self._sc_select_changed)
        # Re-number after drag-reorder:
        self._sc_strip.model().rowsMoved.connect(lambda *a: self._sc_renumber())

        add_btn = QPushButton("＋\nAdd")
        add_btn.setFixedSize(80, 128)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; color:{FG2}; font-size:13pt;
                           border:1px dashed {BORDER}; border-radius:4px; }}
            QPushButton:hover {{ color:{FG}; border-color:{ACCENT}; }}
        """)
        add_btn.clicked.connect(self._sc_pick_files)

        srl.addWidget(self._sc_strip, 1); srl.addWidget(add_btn)
        lay.addWidget(strip_row)

        # ── Controls row ──────────────────────────────────────────────────────
        lay.addWidget(_vspace(10))
        ctrl = QWidget(); cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(12)

        reset_btn = _secondary("Reset Corners")
        reset_btn.clicked.connect(self._sc_crop.reset_corners)
        del_btn = _secondary("Delete Page")
        del_btn.clicked.connect(self._sc_delete_page)
        cl.addWidget(reset_btn); cl.addWidget(del_btn); cl.addSpacing(20)

        cl.addWidget(QLabel("Output size:"))
        self._sc_size = QComboBox()
        self._sc_size.addItems(["Auto (from selection)", "A4 (210×297 mm)", "Letter (8.5×11 in)"])
        self._sc_size.setStyleSheet(f"""
            QComboBox {{ background:{CARD2}; color:{FG}; border:none; padding:6px 10px;
                         border-radius:4px; font-size:10pt; min-width:180px; }}
            QComboBox::drop-down {{ border:none; width:24px; }}
            QComboBox QAbstractItemView {{ background:{CARD2}; color:{FG};
                                           selection-background-color:{ACCENT}; border:none; }}
        """)
        cl.addWidget(self._sc_size)

        self._sc_gray = QCheckBox("Grayscale")
        self._sc_gray.setStyleSheet(f"""
            QCheckBox {{ color:{FG}; spacing:6px; font-size:10pt; }}
            QCheckBox::indicator {{ width:16px; height:16px; border-radius:3px;
                                    border:2px solid {BORDER}; background:{CARD}; }}
            QCheckBox::indicator:checked {{ background:{ACCENT}; border-color:{ACCENT}; }}
        """)
        cl.addWidget(self._sc_gray); cl.addStretch()
        lay.addWidget(ctrl)

        # ── Save path ─────────────────────────────────────────────────────────
        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(10))
        lay.addWidget(_section("SAVE AS")); lay.addWidget(_vspace(6))
        of = QWidget(); ol = QHBoxLayout(of); ol.setContentsMargins(0,0,0,0); ol.setSpacing(8)
        self._sc_out = QLineEdit(); self._sc_out.setReadOnly(True)
        self._sc_out.setPlaceholderText("Choose save location…")
        br2 = _secondary("Browse"); br2.clicked.connect(self._sc_browse)
        ol.addWidget(self._sc_out, 1); ol.addWidget(br2)
        lay.addWidget(of)

        lay.addWidget(_vspace(8)); lay.addWidget(_divider()); lay.addWidget(_vspace(10))
        self._sc_btn = _primary("Convert to PDF"); self._sc_btn.clicked.connect(self._sc_run)
        lay.addWidget(self._sc_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(_vspace(4))
        self._sc_prog = ProgBar(); lay.addWidget(self._sc_prog)

        if not _CV2:
            warn = QLabel("⚠  opencv-python not installed — run:  pip install opencv-python")
            warn.setStyleSheet(f"color:{RED}; font-size:10pt; padding:4px 0;")
            lay.addWidget(warn)

        return page

    # ── helpers ─────────────────────────────────────────────────────────────
    def _sc_pick_files(self):
        exts = "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp);;All Files (*)"
        paths, _ = QFileDialog.getOpenFileNames(self, "Add images", filter=exts)
        if paths: self._sc_add_paths(paths)

    def _sc_add_paths(self, paths):
        """Append new image pages to the strip (with thumbnails)."""
        for path in paths:
            pix = QPixmap(path)
            if pix.isNull(): continue
            thumb = pix.scaled(70, 90, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            item = QListWidgetItem(QIcon(thumb), "")
            item.setData(Qt.ItemDataRole.UserRole, {"path": path, "corners": None})
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sc_strip.addItem(item)

        self._sc_renumber()

        # Auto-select first page so editor isn't blank
        if self._sc_strip.count() and self._sc_cur_item is None:
            self._sc_strip.setCurrentRow(0)

        # Default save path = first image's folder + name
        if not self._sc_out.text() and paths:
            base = os.path.splitext(paths[0])[0]
            self._sc_out.setText(base + "_scan.pdf")

    def _sc_renumber(self):
        for i in range(self._sc_strip.count()):
            self._sc_strip.item(i).setText(f"Page {i+1}")

    def _sc_save_current_corners(self):
        """Persist the crop widget's corners back onto the currently-edited item."""
        if self._sc_cur_item is None: return
        corners = self._sc_crop.image_corners_px()
        if not corners or len(corners) != 4: return
        data = self._sc_cur_item.data(Qt.ItemDataRole.UserRole) or {}
        data["corners"] = corners
        self._sc_cur_item.setData(Qt.ItemDataRole.UserRole, data)

    def _sc_select_changed(self):
        new_item = self._sc_strip.currentItem()
        if new_item is self._sc_cur_item: return

        # Save previous item's corners before switching
        self._sc_save_current_corners()

        if new_item is not None:
            data = new_item.data(Qt.ItemDataRole.UserRole) or {}
            self._sc_crop.load(data["path"])
            if data.get("corners"):
                self._sc_crop.set_image_corners_px(data["corners"])
        else:
            self._sc_crop.clear()

        self._sc_cur_item = new_item

    def _sc_delete_page(self):
        item = self._sc_strip.currentItem()
        if item is None: return
        row = self._sc_strip.row(item)
        was_current = (item is self._sc_cur_item)
        self._sc_strip.takeItem(row)
        self._sc_renumber()
        if was_current: self._sc_cur_item = None
        cnt = self._sc_strip.count()
        if cnt:
            self._sc_strip.setCurrentRow(min(row, cnt-1))
        else:
            self._sc_crop.clear(); self._sc_cur_item = None

    def _sc_browse(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save PDF as",
                   filter="PDF Files (*.pdf)")
        if p: self._sc_out.setText(p if p.endswith(".pdf") else p+".pdf")

    def _sc_run(self):
        if self._sc_strip.count() == 0:
            QMessageBox.warning(self, "No images",
                "Click + Add to load at least one image."); return

        # Save the current page's corners before collecting all
        self._sc_save_current_corners()

        # Collect every page in display order
        pages = []
        for i in range(self._sc_strip.count()):
            data = self._sc_strip.item(i).data(Qt.ItemDataRole.UserRole) or {}
            corners = data.get("corners")
            if not corners or len(corners) != 4:
                QMessageBox.warning(self, "Missing corners",
                    f"Page {i+1} doesn't have all 4 corners placed."); return
            pages.append((data["path"], corners))

        out = self._sc_out.text()
        if not out:
            QMessageBox.warning(self, "No output", "Choose where to save."); return

        size_txt = self._sc_size.currentText()
        out_size = "A4" if "A4" in size_txt else "Letter" if "Letter" in size_txt else "Auto"
        grayscale = self._sc_gray.isChecked()

        self._sc_btn.setDisabled(True); self._sc_btn.setText("Converting…")
        self._sc_prog.working(f"Processing {len(pages)} page{'s' if len(pages)>1 else ''}…")

        def _cb(done, total, name):
            self._post(self._sc_prog.step, done, total, f"Page {done}/{total}  —  {name}")

        def _ok(res):
            out_path, n = res
            self._sc_prog.done(
                f"Saved  {os.path.basename(out_path)}  ({n} page{'s' if n>1 else ''})",
                out_path)
            self._sc_btn.setDisabled(False); self._sc_btn.setText("Convert to PDF")
            self._sb.showMessage(f"Scan saved → {os.path.basename(out_path)}")
        def _err(e):
            self._sc_prog.error(str(e))
            self._sc_btn.setDisabled(False); self._sc_btn.setText("Convert to PDF")
            QMessageBox.critical(self, "Conversion failed", str(e))

        self._run_bg(
            lambda: do_scan_pages_to_pdf(pages, out, out_size, grayscale, _cb),
            _ok, _err)



# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Tool")
    app.setStyleSheet(QSS)
    win = App()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
