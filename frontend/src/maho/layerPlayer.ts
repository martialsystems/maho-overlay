import type { MahoTexture } from "./motion";

export type LayerSpec = {
  width: number;
  height: number;
  facePivot: [number, number];
  zoom: number;
  viewOffset: [number, number];
  layers: { id: string; file: string; bob?: boolean; rotate?: boolean }[];
  face: Record<MahoTexture, string>;
};

const VERTEX_SOURCE = `#version 300 es
in vec2 a_pos;
in vec2 a_uv;
uniform vec2 u_scale;
uniform vec2 u_offset;
uniform vec2 u_pivot;
uniform float u_rot;
uniform float u_bob;
out vec2 v_uv;
void main() {
  vec2 p = a_pos;
  vec2 d = p - u_pivot;
  float c = cos(u_rot);
  float s = sin(u_rot);
  p = u_pivot + vec2(d.x * c - d.y * s, d.x * s + d.y * c);
  p.y += u_bob;
  p = (p - 0.5) * u_scale + 0.5 + u_offset;
  gl_Position = vec4(p * vec2(2.0, -2.0) + vec2(-1.0, 1.0), 0.0, 1.0);
  v_uv = a_uv;
}
`;

const FRAGMENT_SOURCE = `#version 300 es
precision highp float;
in vec2 v_uv;
uniform sampler2D u_tex;
out vec4 fragColor;
void main() {
  fragColor = texture(u_tex, v_uv);
}
`;

function compile(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader {
  const shader = gl.createShader(type);
  if (!shader) throw new Error("Could not create shader");
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const info = gl.getShaderInfoLog(shader) ?? "shader compile failed";
    gl.deleteShader(shader);
    throw new Error(info);
  }
  return shader;
}

function loadTexture(gl: WebGL2RenderingContext, url: string): Promise<WebGLTexture> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const texture = gl.createTexture();
      if (!texture) {
        reject(new Error("Could not create texture"));
        return;
      }
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, 1);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
      resolve(texture);
    };
    image.onerror = () => reject(new Error(`Failed to load ${url}`));
    image.src = url;
  });
}

export type LayerPose = {
  faceRot: number;
  torsoBob: number;
};

const QUAD = new Float32Array([0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1]);

export class MahoLayerPlayer {
  private readonly gl: WebGL2RenderingContext;
  private readonly spec: LayerSpec;
  private program: WebGLProgram | null = null;
  private quad: WebGLBuffer | null = null;
  private textures = new Map<string, WebGLTexture>();
  private posLoc = -1;
  private uvLoc = -1;
  private scaleLoc: WebGLUniformLocation | null = null;
  private offsetLoc: WebGLUniformLocation | null = null;
  private pivotLoc: WebGLUniformLocation | null = null;
  private rotLoc: WebGLUniformLocation | null = null;
  private bobLoc: WebGLUniformLocation | null = null;
  private ready = false;
  private destroyed = false;

  constructor(gl: WebGL2RenderingContext, spec: LayerSpec) {
    this.gl = gl;
    this.spec = spec;
  }

  async initialize(): Promise<void> {
    const gl = this.gl;
    const program = gl.createProgram();
    if (!program) throw new Error("Could not create program");
    gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERTEX_SOURCE));
    gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAGMENT_SOURCE));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) ?? "program link failed");
    }
    this.program = program;
    this.posLoc = gl.getAttribLocation(program, "a_pos");
    this.uvLoc = gl.getAttribLocation(program, "a_uv");
    this.scaleLoc = gl.getUniformLocation(program, "u_scale");
    this.offsetLoc = gl.getUniformLocation(program, "u_offset");
    this.pivotLoc = gl.getUniformLocation(program, "u_pivot");
    this.rotLoc = gl.getUniformLocation(program, "u_rot");
    this.bobLoc = gl.getUniformLocation(program, "u_bob");
    this.quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    gl.bufferData(gl.ARRAY_BUFFER, QUAD, gl.STATIC_DRAW);

    const files = new Set<string>();
    for (const layer of this.spec.layers) files.add(layer.file);
    for (const file of Object.values(this.spec.face)) files.add(file);
    for (const file of files) {
      const texture = await loadTexture(gl, `/maho/${file}`);
      if (this.destroyed) {
        gl.deleteTexture(texture);
        return;
      }
      this.textures.set(file, texture);
    }
    this.ready = true;
  }

  draw(face: MahoTexture, pose: LayerPose, canvasWidth: number, canvasHeight: number): void {
    if (!this.ready || this.destroyed || !this.program || !this.quad) return;
    const gl = this.gl;
    const canvasAspect = canvasWidth / Math.max(1, canvasHeight);
    const imageAspect = this.spec.width / this.spec.height;
    let scaleX = 1;
    let scaleY = 1;
    if (canvasAspect > imageAspect) scaleX = imageAspect / canvasAspect;
    else scaleY = canvasAspect / imageAspect;
    scaleX *= this.spec.zoom;
    scaleY *= this.spec.zoom;

    gl.disable(gl.DITHER);
    gl.disable(gl.CULL_FACE);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.useProgram(this.program);
    gl.uniform2f(this.scaleLoc, scaleX, scaleY);
    gl.uniform2f(this.offsetLoc, this.spec.viewOffset[0], this.spec.viewOffset[1]);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    gl.enableVertexAttribArray(this.posLoc);
    gl.vertexAttribPointer(this.posLoc, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(this.uvLoc);
    gl.vertexAttribPointer(this.uvLoc, 2, gl.FLOAT, false, 0, 0);

    for (const layer of this.spec.layers) {
      const file = layer.id === "face" ? this.spec.face[face] : layer.file;
      const texture = this.textures.get(file);
      if (!texture) continue;
      const rot = layer.rotate ? pose.faceRot : 0;
      const bob = layer.bob ? pose.torsoBob : 0;
      const pivot: [number, number] = layer.rotate ? this.spec.facePivot : [0.5, 0.5];
      gl.uniform2f(this.pivotLoc, pivot[0], pivot[1]);
      gl.uniform1f(this.rotLoc, rot);
      gl.uniform1f(this.bobLoc, bob);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }
  }

  hitTest(x: number, y: number): boolean {
    if (!this.ready || this.destroyed) return false;
    const gl = this.gl;
    const pixel = new Uint8Array(4);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.readPixels(x, y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    return pixel[3] > 16;
  }

  destroy(): void {
    this.destroyed = true;
    this.ready = false;
    const gl = this.gl;
    for (const texture of this.textures.values()) gl.deleteTexture(texture);
    this.textures.clear();
    if (this.quad) gl.deleteBuffer(this.quad);
    if (this.program) gl.deleteProgram(this.program);
    this.quad = null;
    this.program = null;
  }
}
