import { buildGridMesh, skinVertices, type BonePose, type MeshSpec, type SkinnedMesh } from "./buildMesh";
import type { MahoTexture } from "./motion";

const VERTEX_SOURCE = `#version 300 es
in vec2 a_pos;
in vec2 a_uv;
uniform vec2 u_scale;
uniform vec2 u_offset;
out vec2 v_uv;
void main() {
  vec2 p = (a_pos - 0.5) * u_scale + 0.5 + u_offset;
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
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
      gl.generateMipmap(gl.TEXTURE_2D);
      const anisotropic = gl.getExtension("EXT_texture_filter_anisotropic");
      if (anisotropic) {
        const max = gl.getParameter(anisotropic.MAX_TEXTURE_MAX_ANISOTROPY_EXT) as number;
        gl.texParameterf(
          gl.TEXTURE_2D,
          anisotropic.TEXTURE_MAX_ANISOTROPY_EXT,
          Math.min(8, max),
        );
      }
      resolve(texture);
    };
    image.onerror = () => reject(new Error(`Failed to load ${url}`));
    image.src = url;
  });
}

export class MahoMeshPlayer {
  private readonly gl: WebGL2RenderingContext;
  private readonly spec: MeshSpec;
  private readonly mesh: SkinnedMesh;
  private readonly skinned: Float32Array;
  private program: WebGLProgram | null = null;
  private posBuffer: WebGLBuffer | null = null;
  private uvBuffer: WebGLBuffer | null = null;
  private indexBuffer: WebGLBuffer | null = null;
  private textures = new Map<MahoTexture, WebGLTexture>();
  private posLoc = -1;
  private uvLoc = -1;
  private scaleLoc: WebGLUniformLocation | null = null;
  private offsetLoc: WebGLUniformLocation | null = null;
  private ready = false;
  private destroyed = false;

  constructor(gl: WebGL2RenderingContext, spec: MeshSpec) {
    this.gl = gl;
    this.spec = spec;
    this.mesh = buildGridMesh(spec);
    this.skinned = new Float32Array(this.mesh.rest.length);
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

    this.posBuffer = gl.createBuffer();
    this.uvBuffer = gl.createBuffer();
    this.indexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.uvBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, this.mesh.uv, gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, this.mesh.indices, gl.STATIC_DRAW);

    const idle = await loadTexture(gl, this.spec.textures.idle);
    const closed = await loadTexture(gl, this.spec.textures["eyes-closed"]);
    const angry = await loadTexture(gl, this.spec.textures.angry);
    if (this.destroyed) {
      gl.deleteTexture(idle);
      gl.deleteTexture(closed);
      gl.deleteTexture(angry);
      return;
    }
    this.textures.set("idle", idle);
    this.textures.set("eyes-closed", closed);
    this.textures.set("angry", angry);
    this.ready = true;
  }

  draw(texture: MahoTexture, pose: BonePose, canvasWidth: number, canvasHeight: number): void {
    if (!this.ready || this.destroyed || !this.program) return;
    const gl = this.gl;
    skinVertices(this.spec, this.mesh, pose, this.skinned);

    const canvasAspect = canvasWidth / Math.max(1, canvasHeight);
    const imageAspect = this.spec.width / this.spec.height;
    let scaleX = 1;
    let scaleY = 1;
    if (canvasAspect > imageAspect) scaleX = imageAspect / canvasAspect;
    else scaleY = canvasAspect / imageAspect;
    const zoom = 0.72;
    scaleX *= zoom;
    scaleY *= zoom;

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.useProgram(this.program);
    gl.uniform2f(this.scaleLoc, scaleX, scaleY);
    gl.uniform2f(this.offsetLoc, 0, 0.05);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.posBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, this.skinned, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(this.posLoc);
    gl.vertexAttribPointer(this.posLoc, 2, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.uvBuffer);
    gl.enableVertexAttribArray(this.uvLoc);
    gl.vertexAttribPointer(this.uvLoc, 2, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.textures.get(texture) ?? null);
    gl.drawElements(gl.TRIANGLES, this.mesh.indices.length, gl.UNSIGNED_SHORT, 0);
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
    if (this.posBuffer) gl.deleteBuffer(this.posBuffer);
    if (this.uvBuffer) gl.deleteBuffer(this.uvBuffer);
    if (this.indexBuffer) gl.deleteBuffer(this.indexBuffer);
    if (this.program) gl.deleteProgram(this.program);
    this.posBuffer = null;
    this.uvBuffer = null;
    this.indexBuffer = null;
    this.program = null;
  }
}
