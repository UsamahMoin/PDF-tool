export interface Point {
  x: number
  y: number
}

export type Quad = [Point, Point, Point, Point] // TL, TR, BR, BL — in source-image pixel coords

const VS = `
  attribute vec2 a_pos;
  varying vec2 v_uv;
  void main() {
    gl_Position = vec4(a_pos, 0.0, 1.0);
    v_uv = (a_pos + 1.0) * 0.5;
  }
`

const FS = `
  precision highp float;
  uniform sampler2D u_image;
  uniform vec2 u_imageSize;
  uniform vec2 u_tl;
  uniform vec2 u_tr;
  uniform vec2 u_br;
  uniform vec2 u_bl;
  varying vec2 v_uv;
  void main() {
    float fx = v_uv.x;
    float fy = 1.0 - v_uv.y;
    vec2 top    = mix(u_tl, u_tr, fx);
    vec2 bot    = mix(u_bl, u_br, fx);
    vec2 srcPx  = mix(top, bot, fy);
    vec2 srcUV  = srcPx / u_imageSize;
    if (srcUV.x < 0.0 || srcUV.x > 1.0 || srcUV.y < 0.0 || srcUV.y > 1.0) {
      gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
    } else {
      gl_FragColor = texture2D(u_image, srcUV);
    }
  }
`

interface Cached {
  canvas: HTMLCanvasElement
  gl: WebGLRenderingContext
  program: WebGLProgram
  uImageSize: WebGLUniformLocation
  uTL: WebGLUniformLocation
  uTR: WebGLUniformLocation
  uBR: WebGLUniformLocation
  uBL: WebGLUniformLocation
}

let cached: Cached | null = null

function getContext(): Cached {
  if (cached) return cached
  const canvas = document.createElement('canvas')
  const gl =
    canvas.getContext('webgl', { premultipliedAlpha: false, preserveDrawingBuffer: true }) ||
    canvas.getContext('experimental-webgl', { preserveDrawingBuffer: true }) as WebGLRenderingContext | null
  if (!gl) throw new Error('WebGL is not supported in this browser.')

  const vs = compileShader(gl, gl.VERTEX_SHADER, VS)
  const fs = compileShader(gl, gl.FRAGMENT_SHADER, FS)
  const program = gl.createProgram()!
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error('Failed to link WebGL program: ' + gl.getProgramInfoLog(program))
  }
  gl.useProgram(program)

  // Full-screen triangle pair
  const buf = gl.createBuffer()!
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
    gl.STATIC_DRAW,
  )
  const aPos = gl.getAttribLocation(program, 'a_pos')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  cached = {
    canvas,
    gl,
    program,
    uImageSize: gl.getUniformLocation(program, 'u_imageSize')!,
    uTL: gl.getUniformLocation(program, 'u_tl')!,
    uTR: gl.getUniformLocation(program, 'u_tr')!,
    uBR: gl.getUniformLocation(program, 'u_br')!,
    uBL: gl.getUniformLocation(program, 'u_bl')!,
  }
  return cached
}

function compileShader(gl: WebGLRenderingContext, type: number, src: string): WebGLShader {
  const s = gl.createShader(type)!
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(s)
    gl.deleteShader(s)
    throw new Error('Shader compile failed: ' + log)
  }
  return s
}

export function warpQuad(
  source: HTMLImageElement | HTMLCanvasElement | ImageBitmap,
  quad: Quad,
  outWidth: number,
  outHeight: number,
): HTMLCanvasElement {
  const ctx = getContext()
  const { canvas, gl } = ctx

  canvas.width = Math.max(1, Math.floor(outWidth))
  canvas.height = Math.max(1, Math.floor(outHeight))
  gl.viewport(0, 0, canvas.width, canvas.height)

  const srcW = (source as HTMLImageElement).naturalWidth || (source as HTMLCanvasElement).width
  const srcH = (source as HTMLImageElement).naturalHeight || (source as HTMLCanvasElement).height

  const tex = gl.createTexture()!
  gl.bindTexture(gl.TEXTURE_2D, tex)
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source as TexImageSource)

  gl.uniform2f(ctx.uImageSize, srcW, srcH)
  gl.uniform2f(ctx.uTL, quad[0].x, quad[0].y)
  gl.uniform2f(ctx.uTR, quad[1].x, quad[1].y)
  gl.uniform2f(ctx.uBR, quad[2].x, quad[2].y)
  gl.uniform2f(ctx.uBL, quad[3].x, quad[3].y)

  gl.clearColor(1, 1, 1, 1)
  gl.clear(gl.COLOR_BUFFER_BIT)
  gl.drawArrays(gl.TRIANGLES, 0, 6)

  const out = document.createElement('canvas')
  out.width = canvas.width
  out.height = canvas.height
  out.getContext('2d')!.drawImage(canvas, 0, 0)

  gl.bindTexture(gl.TEXTURE_2D, null)
  gl.deleteTexture(tex)

  return out
}

export function dist(a: Point, b: Point): number {
  const dx = a.x - b.x
  const dy = a.y - b.y
  return Math.hypot(dx, dy)
}

/** Compute output canvas size from quad: width = avg of top/bottom edges, height = avg of left/right. */
export function computeWarpedSize(quad: Quad): { width: number; height: number } {
  const [tl, tr, br, bl] = quad
  const w = Math.max(dist(tl, tr), dist(bl, br))
  const h = Math.max(dist(tl, bl), dist(tr, br))
  return { width: Math.max(1, Math.round(w)), height: Math.max(1, Math.round(h)) }
}

/** Default corners: 5% inset from image bounds, in source-pixel coords. */
export function defaultQuad(w: number, h: number): Quad {
  const ix = w * 0.05
  const iy = h * 0.05
  return [
    { x: ix, y: iy },
    { x: w - ix, y: iy },
    { x: w - ix, y: h - iy },
    { x: ix, y: h - iy },
  ]
}
