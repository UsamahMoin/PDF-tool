import { useEffect, useState } from 'react'

interface Props {
  value: number
  onChange: (n: number) => void
  min?: number
  max?: number
  step?: number
  width?: number
  ariaLabel?: string
}

export function Stepper({
  value,
  onChange,
  min = 1,
  max = 9999,
  step = 1,
  width = 64,
  ariaLabel,
}: Props) {
  const [draft, setDraft] = useState(String(value))

  useEffect(() => { setDraft(String(value)) }, [value])

  const clamp = (n: number) => Math.min(max, Math.max(min, n))
  const dec = () => onChange(clamp(value - step))
  const inc = () => onChange(clamp(value + step))

  return (
    <div className="inline-flex items-center bg-panel-2 rounded-md overflow-hidden border border-rule">
      <button
        type="button"
        onClick={dec}
        disabled={value <= min}
        className="h-9 w-9 flex items-center justify-center text-cream hover:bg-rule active:bg-rule-strong disabled:opacity-30 disabled:hover:bg-panel-2 transition-colors cursor-pointer text-lg leading-none focus:outline-none"
        aria-label="Decrease"
      >
        −
      </button>
      <input
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        aria-label={ariaLabel}
        value={draft}
        onChange={e => {
          const v = e.target.value.replace(/[^\d]/g, '')
          setDraft(v)
        }}
        onBlur={() => {
          const n = parseInt(draft, 10)
          if (Number.isFinite(n)) onChange(clamp(n))
          else setDraft(String(value))
        }}
        onKeyDown={e => {
          if (e.key === 'Enter') (e.target as HTMLInputElement).blur()
          else if (e.key === 'ArrowUp') { e.preventDefault(); inc() }
          else if (e.key === 'ArrowDown') { e.preventDefault(); dec() }
        }}
        style={{ width }}
        className="h-9 bg-transparent text-center text-cream font-mono text-[13px] focus:outline-none border-x border-rule"
      />
      <button
        type="button"
        onClick={inc}
        disabled={value >= max}
        className="h-9 w-9 flex items-center justify-center text-cream hover:bg-rule active:bg-rule-strong disabled:opacity-30 disabled:hover:bg-panel-2 transition-colors cursor-pointer text-lg leading-none focus:outline-none"
        aria-label="Increase"
      >
        +
      </button>
    </div>
  )
}
