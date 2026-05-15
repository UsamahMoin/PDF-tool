import clsx from 'clsx'

export type ProgressState =
  | { kind: 'idle' }
  | { kind: 'working'; label: string }
  | { kind: 'progress'; done: number; total: number; label: string }
  | { kind: 'done'; label: string }
  | { kind: 'error'; label: string }

interface Props {
  state: ProgressState
  className?: string
}

export function Progress({ state, className }: Props) {
  if (state.kind === 'idle') return null

  const pct =
    state.kind === 'progress' ? Math.round((state.done / Math.max(1, state.total)) * 100) :
    state.kind === 'done' ? 100 :
    state.kind === 'error' ? 0 : 0

  const indeterminate = state.kind === 'working'

  return (
    <div className={clsx('w-full', className)}>
      <div className="flex items-center justify-between mb-1.5 text-[12px]">
        <span
          className={clsx(
            'truncate',
            state.kind === 'done' && 'text-success',
            state.kind === 'error' && 'text-danger',
            (state.kind === 'working' || state.kind === 'progress') && 'text-stone-soft',
          )}
        >
          {state.label}
        </span>
        {state.kind === 'progress' && (
          <span className="text-stone tabular-nums">{pct}%</span>
        )}
      </div>
      <div className="relative h-1.5 bg-panel-2 rounded-full overflow-hidden">
        {indeterminate ? (
          <div className="relative h-full w-full overflow-hidden">
            <div className="absolute inset-0 shimmer" />
          </div>
        ) : (
          <div
            className={clsx(
              'h-full transition-all duration-300 ease-out',
              state.kind === 'error' ? 'bg-danger' : 'bg-coral',
            )}
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
    </div>
  )
}
