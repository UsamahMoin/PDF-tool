export function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  let n = bytes / 1024
  for (const u of ['KB', 'MB', 'GB', 'TB']) {
    if (n < 1024) return `${n.toFixed(1)} ${u}`
    n /= 1024
  }
  return `${n.toFixed(1)} PB`
}

export function stem(name: string): string {
  return name.replace(/\.pdf$/i, '')
}

export type Downloadable = Uint8Array | ArrayBuffer | Blob | string

export function downloadBlob(data: Downloadable, filename: string, type = 'application/octet-stream') {
  let blob: Blob
  if (data instanceof Blob) {
    blob = data
  } else if (typeof data === 'string') {
    blob = new Blob([data], { type })
  } else if (data instanceof ArrayBuffer) {
    blob = new Blob([data], { type })
  } else {
    // Uint8Array — copy into a fresh ArrayBuffer for the strictest DOM lib types
    const ab = new ArrayBuffer(data.byteLength)
    new Uint8Array(ab).set(data)
    blob = new Blob([ab], { type })
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export function classes(...c: (string | false | null | undefined)[]): string {
  return c.filter(Boolean).join(' ')
}
