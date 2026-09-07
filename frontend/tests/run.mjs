import { fileURLToPath } from "node:url";
import { createServer } from "vite";

const root = fileURLToPath(new URL("../", import.meta.url));
const server = await createServer({ root, server: { middlewareMode: true }, appType: "custom" });
try {
  await server.ssrLoadModule("/tests/overlay.test.ts");
  await server.ssrLoadModule("/tests/maho.test.ts");
  await server.ssrLoadModule("/tests/sleepTimer.test.ts");
} finally {
  await server.close();
}
