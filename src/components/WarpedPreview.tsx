import { useEffect, useRef } from 'react'
import { computeWarpedSize, warpQuad, type Quad } from '../lib/imageWarp'

interface Props {
  image: ImageBitmap
  quad: Quad
}

export function WarpedPreview({ image, quad }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const lastRequest = useRef(0)

  useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return
    const reqId = ++lastRequest.current
    let cancelled = false

    const run = () => {
      if (cancelled || reqId !== lastRequest.current) return
      try {
        const { width, height } = computeWarpedSize(quad)
        const out = warpQuad(image, quad, width, height)
        out.style.maxWidth = '100%'
        out.style.maxHeight = '100%'
        out.style.objectFit = 'contain'
        out.className = 'block mx-auto rounded-md'
        // replace
        const old = wrap.firstElementChild
        wrap.replaceChildren(out)
        if (old) (old as HTMLCanvasElement).remove?.()
      } catch (e) {
        wrap.replaceChildren(Object.assign(document.createElement('div'), {
          className: 'text-[12px] text-danger p-4',
          textContent: 'Preview unavailable: ' + (e as Error).message,
        }))
      }
    }

    // Throttle to next frame so dragging stays smooth
    const raf = requestAnimationFrame(run)
    return () => {
      cancelled = true
      cancelAnimationFrame(raf)
    }
  }, [image, quad])

  return (
    <div
      ref={wrapRef}
      className="flex items-center justify-center w-full h-full bg-panel rounded-md border border-rule overflow-hidden p-2"
    />
  )
}
