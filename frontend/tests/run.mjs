import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

const root = fileURLToPath(new URL("../", import.meta.url));
const extent = spawnSync("python3", ["tests/layer_extent.py"], { cwd: root, encoding: "utf8" });
if (extent.status !== 0) {
  throw new Error(extent.stdout + extent.stderr);
}
process.stdout.write(extent.stdout);

const server = await createServer({ root, server: { middlewareMode: true }, appType: "custom" });
try {
  await server.ssrLoadModule("/tests/overlay.test.ts");
  await server.ssrLoadModule("/tests/maho.test.ts");
  await server.ssrLoadModule("/tests/sleepTimer.test.ts");
} finally {
  await server.close();
}
