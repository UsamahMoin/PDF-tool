import { ReactNode } from 'react'
import clsx from 'clsx'

interface Props {
  children: ReactNode
  className?: string
}

export function SectionLabel({ children, className }: Props) {
  return (
    <div className={clsx('text-[10.5px] font-semibold text-stone uppercase tracking-[0.08em] mb-2', className)}>
      {children}
    </div>
  )
}
