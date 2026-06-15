import { useEffect, useState } from 'react'
import { Button } from './Button'
import { DropZone } from './DropZone'
import { FileBadge } from './FileBadge'
import { Progress, ProgressState } from './Progress'
import { RadioPills } from './RadioPills'
import { SectionLabel } from './SectionLabel'
import { compressPdf, PdfMeta, readPdfMeta } from '../lib/pdf'
import { useTabDirty } from '../lib/dirtyContext'
import { downloadBlob, fmtSize, stem } from '../lib/utils'

type CompressionLevel = 'small' | 'balanced' | 'quality'

const PRESETS: Record<
  CompressionLevel,
  { dpi: number; quality: number; description: string }
> = {
  small: {
    dpi: 72,
    quality: 0.55,
    description: '72 dpi · smallest files for email and on-screen viewing',
  },
  balanced: {
    dpi: 150,
    quality: 0.72,
    description: '150 dpi · recommended balance of size and readability',
  },
  quality: {
    dpi: 220,
    quality: 0.84,
    description: '220 dpi · sharper output for printing',
  },
}

interface Props {
  setStatus: (s: string) => void
}

export function CompressTab({ setStatus }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [meta, setMeta] = useState<PdfMeta | null>(null)
  const [level, setLevel] = useState<CompressionLevel>('balanced')
  const [progress, setProgress] = useState<ProgressState>({ kind: 'idle' })
  const [running, setRunning] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setSaved(false)
  }, [file, level])

  useTabDirty(
    'compress',
    file !== null && !saved,
    `You have a PDF loaded that hasn't been compressed and saved yet.`,
  )

  const loadFile = async (nextFile: File) => {
    setFile(nextFile)
    setMeta(null)
    setProgress({ kind: 'idle' })
    try {
      const nextMeta = await readPdfMeta(nextFile)
      setMeta(nextMeta)
      setStatus(`Loaded  ${nextFile.name}  (${nextMeta.pages} pages)`)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Failed to read PDF')
    }
  }

  const run = async () => {
    if (!file || !meta) return
    setRunning(true)
    setProgress({ kind: 'working', label: 'Preparing pages…' })

    try {
      const preset = PRESETS[level]
      const bytes = await compressPdf(
        file,
        preset,
        (done, total, label) =>
          setProgress({ kind: 'progress', done, total, label }),
      )
      const filename = `${stem(file.name)}_compressed.pdf`
      await downloadBlob(bytes, filename, 'application/pdf')

      const difference = file.size - bytes.byteLength
      const percent = file.size > 0 ? Math.abs(difference / file.size) * 100 : 0
      const comparison =
        difference > 0
          ? `${percent.toFixed(1)}% smaller`
          : 'no reduction available'

      setProgress({
        kind: 'done',
        label: `${fmtSize(file.size)} → ${fmtSize(bytes.byteLength)} (${comparison})`,
      })
      setStatus(`Compressed → ${filename}`)
      setSaved(true)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Compression failed')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
      {!file ? (
        <DropZone
          label="Choose a PDF to compress"
          onFiles={files => loadFile(files[0])}
        />
      ) : (
        <FileBadge
          name={file.name}
          pages={meta?.pages}
          size={meta?.size ?? file.size}
          onClear={() => {
            setFile(null)
            setMeta(null)
            setProgress({ kind: 'idle' })
          }}
        />
      )}

      <div className="h-px bg-rule" />

      <div className="space-y-3">
        <SectionLabel>Compression level</SectionLabel>
        <div className="overflow-x-auto -mx-1 px-1">
          <RadioPills
            value={level}
            onChange={setLevel}
            ariaLabel="Compression level"
            options={[
              { value: 'small', label: 'Smallest' },
              { value: 'balanced', label: 'Balanced' },
              { value: 'quality', label: 'High quality' },
            ]}
          />
        </div>
        <div className="text-[12px] text-stone-soft">
          {PRESETS[level].description}
        </div>
      </div>

      <div className="rounded-md border border-rule bg-panel px-3.5 py-3 text-[11.5px] leading-relaxed text-stone">
        Compression flattens each page into an image. Selectable text, links,
        form fields, and other interactive content will not be preserved.
        Image-heavy and scanned PDFs usually shrink the most. If flattening
        would make the file larger, the original PDF is saved unchanged.
      </div>

      <div className="h-px bg-rule" />

      <div className="flex flex-col items-center gap-4 pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={run}
          disabled={!file || !meta || running}
          className="w-full sm:w-auto"
        >
          {running ? 'Compressing…' : 'Compress PDF'}
        </Button>
        <div className="w-full">
          <Progress state={progress} />
        </div>
      </div>
    </div>
  )
}
