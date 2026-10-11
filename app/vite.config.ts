import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import type { Connect, Plugin } from "vite";
import { defineConfig } from "vite";

const base = "/project-manager-training-2/";
const dataRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../content",
);
const dataPrefix = `${base}content/`;

const contentTypes: Record<string, string> = {
  ".json": "application/json; charset=utf-8",
  ".webp": "image/webp",
};

function serveExamData(): Plugin {
  const serve: Connect.NextHandleFunction = (req, res, next) => {
    const url = req.url?.split("?")[0] ?? "";
    if (!url.startsWith(dataPrefix)) {
      next();
      return;
    }

    const relative = decodeURIComponent(url.slice(dataPrefix.length));
    const file = path.resolve(dataRoot, relative);
    if (file !== dataRoot && !file.startsWith(`${dataRoot}${path.sep}`)) {
      res.statusCode = 403;
      res.end();
      return;
    }

    fs.stat(file, (error, stat) => {
      if (error || !stat.isFile()) {
        res.statusCode = 404;
        res.end();
        return;
      }
      const type = contentTypes[path.extname(file)] ?? "application/octet-stream";
      res.setHeader("Content-Type", type);
      fs.createReadStream(file).pipe(res);
    });
  };

  return {
    name: "serve-exam-data",
    configureServer(server) {
      server.middlewares.use(serve);
    },
    configurePreviewServer(server) {
      server.middlewares.use(serve);
    },
    closeBundle() {
      const dist = path.resolve("dist");
      fs.cpSync(dataRoot, path.resolve(dist, "content"), { recursive: true });
      fs.copyFileSync(path.resolve(dist, "index.html"), path.resolve(dist, "404.html"));
    },
  };
}

export default defineConfig({
  base,
  plugins: [react(), serveExamData()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
