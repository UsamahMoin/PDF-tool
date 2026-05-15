import { ButtonHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: 'sm' | 'md' | 'lg'
}

const base =
  'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors select-none disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer whitespace-nowrap'

const sizes: Record<NonNullable<Props['size']>, string> = {
  sm: 'h-7 px-2.5 text-[12px]',
  md: 'h-9 px-3.5 text-[13px]',
  lg: 'h-11 px-7 text-[14px] font-semibold',
}

const variants: Record<Variant, string> = {
  primary: 'bg-coral text-white hover:bg-coral-hover active:bg-coral-hover shadow-sm',
  secondary: 'bg-panel-2 text-cream hover:bg-rule active:bg-rule-strong',
  ghost: 'bg-transparent text-stone hover:text-cream hover:bg-panel-2',
  danger: 'bg-transparent text-danger hover:bg-panel-2',
}

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = 'secondary', size = 'md', className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={clsx(base, sizes[size], variants[variant], className)}
      {...rest}
    />
  )
})
