import { PDFDocument } from 'pdf-lib'
import * as pdfjsLib from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url'
import JSZip from 'jszip'
import { stem } from './utils'

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl

export interface PdfMeta {
  pages: number
  size: number
}

export async function readPdfMeta(file: File): Promise<PdfMeta> {
  const buf = await file.arrayBuffer()
  const doc = await PDFDocument.load(buf, { ignoreEncryption: true })
  return { pages: doc.getPageCount(), size: file.size }
}

export type SplitOptions =
  | { mode: 'pages'; pagesPerChunk: number }
  | { mode: 'parts'; numParts: number }
  | { mode: 'custom'; spec: string }

export interface SplitOutput {
  filename: string
  bytes: Uint8Array
}

export function parsePageSpec(spec: string, total: number): number[] {
  const pages = new Set<number>()
  for (const part of spec.replace(/\s/g, '').split(',')) {
    if (!part) continue
    if (part.includes('-')) {
      const [aStr, bStr] = part.split('-', 2)
      const a = Number(aStr)
      const b = Number(bStr)
      if (Number.isFinite(a) && Number.isFinite(b)) {
        for (let i = a - 1; i < b; i++) pages.add(i)
      }
    } else {
      const n = Number(part)
      if (Number.isFinite(n)) pages.add(n - 1)
    }
  }
  return [...pages].filter(x => x >= 0 && x < total).sort((a, b) => a - b)
}

export async function splitPdf(
  file: File,
  options: SplitOptions,
  onProgress?: (done: number, total: number, filename: string) => void,
): Promise<SplitOutput[]> {
  const buf = await file.arrayBuffer()
  const src = await PDFDocument.load(buf, { ignoreEncryption: true })
  const total = src.getPageCount()
  const name = stem(file.name)
  const out: SplitOutput[] = []

  if (options.mode === 'custom') {
    const idx = parsePageSpec(options.spec, total)
    if (idx.length === 0) throw new Error('No valid pages in the custom spec.')
    const doc = await PDFDocument.create()
    const pages = await doc.copyPages(src, idx)
    pages.forEach(p => doc.addPage(p))
    const bytes = await doc.save()
    const filename = `${name}_custom_${idx.length}pages.pdf`
    out.push({ filename, bytes })
    onProgress?.(1, 1, filename)
    return out
  }

  const chunkSize =
    options.mode === 'pages'
      ? Math.max(1, options.pagesPerChunk)
      : Math.ceil(total / Math.max(1, options.numParts))
  const numChunks = Math.ceil(total / chunkSize)

  let n = 0
  let s = 0
  while (s < total) {
    n++
    const e = Math.min(s + chunkSize, total)
    const doc = await PDFDocument.create()
    const indices = Array.from({ length: e - s }, (_, i) => s + i)
    const pages = await doc.copyPages(src, indices)
    pages.forEach(p => doc.addPage(p))
    const bytes = await doc.save()
    const filename = `${name}_part${String(n).padStart(3, '0')}_p${s + 1}-${e}.pdf`
    out.push({ filename, bytes })
    onProgress?.(n, numChunks, filename)
    s = e
    // yield to UI
    await new Promise(r => setTimeout(r, 0))
  }
  return out
}

export async function mergePdfs(
  files: File[],
  onProgress?: (done: number, total: number, filename: string) => void,
): Promise<{ bytes: Uint8Array; totalPages: number }> {
  const merged = await PDFDocument.create()
  let totalPages = 0
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const buf = await file.arrayBuffer()
    const src = await PDFDocument.load(buf, { ignoreEncryption: true })
    const indices = src.getPageIndices()
    const pages = await merged.copyPages(src, indices)
    pages.forEach(p => merged.addPage(p))
    totalPages += indices.length
    onProgress?.(i + 1, files.length, file.name)
    await new Promise(r => setTimeout(r, 0))
  }
  const bytes = await merged.save()
  return { bytes, totalPages }
}

