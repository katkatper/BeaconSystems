import fs from "node:fs";

const reportPath = process.argv[2] ?? "browser-test.log";
const log = fs.readFileSync(reportPath, "utf8");
const lines = log.split(/\r?\n/);
const selected = [];

for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^\s*\d+\) \[[^\]]+\] /.test(line)) {
        selected.push(line.trim());
        for (let offset = 1; offset <= 8 && index + offset < lines.length; offset += 1) {
            const detail = lines[index + offset];
            if (/^\s*(Error:|Test timeout|Expected:|Received:)/.test(detail)) {
                selected.push(`  ${detail.trim()}`);
            }
        }
    }
}

const summary = selected.length > 0
    ? selected.join("\n")
    : lines.slice(-100).join("\n");
const escaped = summary
    .replaceAll("%", "%25")
    .replaceAll("\r", "%0D")
    .replaceAll("\n", "%0A");

console.log(`::error title=Browser matrix failure::${escaped}`);
