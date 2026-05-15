import { DragEvent, useRef, useState } from 'react'
import clsx from 'clsx'

interface Props {
  label: string
  sublabel?: string
  accept?: string
  multiple?: boolean
  onFiles: (files: File[]) => void
  className?: string
  compact?: boolean
}

export function DropZone({
  label,
  sublabel = 'Drag & drop, or click to browse',
  accept = '.pdf,application/pdf',
  multiple = false,
  onFiles,
  className,
  compact = false,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const dragCount = useRef(0)

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    dragCount.current = 0
    setOver(false)
    const files = filterFiles(Array.from(e.dataTransfer.files), accept)
    if (files.length) onFiles(multiple ? files : files.slice(0, 1))
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragEnter={e => {
        e.preventDefault()
        dragCount.current++
        setOver(true)
      }}
      onDragLeave={() => {
        dragCount.current--
        if (dragCount.current <= 0) {
          dragCount.current = 0
          setOver(false)
        }
      }}
      onDragOver={e => e.preventDefault()}
      onDrop={onDrop}
      role="button"
      tabIndex={0}
      className={clsx(
        'group relative rounded-lg cursor-pointer transition-all',
        'border border-dashed flex flex-col items-center justify-center text-center',
        compact ? 'h-20 px-4' : 'h-28 px-6',
        over
          ? 'border-coral bg-coral/5 scale-[1.005]'
          : 'border-rule bg-panel hover:border-rule-strong hover:bg-panel/80',
        className,
      )}
    >
      <span
        className={clsx(
          'font-semibold text-cream',
          compact ? 'text-[13px]' : 'text-[14px]',
        )}
      >
        {label}
      </span>
      <span
        className={clsx(
          'mt-1 transition-colors',
          compact ? 'text-[11px]' : 'text-[12px]',
          over ? 'text-coral' : 'text-stone',
        )}
      >
        {sublabel}
      </span>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={e => {
          const files = Array.from(e.target.files ?? [])
          if (files.length) onFiles(multiple ? files : files.slice(0, 1))
          // reset so same file can be re-selected
          e.target.value = ''
        }}
      />
    </div>
  )
}

function filterFiles(files: File[], accept: string): File[] {
  const exts = accept
    .split(',')
    .map(s => s.trim().toLowerCase())
    .filter(s => s.startsWith('.'))
  if (!exts.length) return files
  return files.filter(f => exts.some(ext => f.name.toLowerCase().endsWith(ext)))
}
