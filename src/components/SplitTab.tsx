import { useEffect, useState } from 'react'
import { DropZone } from './DropZone'
import { FileBadge } from './FileBadge'
import { SectionLabel } from './SectionLabel'
import { Stepper } from './Stepper'
import { RadioPills } from './RadioPills'
import { TextField } from './TextField'
import { Button } from './Button'
import { Progress, ProgressState } from './Progress'
import { PdfMeta, readPdfMeta, splitPdf, zipFiles, parsePageSpec } from '../lib/pdf'
import { downloadBlob, stem } from '../lib/utils'
import { useTabDirty } from '../lib/dirtyContext'

type Mode = 'pages' | 'parts' | 'custom'

interface Props {
  setStatus: (s: string) => void
}

export function SplitTab({ setStatus }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [meta, setMeta] = useState<PdfMeta | null>(null)
  const [mode, setMode] = useState<Mode>('pages')
  const [pagesPerChunk, setPagesPerChunk] = useState(1)
  const [numParts, setNumParts] = useState(2)
  const [spec, setSpec] = useState('')
  const [progress, setProgress] = useState<ProgressState>({ kind: 'idle' })
  const [running, setRunning] = useState(false)
  const [saved, setSaved] = useState(false)

  // Any change that invalidates the previously-saved split.
  useEffect(() => {
    setSaved(false)
  }, [file, mode, pagesPerChunk, numParts, spec])

  useTabDirty(
    'split',
    file !== null && !saved,
    `You have a PDF loaded that hasn't been split and saved yet.`,
  )

  const loadFile = async (f: File) => {
    setFile(f); setMeta(null); setProgress({ kind: 'idle' })
    try {
      const m = await readPdfMeta(f)
      setMeta(m)
      setStatus(`Loaded  ${f.name}  (${m.pages} pages)`)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Failed to read PDF')
    }
  }

  const customValid =
    mode !== 'custom' || (meta != null && parsePageSpec(spec, meta.pages).length > 0)

  const canRun = !!file && !!meta && customValid && !running

  const run = async () => {
    if (!file) return
    setRunning(true)
    setProgress({ kind: 'working', label: 'Preparing…' })
    try {
      const out = await splitPdf(
        file,
        mode === 'pages' ? { mode: 'pages', pagesPerChunk } :
        mode === 'parts' ? { mode: 'parts', numParts } :
        { mode: 'custom', spec },
        (done, total, name) =>
          setProgress({ kind: 'progress', done, total, label: name }),
      )
      if (out.length === 1) {
        downloadBlob(out[0].bytes, out[0].filename, 'application/pdf')
        setProgress({ kind: 'done', label: `Saved ${out[0].filename}` })
        setStatus(`Split complete — 1 file downloaded`)
      } else {
        setProgress({ kind: 'working', label: `Packaging ${out.length} files…` })
        const zip = await zipFiles(out)
        const zipName = `${stem(file.name)}_split.zip`
        downloadBlob(zip, zipName, 'application/zip')
        setProgress({ kind: 'done', label: `Saved ${out.length} files as ${zipName}` })
        setStatus(`Split complete — ${out.length} files in ${zipName}`)
      }
      setSaved(true)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Split failed')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
      {!file ? (
        <DropZone
          label="Choose a PDF to split"
          onFiles={files => loadFile(files[0])}
        />
      ) : (
        <FileBadge
          name={file.name}
          pages={meta?.pages}
          size={meta?.size ?? file.size}
          onClear={() => {
            setFile(null); setMeta(null); setProgress({ kind: 'idle' })
          }}
        />
      )}

      <div className="h-px bg-rule" />

      <div className="space-y-3">
        <SectionLabel>Split mode</SectionLabel>
        <div className="overflow-x-auto -mx-1 px-1">
          <RadioPills
            value={mode}
            onChange={setMode}
            ariaLabel="Split mode"
            options={[
              { value: 'pages', label: 'Pages per chunk' },
              { value: 'parts', label: 'Equal parts' },
              { value: 'custom', label: 'Custom page list' },
            ]}
          />
        </div>

        <div className="pt-2">
          {mode === 'pages' && (
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-[12.5px] text-stone-soft">Each file contains</span>
              <Stepper value={pagesPerChunk} onChange={setPagesPerChunk} min={1} max={meta?.pages ?? 9999} ariaLabel="Pages per chunk" />
              <span className="text-[12.5px] text-stone-soft">page(s)</span>
            </div>
          )}
          {mode === 'parts' && (
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-[12.5px] text-stone-soft">Split into</span>
              <Stepper value={numParts} onChange={setNumParts} min={2} max={meta?.pages ?? 9999} ariaLabel="Number of parts" />
              <span className="text-[12.5px] text-stone-soft">equal parts</span>
            </div>
          )}
          {mode === 'custom' && (
            <div className="space-y-1.5">
              <TextField
                value={spec}
                onChange={e => setSpec(e.target.value)}
                placeholder="e.g.  1, 3, 5-10, 15"
                mono
                className="w-full sm:w-80"
              />
              <div className="text-[11px] text-stone">
                {meta && spec
                  ? `${parsePageSpec(spec, meta.pages).length} page(s) selected of ${meta.pages}`
                  : 'Comma-separated pages and ranges'}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="h-px bg-rule" />

      <div className="flex flex-col items-center gap-4 pt-2">
        <Button variant="primary" size="lg" onClick={run} disabled={!canRun} className="w-full sm:w-auto">
          {running ? 'Splitting…' : 'Split PDF'}
        </Button>
        <div className="w-full">
          <Progress state={progress} />
        </div>
      </div>

      <div className="text-[11px] text-stone text-center pt-2">
        Single file → direct download · Multiple files → packaged as ZIP
      </div>
    </div>
  )
}
