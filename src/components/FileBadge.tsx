import { fmtSize } from '../lib/utils'

interface Props {
  name: string
  pages?: number
  size: number
  onClear?: () => void
}

export function FileBadge({ name, pages, size, onClear }: Props) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-panel rounded-md border border-rule">
      <div className="h-8 w-8 rounded bg-panel-2 flex items-center justify-center text-stone-soft text-[10px] font-bold">
        PDF
      </div>
      <div className="flex-1 min-w-0">
        <div className="truncate text-[13px] text-cream font-medium">{name}</div>
        <div className="text-[11px] text-stone tabular-nums mt-0.5">
          {pages != null ? `${pages} page${pages === 1 ? '' : 's'} · ` : ''}{fmtSize(size)}
        </div>
      </div>
      {onClear && (
        <button
          onClick={onClear}
          aria-label="Remove file"
          className="text-stone hover:text-cream w-7 h-7 flex items-center justify-center rounded hover:bg-panel-2 transition-colors cursor-pointer focus:outline-none"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <path d="M3 3l8 8M11 3l-8 8" />
          </svg>
        </button>
      )}
    </div>
  )
}
