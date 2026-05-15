import { InputHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  mono?: boolean
}

export const TextField = forwardRef<HTMLInputElement, Props>(function TextField(
  { mono, className, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      className={clsx(
        'h-9 px-3 rounded-md bg-panel border border-rule text-cream text-[13px]',
        'placeholder:text-stone focus:outline-none focus:border-coral focus:ring-1 focus:ring-coral transition-colors',
        mono && 'font-mono',
        className,
      )}
      {...rest}
    />
  )
})