export interface CompressOptions {
  dpi: number
  quality: number
  maxPixels?: number
}

export async function compressPdf(
  file: File,
  options: CompressOptions,
  onProgress?: (done: number, total: number, label: string) => void,
): Promise<Uint8Array> {
  const original = new Uint8Array(await file.arrayBuffer())
  const loadingTask = pdfjsLib.getDocument({ data: original.slice() })
  const source = await loadingTask.promise
  const output = await PDFDocument.create()
  const maxPixels = options.maxPixels ?? 16_000_000

  try {
    for (let pageNumber = 1; pageNumber <= source.numPages; pageNumber++) {
      const sourcePage = await source.getPage(pageNumber)
      const baseViewport = sourcePage.getViewport({ scale: 1 })
      let scale = Math.max(0.1, options.dpi / 72)
      let renderViewport = sourcePage.getViewport({ scale })
      const requestedPixels = renderViewport.width * renderViewport.height

      if (requestedPixels > maxPixels) {
        scale *= Math.sqrt(maxPixels / requestedPixels)
        renderViewport = sourcePage.getViewport({ scale })
      }

      const canvas = document.createElement('canvas')
      canvas.width = Math.max(1, Math.round(renderViewport.width))
      canvas.height = Math.max(1, Math.round(renderViewport.height))
      const context = canvas.getContext('2d', { alpha: false })
      if (!context) throw new Error('Canvas rendering is unavailable in this browser.')

      context.fillStyle = '#ffffff'
      context.fillRect(0, 0, canvas.width, canvas.height)
      await sourcePage.render({
        canvasContext: context,
        viewport: renderViewport,
        background: '#ffffff',
      }).promise

      const jpeg = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          blob => blob ? resolve(blob) : reject(new Error(`Failed to encode page ${pageNumber}.`)),
          'image/jpeg',
          options.quality,
        )
      })
      const image = await output.embedJpg(await jpeg.arrayBuffer())
      const outputPage = output.addPage([baseViewport.width, baseViewport.height])
      outputPage.drawImage(image, {
        x: 0,
        y: 0,
        width: baseViewport.width,
        height: baseViewport.height,
      })

      sourcePage.cleanup()
      canvas.width = 1
      canvas.height = 1
      onProgress?.(pageNumber, source.numPages, `Compressed page ${pageNumber}/${source.numPages}`)
      await new Promise(resolve => setTimeout(resolve, 0))
    }

    const compressed = await output.save({ useObjectStreams: true })
    return compressed.byteLength < original.byteLength ? compressed : original
  } finally {
    await source.destroy()
  }
}

export async function* extractText(
  file: File,
  startPage: number,
  endPage: number,
): AsyncGenerator<{ page: number; text: string; totalPages: number }> {
  const buf = await file.arrayBuffer()
  const pdf = await pdfjsLib.getDocument({ data: buf }).promise
  const total = pdf.numPages
  const start = Math.max(1, startPage)
  const end = Math.min(total, endPage)
  for (let i = start; i <= end; i++) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    let last: { x: number; y: number } | null = null
    let text = ''
    for (const item of content.items as Array<{
      str: string
      transform: number[]
      hasEOL?: boolean
    }>) {
      const x = item.transform[4]
      const y = item.transform[5]
      if (last && Math.abs(y - last.y) > 4) text += '\n'
      else if (last && x - last.x > 12 && !text.endsWith(' ')) text += ' '
      text += item.str
      if (item.hasEOL) text += '\n'
      last = { x: x + (item.str.length * 4), y }
    }
    yield { page: i, text: text.trim(), totalPages: total }
  }
}

export async function zipFiles(files: SplitOutput[]): Promise<Blob> {
  const zip = new JSZip()
  for (const f of files) zip.file(f.filename, f.bytes)
  return zip.generateAsync({ type: 'blob', compression: 'DEFLATE', compressionOptions: { level: 6 } })
}
