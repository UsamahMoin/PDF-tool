import { useEffect, useState } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import clsx from 'clsx'

import { DropZone } from './DropZone'
import { SectionLabel } from './SectionLabel'
import { Button } from './Button'
import { Progress, ProgressState } from './Progress'
import { mergePdfs, readPdfMeta } from '../lib/pdf'
import { downloadBlob, fmtSize } from '../lib/utils'
import { useTabDirty } from '../lib/dirtyContext'

interface QueuedFile {
  id: string
  file: File
  pages?: number
  size: number
  loading: boolean
  error?: string
}

interface Props {
  setStatus: (s: string) => void
}

export function MergeTab({ setStatus }: Props) {
  const [items, setItems] = useState<QueuedFile[]>([])
  const [progress, setProgress] = useState<ProgressState>({ kind: 'idle' })
  const [running, setRunning] = useState(false)
  const [saved, setSaved] = useState(false)

  // Any change to the queue invalidates the previous merge.
  useEffect(() => {
    setSaved(false)
  }, [items])

  useTabDirty(
    'merge',
    items.length > 0 && !saved,
    `You have ${items.length} file${items.length === 1 ? '' : 's'} queued that haven't been merged and saved yet.`,
  )

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const addFiles = (files: File[]) => {
    const created: QueuedFile[] = files.map(f => ({
      id: `${f.name}-${f.size}-${f.lastModified}-${Math.random().toString(36).slice(2, 6)}`,
      file: f,
      size: f.size,
      loading: true,
    }))
    setItems(prev => [...prev, ...created])
    // Read meta in parallel, capped at 4 at a time would be ideal but keep simple:
    created.forEach(async qf => {
      try {
        const m = await readPdfMeta(qf.file)
        setItems(prev =>
          prev.map(p => (p.id === qf.id ? { ...p, pages: m.pages, loading: false } : p)),
        )
      } catch (e) {
        setItems(prev =>
          prev.map(p => (p.id === qf.id ? { ...p, loading: false, error: (e as Error).message } : p)),
        )
      }
    })
  }

  const remove = (id: string) => setItems(prev => prev.filter(p => p.id !== id))
  const clear = () => { setItems([]); setProgress({ kind: 'idle' }) }

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return
    setItems(prev => {
      const oldIdx = prev.findIndex(p => p.id === active.id)
      const newIdx = prev.findIndex(p => p.id === over.id)
      if (oldIdx < 0 || newIdx < 0) return prev
      return arrayMove(prev, oldIdx, newIdx)
    })
  }

  const totalPages = items.reduce((acc, p) => acc + (p.pages ?? 0), 0)
  const totalSize = items.reduce((acc, p) => acc + p.size, 0)

  const canRun = items.length >= 2 && !items.some(i => i.loading || i.error) && !running

  const run = async () => {
    setRunning(true)
    setProgress({ kind: 'working', label: 'Preparing…' })
    try {
      const { bytes, totalPages: tp } = await mergePdfs(
        items.map(i => i.file),
        (done, total, name) =>
          setProgress({ kind: 'progress', done, total, label: name }),
      )
      const outName = 'merged.pdf'
      downloadBlob(bytes, outName, 'application/pdf')
      setProgress({ kind: 'done', label: `Merged ${items.length} PDFs (${tp} pages) → ${outName}` })
      setStatus(`Merged → ${outName}`)
      setSaved(true)
    } catch (e) {
      setProgress({ kind: 'error', label: (e as Error).message })
      setStatus('Merge failed')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
      <DropZone
        label="Add PDFs to merge"
        sublabel="Drag & drop multiple files, or click to browse · drag rows to reorder"
        multiple
        onFiles={addFiles}
        compact={items.length > 0}
      />

      {items.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <SectionLabel className="mb-0">
              {items.length} file{items.length === 1 ? '' : 's'} queued
              {totalPages > 0 && ` · ${totalPages} pages · ${fmtSize(totalSize)}`}
            </SectionLabel>
            <Button variant="ghost" size="sm" onClick={clear}>Clear all</Button>
          </div>

          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
            <SortableContext items={items.map(i => i.id)} strategy={verticalListSortingStrategy}>
              <ul className="space-y-1.5">
                {items.map((it, i) => (
                  <SortableRow key={it.id} item={it} index={i} onRemove={() => remove(it.id)} />
                ))}
              </ul>
            </SortableContext>
          </DndContext>
        </div>
      )}

      <div className="h-px bg-rule" />

      <div className="flex flex-col items-center gap-4 pt-2">
        <Button variant="primary" size="lg" onClick={run} disabled={!canRun} className="w-full sm:w-auto">
          {running ? 'Merging…' : `Merge ${items.length || ''} PDF${items.length === 1 ? '' : 's'}`.trim()}
        </Button>
        <div className="w-full">
          <Progress state={progress} />
        </div>
      </div>

      {items.length < 2 && items.length > 0 && (
        <div className="text-[11px] text-stone text-center">Add at least one more file to merge.</div>
      )}
    </div>
  )
}

function SortableRow({
  item,
  index,
  onRemove,
}: {
  item: QueuedFile
  index: number
  onRemove: () => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: item.id })

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={clsx(
        'flex items-center gap-3 px-2.5 py-2 bg-panel rounded-md border border-rule',
        isDragging && 'opacity-60 shadow-lg ring-1 ring-coral z-10 relative',
      )}
    >
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing text-stone hover:text-cream w-6 h-6 flex items-center justify-center focus:outline-none focus:text-cream"
        aria-label="Drag to reorder"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
          <circle cx="4" cy="3" r="1" />
          <circle cx="8" cy="3" r="1" />
          <circle cx="4" cy="6" r="1" />
          <circle cx="8" cy="6" r="1" />
          <circle cx="4" cy="9" r="1" />
          <circle cx="8" cy="9" r="1" />
        </svg>
      </button>
      <span className="font-mono text-[11px] text-stone w-6 text-right tabular-nums">{index + 1}</span>
      <div className="flex-1 min-w-0">
        <div className="truncate text-[13px] text-cream">{item.file.name}</div>
        <div className="text-[11px] text-stone tabular-nums mt-0.5">
          {item.loading
            ? 'Reading…'
            : item.error
              ? <span className="text-danger">{item.error}</span>
              : `${item.pages ?? '?'} pages · ${fmtSize(item.size)}`}
        </div>
      </div>
      <button
        onClick={onRemove}
        aria-label="Remove file"
        className="text-stone hover:text-cream w-7 h-7 flex items-center justify-center rounded hover:bg-panel-2 transition-colors cursor-pointer focus:outline-none"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
          <path d="M3 3l8 8M11 3l-8 8" />
        </svg>
      </button>
    </li>
  )
}

