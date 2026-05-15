import { ReactNode, useLayoutEffect, useRef, useState } from 'react'
import clsx from 'clsx'

export interface Tab {
  id: string
  label: ReactNode
  content: ReactNode
}

interface Props {
  tabs: Tab[]
  active: string
  onChange: (id: string) => void
}

export function Tabs({ tabs, active, onChange }: Props) {
  const stripRef = useRef<HTMLDivElement>(null)
  const btnRefs = useRef<Record<string, HTMLButtonElement | null>>({})
  const [indicator, setIndicator] = useState<{ left: number; width: number }>({ left: 0, width: 0 })

  useLayoutEffect(() => {
    const reposition = () => {
      const btn = btnRefs.current[active]
      const strip = stripRef.current
      if (!btn || !strip) return
      const sr = strip.getBoundingClientRect()
      const br = btn.getBoundingClientRect()
      setIndicator({
        left: br.left - sr.left + strip.scrollLeft,
        width: br.width,
      })
    }
    reposition()
    const strip = stripRef.current
    if (strip) strip.addEventListener('scroll', reposition, { passive: true })
    window.addEventListener('resize', reposition)
    return () => {
      if (strip) strip.removeEventListener('scroll', reposition)
      window.removeEventListener('resize', reposition)
    }
  }, [active, tabs.length])

  // Make sure the active tab is visible when the strip overflows
  useLayoutEffect(() => {
    const btn = btnRefs.current[active]
    btn?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [active])

  return (
    <div className="flex flex-col h-full min-h-0">
      <div
        ref={stripRef}
        className="relative flex bg-panel-2 border-b border-rule overflow-x-auto"
        style={{ scrollbarWidth: 'none' }}
        role="tablist"
      >
        {tabs.map(t => {
          const isActive = t.id === active
          return (
            <button
              key={t.id}
              ref={el => { btnRefs.current[t.id] = el }}
              role="tab"
              aria-selected={isActive}
              tabIndex={isActive ? 0 : -1}
              onClick={() => onChange(t.id)}
              className={clsx(
                'relative px-3.5 sm:px-6 h-11 text-[13px] transition-colors cursor-pointer focus:outline-none whitespace-nowrap shrink-0',
                isActive
                  ? 'bg-ink text-cream font-semibold'
                  : 'text-stone hover:text-cream hover:bg-rule',
              )}
            >
              {t.label}
            </button>
          )
        })}
        <div
          className="absolute bottom-0 h-[2px] bg-coral transition-all duration-200 ease-out pointer-events-none"
          style={{ left: indicator.left, width: indicator.width }}
        />
      </div>
      <div
        className="flex-1 min-h-0 overflow-y-auto"
        style={{ scrollbarGutter: 'stable' }}
      >
        {tabs.map(t => (
          <div
            key={t.id}
            role="tabpanel"
            hidden={t.id !== active}
            aria-hidden={t.id !== active}
            className="h-full"
          >
            {t.content}
          </div>
        ))}
      </div>
    </div>
  )
}
