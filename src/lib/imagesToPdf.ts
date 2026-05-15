import { PDFDocument } from 'pdf-lib'

/**
 * Build a PDF where each blob becomes one page sized to the image.
 * Blobs must be JPEG or PNG.
 */
export async function imagesToPdf(
  blobs: Blob[],
  onProgress?: (done: number, total: number, label: string) => void,
): Promise<Uint8Array> {
  const pdf = await PDFDocument.create()
  for (let i = 0; i < blobs.length; i++) {
    const blob = blobs[i]
    const bytes = new Uint8Array(await blob.arrayBuffer())
    const isPng = blob.type === 'image/png' || sniffPng(bytes)
    const img = isPng ? await pdf.embedPng(bytes) : await pdf.embedJpg(bytes)
    const page = pdf.addPage([img.width, img.height])
    page.drawImage(img, { x: 0, y: 0, width: img.width, height: img.height })
    onProgress?.(i + 1, blobs.length, `Page ${i + 1}`)
    await new Promise(r => setTimeout(r, 0))
  }
  return pdf.save()
}

function sniffPng(bytes: Uint8Array): boolean {
  return (
    bytes.length >= 8 &&
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47
  )
}

/** Convert a canvas to a JPEG Blob at the given quality. */
export function canvasToJpeg(canvas: HTMLCanvasElement, quality = 0.92): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      b => (b ? resolve(b) : reject(new Error('Failed to encode canvas to JPEG'))),
      'image/jpeg',
      quality,
    )
  })
}
