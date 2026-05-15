import { PointerEvent as RPointerEvent, useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { Point, Quad } from '../lib/imageWarp'

interface Props {
  image: ImageBitmap
  quad: Quad
  onChange: (q: Quad) => void
}

const HANDLE_LABELS = ['TL', 'TR', 'BR', 'BL'] as const

export function CornerEditor({ image, quad, onChange }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [layout, setLayout] = useState({ w: 0, h: 0, scale: 1 })
  const dragRef = useRef<{ idx: number; pointerId: number } | null>(null)

  // Fit image to container preserving aspect
  useLayoutEffect(() => {
    const update = () => {
      const wrap = wrapRef.current
      if (!wrap) return
      const cw = wrap.clientWidth
      const ch = wrap.clientHeight
      if (cw === 0 || ch === 0) return
      const scale = Math.min(cw / image.width, ch / image.height)
      setLayout({ w: image.width * scale, h: image.height * scale, scale })
    }
    update()
    const ro = new ResizeObserver(update)
    if (wrapRef.current) ro.observe(wrapRef.current)
    return () => ro.disconnect()
  }, [image])

  // Draw image to canvas when bitmap or layout changes
  useEffect(() => {
    const c = canvasRef.current
    if (!c || layout.w === 0) return
    c.width = Math.round(layout.w * devicePixelRatio)
    c.height = Math.round(layout.h * devicePixelRatio)
    c.style.width = `${layout.w}px`
    c.style.height = `${layout.h}px`
    const ctx = c.getContext('2d')!
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(image, 0, 0, c.width, c.height)
  }, [image, layout])

  const handlePointerDown = (idx: number) => (e: RPointerEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    e.currentTarget.setPointerCapture(e.pointerId)
    dragRef.current = { idx, pointerId: e.pointerId }
  }

  const handlePointerMove = (e: RPointerEvent<HTMLDivElement>) => {
    const d = dragRef.current
    if (!d) return
    e.preventDefault()
    const rect = wrapRef.current!.getBoundingClientRect()
    const offsetX = (rect.width - layout.w) / 2
    const offsetY = (rect.height - layout.h) / 2
    const localX = e.clientX - rect.left - offsetX
    const localY = e.clientY - rect.top - offsetY
    const sx = clamp(localX / layout.scale, 0, image.width)
    const sy = clamp(localY / layout.scale, 0, image.height)
    const next = quad.slice() as Quad
    next[d.idx] = { x: sx, y: sy }
    onChange(next)
  }

  const handlePointerUp = (e: RPointerEvent<HTMLDivElement>) => {
    const d = dragRef.current
    if (!d) return
    e.currentTarget.releasePointerCapture(d.pointerId)
    dragRef.current = null
  }

  // Convert source-pixel coord to display-px relative to wrap container
  const toScreen = (p: Point) => {
    const wrap = wrapRef.current
    if (!wrap) return { x: 0, y: 0 }
    const offsetX = (wrap.clientWidth - layout.w) / 2
    const offsetY = (wrap.clientHeight - layout.h) / 2
    return { x: p.x * layout.scale + offsetX, y: p.y * layout.scale + offsetY }
  }

  const screenQuad = quad.map(toScreen)

  return (
    <div
      ref={wrapRef}
      className="relative w-full h-full bg-panel rounded-md border border-rule overflow-hidden touch-none select-none"
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      {layout.w > 0 && (
        <>
          <canvas
            ref={canvasRef}
            className="absolute pointer-events-none"
            style={{
              left: `calc(50% - ${layout.w / 2}px)`,
              top: `calc(50% - ${layout.h / 2}px)`,
            }}
          />
          <svg
            className="absolute inset-0 pointer-events-none"
            width="100%"
            height="100%"
          >
            <polygon
              points={screenQuad.map(p => `${p.x},${p.y}`).join(' ')}
              fill="rgba(207, 95, 42, 0.10)"
              stroke="#CF5F2A"
              strokeWidth="2"
              strokeLinejoin="round"
            />
          </svg>
          {screenQuad.map((p, i) => (
            <Handle
              key={i}
              label={HANDLE_LABELS[i]}
              x={p.x}
              y={p.y}
              onPointerDown={handlePointerDown(i)}
            />
          ))}
        </>
      )}
    </div>
  )
}

function Handle({
  x,
  y,
  label,
  onPointerDown,
}: {
  x: number
  y: number
  label: string
  onPointerDown: (e: RPointerEvent<HTMLDivElement>) => void
}) {
  return (
    <div
      role="slider"
      aria-label={`${label} corner`}
      onPointerDown={onPointerDown}
      className="absolute w-5 h-5 -ml-2.5 -mt-2.5 rounded-full bg-white border-[2px] border-coral shadow-md cursor-grab active:cursor-grabbing hover:scale-110 transition-transform"
      style={{ left: x, top: y, touchAction: 'none' }}
    />
  )
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v))
}
