# PDF Tool

A cross-platform PDF utility with an Anthropic/Claude-inspired UI. Split, merge, extract text, compress, and scan photos into PDFs — from the web, iOS, Android, or your desktop.

## Features

- **Split** — break a PDF into pages or custom ranges
- **Merge** — combine multiple PDFs with drag-and-drop reordering
- **Extract Text** — pull text out of any PDF
- **Compress** — reduce image-heavy PDFs with selectable size/quality presets
- **Photos → PDF** — scan documents from your camera/photo library, with corner-point perspective warp for clean output

## Platforms

| Platform | Stack |
|----------|-------|
| Web      | React 18 + Vite + TypeScript + Tailwind CSS v4 |
| iOS      | Capacitor wrapper (native camera, file save, share) |
| Android  | Capacitor wrapper (native camera, file save, share) |
| Desktop  | Python + Tkinter (`pdf_tool.py`) — the original |

## Getting started (web)

```bash
npm install
npm run dev
```

Then open the URL Vite prints (typically `http://localhost:5173`).

### Build for production

```bash
npm run build
npm run preview
```

## Mobile (Capacitor)

After building the web app, sync the native projects:

```bash
npm run build
npx cap sync
```

Then open in Xcode or Android Studio:

```bash
npx cap open ios
npx cap open android
```

The iOS and Android shells use:
- `@capacitor/camera` — native camera and photo picker
- `@capacitor/filesystem` — save PDFs to device storage
- `@capacitor/share` — share PDFs via the OS share sheet

## Desktop (Python)

The original Tkinter app lives at `pdf_tool.py` and supports the same Split / Merge / Extract operations.

```bash
pip install pypdf tkinterdnd2
python pdf_tool.py
```

`tkinterdnd2` is optional — without it, drag-and-drop is disabled but file pickers still work.

## Project structure

```
.
├── src/
│   ├── App.tsx                 # Tab shell + dirty-state guard
│   ├── components/             # SplitTab, MergeTab, ExtractTab, ScanTab, ...
│   └── lib/
│       ├── pdf.ts              # pdf-lib + pdfjs-dist helpers
│       ├── imagesToPdf.ts      # Photos → PDF pipeline
│       ├── imageWarp.ts        # Corner-point perspective warp
│       └── native.ts           # Capacitor bridge (camera, save, share)
├── ios/                        # Capacitor iOS project
├── android/                    # Capacitor Android project
├── pdf_tool.py                 # Original Tkinter desktop app
├── capacitor.config.ts
├── vite.config.ts
└── package.json
```

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — type-check and build for production
- `npm run preview` — preview the production build locally
- `npm run typecheck` — TypeScript check without emitting files

## Tech notes

- PDF parsing and rendering use [`pdfjs-dist`](https://github.com/mozilla/pdf.js); PDF creation/editing uses [`pdf-lib`](https://github.com/Hopding/pdf-lib).
- Drag-and-drop reordering in the Merge tab is powered by [`@dnd-kit`](https://dndkit.com/).
- The UI is built on Tailwind v4 with a custom dark color palette (coral accent, warm off-white text).
