import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const distPath = path.join(projectRoot, 'dist');

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const makeWritable = async (targetPath) => {
  try {
    const entries = await fs.readdir(targetPath, { withFileTypes: true });

    await Promise.all(entries.map(async (entry) => {
      const entryPath = path.join(targetPath, entry.name);

      if (entry.isDirectory()) {
        await makeWritable(entryPath);
      }

      await fs.chmod(entryPath, 0o666).catch(() => {});
    }));
  } catch {
    return;
  }
};

for (let attempt = 1; attempt <= 5; attempt += 1) {
  try {
    await makeWritable(distPath);
    await fs.rm(distPath, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
    await fs.mkdir(distPath, { recursive: true });
    process.exit(0);
  } catch (error) {
    if (attempt === 5) {
      console.error(`Could not prepare Vite output directory: ${error.message}`);
      process.exit(1);
    }

    await wait(250 * attempt);
  }
}
