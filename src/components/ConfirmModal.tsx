import { useEffect, useRef } from 'react'
import { Button } from './Button'

interface Props {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = 'Continue',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
}: Props) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    confirmRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onCancel()
      } else if (e.key === 'Enter') {
        e.preventDefault()
        onConfirm()
      }
    }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onConfirm, onCancel])

  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm fade-in"
      onClick={onCancel}
    >
      <div
        onClick={e => e.stopPropagation()}
        className="bg-panel-2 rounded-lg shadow-2xl border border-rule max-w-md w-full overflow-hidden"
      >
        <div className="p-5">
          <h3 id="modal-title" className="text-[14px] font-semibold text-cream">
            {title}
          </h3>
          <p className="mt-2 text-[12.5px] text-stone-soft leading-relaxed">{message}</p>
        </div>
        <div className="flex justify-end gap-2 px-4 py-3 bg-panel border-t border-rule">
          <Button variant="secondary" size="md" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button ref={confirmRef} variant="primary" size="md" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
