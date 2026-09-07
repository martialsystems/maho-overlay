export type UvRect = { u0: number; v0: number; u1: number; v1: number };

export type MeshSpec = {
  width: number;
  height: number;
  cols: number;
  rows: number;
  groups: Record<string, UvRect>;
  bones: Record<string, { pivot: [number, number]; groups: string[] }>;
  textures: Record<string, string>;
};

export type SkinnedMesh = {
  rest: Float32Array;
  uv: Float32Array;
  indices: Uint16Array;
  group: Uint8Array;
  groupNames: string[];
};

/** Tightest part wins so the cat is not skinned with the chest. */
const GROUP_PRIORITY = ["eyes", "face", "plush", "arms", "head", "body"] as const;

export function containsUv(rect: UvRect, u: number, v: number): boolean {
  return u >= rect.u0 && u <= rect.u1 && v >= rect.v0 && v <= rect.v1;
}

export function groupIndexAt(spec: MeshSpec, u: number, v: number): number {
  for (const name of GROUP_PRIORITY) {
    const rect = spec.groups[name];
    if (rect && containsUv(rect, u, v)) return GROUP_PRIORITY.indexOf(name);
  }
  return GROUP_PRIORITY.indexOf("body");
}

export function buildGridMesh(spec: MeshSpec): SkinnedMesh {
  const cols = spec.cols;
  const rows = spec.rows;
  const vertsX = cols + 1;
  const vertsY = rows + 1;
  const vertCount = vertsX * vertsY;
  const rest = new Float32Array(vertCount * 2);
  const uv = new Float32Array(vertCount * 2);
  const group = new Uint8Array(vertCount);

  for (let j = 0; j <= rows; j++) {
    const v = j / rows;
    for (let i = 0; i <= cols; i++) {
      const u = i / cols;
      const index = j * vertsX + i;
      rest[index * 2] = u;
      rest[index * 2 + 1] = v;
      uv[index * 2] = u;
      uv[index * 2 + 1] = v;
      group[index] = groupIndexAt(spec, u, v);
    }
  }

  const indices = new Uint16Array(cols * rows * 6);
  let cursor = 0;
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const a = j * vertsX + i;
      const b = a + 1;
      const c = a + vertsX;
      const d = c + 1;
      indices[cursor++] = a;
      indices[cursor++] = c;
      indices[cursor++] = b;
      indices[cursor++] = b;
      indices[cursor++] = c;
      indices[cursor++] = d;
    }
  }

  return {
    rest,
    uv,
    indices,
    group,
    groupNames: [...GROUP_PRIORITY],
  };
}

export type BonePose = {
  faceRot: number;
  hairSway: number;
  torsoBob: number;
  armBob: number;
  plushBob: number;
  shakeX: number;
};

function applyRotate(
  u: number,
  v: number,
  pivot: [number, number],
  cos: number,
  sin: number,
): [number, number] {
  const dx = u - pivot[0];
  const dy = v - pivot[1];
  return [pivot[0] + dx * cos - dy * sin, pivot[1] + dx * sin + dy * cos];
}

export function skinVertices(
  spec: MeshSpec,
  mesh: SkinnedMesh,
  pose: BonePose,
  out: Float32Array,
): void {
  const facePivot = spec.bones.face?.pivot ?? spec.bones.head.pivot;
  const hairPivot = spec.bones.head.pivot;
  const faceCos = Math.cos(pose.faceRot);
  const faceSin = Math.sin(pose.faceRot);
  const hairCos = Math.cos(pose.hairSway);
  const hairSin = Math.sin(pose.hairSway);

  for (let i = 0; i < mesh.group.length; i++) {
    let u = mesh.rest[i * 2] + pose.shakeX;
    let v = mesh.rest[i * 2 + 1];
    const name = mesh.groupNames[mesh.group[i]] ?? "body";

    if (name === "face" || name === "eyes") {
      [u, v] = applyRotate(u, v, facePivot, faceCos, faceSin);
    } else if (name === "head") {
      [u, v] = applyRotate(u, v, hairPivot, hairCos, hairSin);
    } else if (name === "body") {
      v += pose.torsoBob;
    } else if (name === "plush") {
      v += pose.plushBob;
    } else if (name === "arms") {
      v += pose.armBob;
    }

    out[i * 2] = u;
    out[i * 2 + 1] = v;
  }
}
