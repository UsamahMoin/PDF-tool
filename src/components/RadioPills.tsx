import clsx from 'clsx'

interface Option<V extends string> {
  value: V
  label: string
  hint?: string
}

interface Props<V extends string> {
  value: V
  options: Option<V>[]
  onChange: (v: V) => void
  ariaLabel?: string
}

export function RadioPills<V extends string>({ value, options, onChange, ariaLabel }: Props<V>) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="inline-flex bg-panel rounded-md p-1 border border-rule">
      {options.map(opt => {
        const active = opt.value === value
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={clsx(
              'px-3.5 h-8 rounded text-[12.5px] transition-colors cursor-pointer focus:outline-none whitespace-nowrap',
              active
                ? 'bg-panel-2 text-cream shadow-sm'
                : 'text-stone hover:text-cream',
            )}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
