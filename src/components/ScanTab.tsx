import { ReactNode, useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'

import { DropZone } from './DropZone'
import { SectionLabel } from './SectionLabel'
import { Button } from './Button'
import { Progress, ProgressState } from './Progress'
import { CornerEditor } from './CornerEditor'
import { WarpedPreview } from './WarpedPreview'

import {
  computeWarpedSize,
  defaultQuad,
  warpQuad,
  type Quad,
} from '../lib/imageWarp'
import { canvasToJpeg, imagesToPdf } from '../lib/imagesToPdf'
import { downloadBlob, fmtSize } from '../lib/utils'
import { useTabDirty } from '../lib/dirtyContext'
import { isNative, takePhoto } from '../lib/native'

interface ScanPage {
  id: string
  file: File
  bitmap: ImageBitmap | null
  width: number
  height: number
  quad: Quad
  thumbUrl: string
  loading: boolean
  error?: string
}

interface Props {
  setStatus: (s: string) => void
}

export function ScanTab({ setStatus }: Props) {
  const [pages, setPages] = useState<ScanPage[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [progress, setProgress] = useState<ProgressState>({ kind: 'idle' })
  const [running, setRunning] = useState(false)
  const [saved, setSaved] = useState(false)

  // Pages list (add/remove) and any quad edit invalidates the saved PDF.
  useEffect(() => {
    setSaved(false)
  }, [pages])

  useTabDirty(
    'scan',
    pages.length > 0 && !saved,
    `You have ${pages.length} photo${pages.length === 1 ? '' : 's'} that haven't been built into a PDF yet.`,
  )

  // Cleanup thumbnails on unmount
  useEffect(() => {
    return () => {
      pages.forEach(p => p.thumbUrl && URL.revokeObjectURL(p.thumbUrl))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const active = useMemo(() => pages.find(p => p.id === activeId) ?? null, [pages, activeId])

  const addFiles = async (files: File[]) => {
    const imgFiles = files.filter(f => f.type.startsWith('image/'))
    if (imgFiles.length === 0) return

    const stubs: ScanPage[] = imgFiles.map(f => ({
      id: `${f.name}-${f.size}-${f.lastModified}-${Math.random().toString(36).slice(2, 6)}`,
      file: f,
      bitmap: null,
      width: 0,
      height: 0,
      quad: defaultQuad(1, 1),
      thumbUrl: URL.createObjectURL(f),
      loading: true,
    }))
    setPages(prev => {
      const next = [...prev, ...stubs]
      if (!activeId && next.length > 0) setActiveId(next[0].id)
      return next
    })

    for (const stub of stubs) {
      try {
        const bitmap = await createImageBitmap(stub.file)
        setPages(prev =>
          prev.map(p =>
            p.id === stub.id
              ? {
                  ...p,
                  bitmap,
                  width: bitmap.width,
                  height: bitmap.height,
                  quad: defaultQuad(bitmap.width, bitmap.height),
                  loading: false,
                }
              : p,
          ),
        )
      } catch (e) {
        setPages(prev =>
          prev.map(p =>
            p.id === stub.id ? { ...p, loading: false, error: (e as Error).message } : p,
          ),
        )
      }
    }
  }

  const removePage = (id: string) => {
    setPages(prev => {
      const idx = prev.findIndex(p => p.id === id)
      const next = prev.filter(p => p.id !== id)
      const target = prev[idx]
      if (target) URL.revokeObjectURL(target.thumbUrl)
      if (activeId === id) {
        setActiveId(next[idx]?.id ?? next[idx - 1]?.id ?? next[0]?.id ?? null)
      }
      return next
    })
  }

  const updateActiveQuad = (q: Quad) => {
    if (!activeId) return
    setPages(prev => prev.map(p => (p.id === activeId ? { ...p, quad: q } : p)))
  }

  const resetActiveQuad = () => {
    if (!active || !active.bitmap) return
    updateActiveQuad(defaultQuad(active.bitmap.width, active.bitmap.height))
  }

  const expandActiveQuad = () => {
    if (!active || !active.bitmap) return
    updateActiveQuad([
      { x: 0, y: 0 },
      { x: active.bitmap.width, y: 0 },
      { x: active.bitmap.width, y: active.bitmap.height },
      { x: 0, y: active.bitmap.height },
    ])
  }

  const canBuild = pages.length > 0 && pages.every(p => !p.loading && !p.error && p.bitmap) && !running

  const build = async () => {
    setRunning(true)
    setProgress({ kind: 'working', label: 'Warping images…' })
    try {
      const blobs: Blob[] = []
      for (let i = 0; i < pages.length; i++) {
        const p = pages[i]
        if (!p.bitmap) continue
        const { width, height } = computeWarpedSize(p.quad)
        const canvas = warpQuad(p.bitmap, p.quad, width, height)
        const blob = await canvasToJpeg(canvas, 0.92)
        blobs.push(blob)
        setProgress({
          kind: 'progress',
          done: i + 1,
          total: pages.length + 1,
          label: `Warped page ${i + 1}/${pages.length}`,
        })
      }
      setProgress({ kind: 'working', label: 'Building PDF…' })
      const bytes = await imagesToPdf(blobs, (done, total) =>
        setProgress({
          kind: 'progress',
          done: pages.length + done,
          total: pages.length + total,
          label: `Embedded ${done}/${total}`,
        }),
      )
      const filename = 'scan.pdf'
      downloadBlob(bytes, filename, 'application/pdf')
      setProgress({
        kind: 'done',
        label: `Built ${pages.length}-page PDF (${fmtSize(bytes.byteLength)}) → ${filename}`,
      })
      setStatus(`Scan complete — ${pages.length} pages → ${filename}`)
      setSaved(true)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Scan failed')
    } finally {
      setRunning(false)
    }
  }

  const outputSize = active?.bitmap ? computeWarpedSize(active.quad) : null

  const captureFromCamera = async () => {
    try {
      const file = await takePhoto()
      await addFiles([file])
    } catch (e) {
      // User cancelled or permission denied — silent retry-friendly fail
      const msg = (e as Error).message
      if (msg && !/cancel/i.test(msg)) {
        setStatus(`Camera: ${msg}`)
      }
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 flex flex-col gap-5 h-full min-h-0">
      {isNative && (
        <Button
          variant="primary"
          size="lg"
          onClick={captureFromCamera}
          className="w-full"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
          </svg>
          Take photo
        </Button>
      )}
      <DropZone
        label={isNative ? 'Or pick from photos' : 'Add photos to scan'}
        sublabel={
          isNative
            ? 'JPG, PNG, WebP · pick one or more from your library'
            : 'JPG, PNG, WebP · drag the 4 corners on each image to mark the document edges'
        }
        accept="image/jpeg,image/png,image/webp,image/*"
        multiple
        onFiles={addFiles}
        compact={pages.length > 0}
      />

      {pages.length === 0 ? (
        <div className="text-center text-stone text-[12px] py-6">
          Drop a photo of a document. You'll mark the four corners on each, and
          the app will deskew and bundle them into a single PDF.
        </div>
      ) : (
        <>
          <Thumbnails
            pages={pages}
            activeId={activeId}
            onSelect={setActiveId}
            onRemove={removePage}
          />

          <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-4 flex-1 min-h-0">
            <ScanPane
              title="Mark the corners"
              actions={
                <>
                  <Button variant="ghost" size="sm" onClick={expandActiveQuad} disabled={!active?.bitmap}>
                    Full image
                  </Button>
                  <Button variant="ghost" size="sm" onClick={resetActiveQuad} disabled={!active?.bitmap}>
                    Reset
                  </Button>
                </>
              }
              footer=" "
            >
              {active?.bitmap ? (
                <CornerEditor image={active.bitmap} quad={active.quad} onChange={updateActiveQuad} />
              ) : (
                <Placeholder>
                  {active?.loading ? 'Decoding image…' : active?.error ?? 'Select a photo'}
                </Placeholder>
              )}
            </ScanPane>

            <ScanPane
              title="Preview"
              footer={outputSize ? `Output ${outputSize.width} × ${outputSize.height} px` : ' '}
            >
              {active?.bitmap ? (
                <WarpedPreview image={active.bitmap} quad={active.quad} />
              ) : (
                <Placeholder>{null}</Placeholder>
              )}
            </ScanPane>
          </div>
        </>
      )}

      <div className="h-px bg-rule" />

      <div className="flex flex-col items-center gap-3">
        <Button
          variant="primary"
          size="lg"
          onClick={build}
          disabled={!canBuild}
          className="w-full sm:w-auto"
        >
          {running
            ? 'Building…'
            : pages.length
              ? `Build ${pages.length}-page PDF`
              : 'Build PDF'}
        </Button>
        <div className="w-full">
          <Progress state={progress} />
        </div>
      </div>
    </div>
  )
}

function ScanPane({
  title,
  actions,
  footer,
  children,
}: {
  title: string
  actions?: ReactNode
  footer: ReactNode
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-2 min-h-0">
      <div className="h-7 flex items-center justify-between flex-shrink-0">
        <SectionLabel className="mb-0">{title}</SectionLabel>
        <div className="flex gap-1.5">{actions}</div>
      </div>
      <div className="flex-1 min-h-[280px] sm:min-h-[340px] lg:min-h-[360px]">
        {children}
      </div>
      <div className="h-4 flex items-center justify-center text-[11px] text-stone tabular-nums flex-shrink-0">
        {footer}
      </div>
    </div>
  )
}

function Placeholder({ children }: { children: ReactNode }) {
  return (
    <div className="w-full h-full bg-panel rounded-md border border-rule flex items-center justify-center text-stone text-[12px]">
      {children}
    </div>
  )
}

function Thumbnails({
  pages,
  activeId,
  onSelect,
  onRemove,
}: {
  pages: ScanPage[]
  activeId: string | null
  onSelect: (id: string) => void
  onRemove: (id: string) => void
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
      {pages.map((p, i) => (
        <button
          key={p.id}
          onClick={() => onSelect(p.id)}
          className={clsx(
            'group relative flex-shrink-0 w-16 h-20 sm:w-20 sm:h-24 rounded-md overflow-hidden border-2 transition-all cursor-pointer focus:outline-none',
            p.id === activeId
              ? 'border-coral'
              : 'border-rule hover:border-rule-strong opacity-80 hover:opacity-100',
          )}
        >
          <img src={p.thumbUrl} alt="" className="w-full h-full object-cover" />
          <span className="absolute top-1 left-1 bg-black/70 text-white text-[10px] rounded px-1 tabular-nums">
            {i + 1}
          </span>
          {p.loading && (
            <span className="absolute inset-0 flex items-center justify-center bg-black/40 text-white text-[10px]">
              …
            </span>
          )}
          {p.error && (
            <span className="absolute inset-0 flex items-center justify-center bg-danger/70 text-white text-[10px] p-1 text-center">
              !
            </span>
          )}
          <span
            role="button"
            tabIndex={-1}
            aria-label="Remove"
            onClick={e => {
              e.stopPropagation()
              onRemove(p.id)
            }}
            className="absolute top-0.5 right-0.5 w-5 h-5 rounded-full bg-black/70 text-white text-[11px] leading-none flex items-center justify-center hover:bg-danger transition-colors"
          >
            ×
          </span>
        </button>
      ))}
    </div>
  )
}
