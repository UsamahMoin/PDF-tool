import { ReactNode, useEffect, useMemo, useRef, useState } from 'react'
import { DropZone } from './DropZone'
import { FileBadge } from './FileBadge'
import { SectionLabel } from './SectionLabel'
import { Stepper } from './Stepper'
import { Button } from './Button'
import { TextField } from './TextField'
import { Progress, ProgressState } from './Progress'
import { extractText, PdfMeta, readPdfMeta } from '../lib/pdf'
import { downloadBlob, stem } from '../lib/utils'
import { useTabDirty } from '../lib/dirtyContext'

interface PageText {
  page: number
  text: string
}

interface Props {
  setStatus: (s: string) => void
}

export function ExtractTab({ setStatus }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [meta, setMeta] = useState<PdfMeta | null>(null)
  const [from, setFrom] = useState(1)
  const [to, setTo] = useState(9999)
  const [pages, setPages] = useState<PageText[]>([])
  const [progress, setProgress] = useState<ProgressState>({ kind: 'idle' })
  const [running, setRunning] = useState(false)
  const [find, setFind] = useState('')
  const [matchIdx, setMatchIdx] = useState(0)
  const [copyHint, setCopyHint] = useState('')
  const [savedOrCopied, setSavedOrCopied] = useState(false)

  // A new extraction invalidates the "saved/copied" state.
  useEffect(() => {
    setSavedOrCopied(false)
  }, [pages])

  useTabDirty(
    'extract',
    pages.length > 0 && !savedOrCopied,
    `You have extracted text that hasn't been copied or saved yet.`,
  )

  const scrollRef = useRef<HTMLDivElement>(null)
  const cancelRef = useRef(false)

  const loadFile = async (f: File) => {
    setFile(f); setMeta(null); setPages([])
    setProgress({ kind: 'idle' }); setFind('')
    try {
      const m = await readPdfMeta(f)
      setMeta(m); setFrom(1); setTo(m.pages)
      setStatus(`Loaded  ${f.name}  (${m.pages} pages)`)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Failed to read PDF')
    }
  }

  const run = async () => {
    if (!file || !meta) return
    cancelRef.current = false
    setRunning(true); setPages([])
    setProgress({ kind: 'working', label: 'Extracting…' })

    try {
      const start = Math.max(1, from)
      const end = Math.min(meta.pages, to)
      let count = 0
      const total = Math.max(1, end - start + 1)
      for await (const p of extractText(file, start, end)) {
        if (cancelRef.current) break
        count++
        setPages(prev => [...prev, { page: p.page, text: p.text }])
        setProgress({ kind: 'progress', done: count, total, label: `Page ${p.page}` })
      }
      setProgress({ kind: 'done', label: `Extracted ${count} page${count === 1 ? '' : 's'}` })
      setStatus('Extraction complete')
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Extract failed')
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => () => { cancelRef.current = true }, [])

  const allText = useMemo(
    () => pages.map(p => `Page ${p.page}\n${'─'.repeat(44)}\n${p.text}`).join('\n\n'),
    [pages],
  )

  const matches = useMemo(() => {
    if (!find.trim()) return []
    const q = find.toLowerCase()
    const m: { page: number; pos: number; len: number }[] = []
    for (const p of pages) {
      const hay = p.text.toLowerCase()
      let i = hay.indexOf(q)
      while (i !== -1) {
        m.push({ page: p.page, pos: i, len: find.length })
        i = hay.indexOf(q, i + Math.max(1, find.length))
      }
    }
    return m
  }, [find, pages])

  useEffect(() => { setMatchIdx(0) }, [find])

  useEffect(() => {
    if (!matches.length || !scrollRef.current) return
    const m = matches[matchIdx]
    if (!m) return
    const el = scrollRef.current.querySelector(
      `[data-page="${m.page}"]`,
    ) as HTMLElement | null
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [matchIdx, matches])

  const copyAll = async () => {
    if (!allText.trim()) return
    await navigator.clipboard.writeText(allText)
    setCopyHint('Copied to clipboard')
    setSavedOrCopied(true)
    setTimeout(() => setCopyHint(''), 2000)
  }

  const saveTxt = () => {
    if (!allText.trim() || !file) return
    downloadBlob(allText, `${stem(file.name)}.txt`, 'text/plain;charset=utf-8')
    setCopyHint(`Saved ${stem(file.name)}.txt`)
    setSavedOrCopied(true)
    setTimeout(() => setCopyHint(''), 2000)
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6 flex flex-col h-full">
      {!file ? (
        <DropZone
          label="Choose a PDF to extract text from"
          onFiles={files => loadFile(files[0])}
        />
      ) : (
        <FileBadge
          name={file.name}
          pages={meta?.pages}
          size={meta?.size ?? file.size}
          onClear={() => {
            cancelRef.current = true
            setFile(null); setMeta(null); setPages([])
            setProgress({ kind: 'idle' }); setFind('')
          }}
        />
      )}

      <div className="h-px bg-rule" />

      <div className="space-y-3">
        <SectionLabel>Page range</SectionLabel>
        <div className="flex items-center flex-wrap gap-3">
          <span className="text-[12.5px] text-stone-soft">From</span>
          <Stepper value={from} onChange={setFrom} min={1} max={meta?.pages ?? 9999} ariaLabel="From page" />
          <span className="text-[12.5px] text-stone-soft">to</span>
          <Stepper value={meta ? Math.min(to, meta.pages) : to} onChange={setTo} min={1} max={meta?.pages ?? 9999} ariaLabel="To page" />
          {meta && <span className="text-[11px] text-stone">of {meta.pages}</span>}
          <Button variant="primary" onClick={run} disabled={!file || !meta || running} className="ml-auto w-full sm:w-auto">
            {running ? 'Extracting…' : 'Extract Text'}
          </Button>
        </div>
        <Progress state={progress} />
      </div>

      <div className="h-px bg-rule" />

      <div className="flex flex-col flex-1 min-h-0 gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <SectionLabel className="mb-0 mr-auto">Extracted text</SectionLabel>
          <div className="relative flex-1 sm:flex-none min-w-[10rem]">
            <TextField
              value={find}
              onChange={e => setFind(e.target.value)}
              placeholder="Find in text…"
              className="w-full sm:w-56 pl-8"
            />
            <svg className="absolute left-2.5 top-2.5 text-stone" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="7" cy="7" r="5" />
              <path d="M11 11l3 3" strokeLinecap="round" />
            </svg>
          </div>
          {find && (
            <div className="text-[11px] text-stone tabular-nums">
              {matches.length === 0 ? 'No matches' : `${matchIdx + 1} / ${matches.length}`}
            </div>
          )}
          <Button
            variant="secondary"
            size="sm"
            disabled={matches.length === 0}
            onClick={() => setMatchIdx(i => (i - 1 + matches.length) % Math.max(1, matches.length))}
          >
            Prev
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={matches.length === 0}
            onClick={() => setMatchIdx(i => (i + 1) % Math.max(1, matches.length))}
          >
            Next
          </Button>
        </div>

        <div
          ref={scrollRef}
          className="flex-1 min-h-[200px] overflow-y-auto bg-panel rounded-md border border-rule p-4 font-mono text-[12.5px] leading-relaxed"
        >
          {pages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-stone text-[12px] font-sans">
              {running ? 'Working…' : 'Extracted text will appear here.'}
            </div>
          ) : (
            pages.map(p => {
              const pageMatches = matches
                .map((m, gi) => ({ ...m, globalIndex: gi }))
                .filter(m => m.page === p.page)
              return (
                <div key={p.page} data-page={p.page} className="mb-6 last:mb-0">
                  <div className="text-stone-soft text-[11px] font-sans uppercase tracking-wider mb-1.5">
                    Page {p.page}
                  </div>
                  <pre className="whitespace-pre-wrap break-words text-cream font-mono">
                    {renderHighlighted(p.text, find, pageMatches, matchIdx)}
                  </pre>
                </div>
              )
            })
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button onClick={copyAll} disabled={!pages.length}>Copy all</Button>
          <Button onClick={saveTxt} disabled={!pages.length}>Save as .txt</Button>
          {copyHint && <span className="text-[12px] text-success ml-2">{copyHint}</span>}
        </div>
      </div>
    </div>
  )
}

function renderHighlighted(
  text: string,
  query: string,
  pageMatches: { pos: number; len: number; globalIndex: number }[],
  currentGlobalIdx: number,
): ReactNode {
  if (!query.trim() || pageMatches.length === 0) return text
  const parts: ReactNode[] = []
  let cursor = 0
  for (let i = 0; i < pageMatches.length; i++) {
    const m = pageMatches[i]
    if (m.pos > cursor) parts.push(text.slice(cursor, m.pos))
    const isCurrent = m.globalIndex === currentGlobalIdx
    parts.push(
      <mark
        key={`${m.pos}-${i}`}
        className={
          isCurrent
            ? 'bg-coral text-white rounded px-0.5'
            : 'bg-coral/30 text-cream rounded px-0.5'
        }
      >
        {text.slice(m.pos, m.pos + m.len)}
      </mark>,
    )
    cursor = m.pos + m.len
  }
  if (cursor < text.length) parts.push(text.slice(cursor))
  return parts
}
