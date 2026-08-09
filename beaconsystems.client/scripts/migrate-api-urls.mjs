import fs from "node:fs";
import path from "node:path";


const pagesDirectory = path.resolve("src/pages");
const excludedFiles = new Set(process.argv.slice(2));
const files = fs.readdirSync(pagesDirectory)
    .filter((fileName) => fileName.endsWith(".jsx"))
    .filter((fileName) => !excludedFiles.has(fileName));

for (const fileName of files) {
    const filePath = path.join(pagesDirectory, fileName);
    const original = fs.readFileSync(filePath, "utf8");
    let updated = original
        .replace(
            /"http:\/\/127\.0\.0\.1:8000([^"\r\n]*)"/g,
            (_, route) => `apiUrl("${route}")`,
        )
        .replace(
            /`http:\/\/127\.0\.0\.1:8000([^`]*)`/g,
            (_, route) => `apiUrl(\`${route}\`)`,
        );

    if (updated === original) {
        continue;
    }

    const apiImportPattern = /import\s*\{([^}]*)\}\s*from\s*["']\.\.\/api\.jsx["'];?/;
    const existingApiImport = updated.match(apiImportPattern);

    if (existingApiImport) {
        const imports = existingApiImport[1]
            .split(",")
            .map((name) => name.trim())
            .filter(Boolean);

        if (!imports.includes("apiUrl")) {
            imports.push("apiUrl");
        }

        updated = updated.replace(
            apiImportPattern,
            `import { ${imports.join(", ")} } from "../api.jsx";`,
        );
    } else {
        updated = `import { apiUrl } from "../api.jsx";\n${updated}`;
    }

    fs.writeFileSync(filePath, updated, "utf8");
    process.stdout.write(`Updated ${fileName}\n`);
}
