import { Capacitor } from '@capacitor/core'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import { Filesystem, Directory } from '@capacitor/filesystem'
import { Share } from '@capacitor/share'

export const isNative = Capacitor.isNativePlatform()
export const platform = Capacitor.getPlatform() as 'ios' | 'android' | 'web'

/**
 * Opens the device camera and returns the photo as a File suitable for
 * the existing image pipeline. Native only — on web this rejects.
 */
export async function takePhoto(): Promise<File> {
  if (!isNative) throw new Error('Camera capture requires the native app.')

  const photo = await Camera.getPhoto({
    quality: 92,
    allowEditing: false,
    resultType: CameraResultType.Uri,
    source: CameraSource.Camera,
    saveToGallery: false,
  })
  if (!photo.webPath) throw new Error('Camera returned no image.')

  const response = await fetch(photo.webPath)
  const blob = await response.blob()
  const ext = (photo.format || 'jpg').replace('jpeg', 'jpg')
  return new File([blob], `photo-${Date.now()}.${ext}`, {
    type: blob.type || `image/${photo.format || 'jpeg'}`,
  })
}

/**
 * Saves a file on the native device into the app's Documents directory
 * and presents the Share sheet so the user can move it anywhere (Files,
 * Drive, AirDrop, Mail, etc). The file always lands in Documents first,
 * so it's still recoverable even if the user dismisses the share sheet.
 */
export async function saveFileNative(
  data: Blob | Uint8Array | ArrayBuffer | string,
  filename: string,
  mimeType: string,
): Promise<{ uri: string }> {
  const base64 = await toBase64(data, mimeType)
  const written = await Filesystem.writeFile({
    path: filename,
    data: base64,
    directory: Directory.Documents,
    recursive: true,
  })

  // Try to surface the Share sheet so the user can pick a destination.
  // If unsupported or cancelled, the file is still saved in Documents.
  try {
    await Share.share({
      title: filename,
      url: written.uri,
      dialogTitle: `Save ${filename}`,
    })
  } catch {
    // user cancelled or share unsupported — file remains in Documents
  }

  return { uri: written.uri }
}

async function toBase64(
  data: Blob | Uint8Array | ArrayBuffer | string,
  mimeType: string,
): Promise<string> {
  if (typeof data === 'string') {
    return btoa(unescape(encodeURIComponent(data)))
  }
  if (data instanceof Blob) {
    return blobToBase64(data)
  }
  const bytes = data instanceof ArrayBuffer ? new Uint8Array(data) : data
  // For large buffers go via Blob to avoid blowing the call stack.
  if (bytes.byteLength > 65_536) {
    const ab = new ArrayBuffer(bytes.byteLength)
    new Uint8Array(ab).set(bytes)
    return blobToBase64(new Blob([ab], { type: mimeType }))
  }
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      const comma = result.indexOf(',')
      resolve(comma >= 0 ? result.slice(comma + 1) : result)
    }
    reader.onerror = () => reject(reader.error ?? new Error('Failed to read blob'))
    reader.readAsDataURL(blob)
  })
}
