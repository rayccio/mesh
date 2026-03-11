const fs = require("fs");
const path = require("path");

// Settings
const rootDir = __dirname;
const outputFile = path.join(rootDir, "project_export.md");
const outputFileName = path.basename(outputFile);

const ignoredFolders = ['node_modules', 'venv', '.git', '.next', 'dist', 'build'];
const allowedExtensions = ['.js', '.ts', '.tsx', '.json', '.jsonld', '.yml', '.yaml', '.md', '.html', '.css', '.scss', '.txt', '.py', '.sh', '.Dockerfile', 'Dockerfile', '.conf'];

// Helper: Check if a path includes any ignored folder
function isInIgnoredFolder(fullPath) {
  return ignoredFolders.some(folder =>
    fullPath.split(path.sep).includes(folder)
  );
}

// Helper: Recursively get all allowed files
function getAllFiles(dir, fileList = []) {
  let files;
  try {
    files = fs.readdirSync(dir);
  } catch (err) {
    console.error(`❌ Failed to read directory ${dir}:`, err.message);
    return fileList;
  }

  for (const file of files) {
    const fullPath = path.join(dir, file);

    let stat;
    try {
      stat = fs.statSync(fullPath);
    } catch (err) {
      console.error(`❌ Failed to stat ${fullPath}:`, err.message);
      continue;
    }

    const relPath = path.relative(rootDir, fullPath);

    if (stat.isDirectory() && !isInIgnoredFolder(fullPath)) {
      getAllFiles(fullPath, fileList);
    } else if (
      stat.isFile() &&
      allowedExtensions.includes(path.extname(file).toLowerCase()) &&
      ![
        "export.js",
        "package-lock.json",
        outputFileName,
      ].includes(path.basename(file)) &&
      relPath !== "app/globals.css"
    ) {
      fileList.push(fullPath);
    }
  }

  return fileList;
}

// Get all files
const files = getAllFiles(rootDir);

// Write output
const writeStream = fs.createWriteStream(outputFile, { flags: "w" });

writeStream.on("finish", () => {
  console.log(`✅ Project exported to: ${outputFile}`);
});

files.forEach(file => {
  const relativePath = path.relative(rootDir, file);

  let content;
  try {
    content = fs.readFileSync(file, "utf8");
  } catch (err) {
    console.error(`❌ Failed to read file ${file}:`, err.message);
    return;
  }

  const ext = path.extname(file).slice(1) || ""; // get extension without dot

  writeStream.write(`## 📄 ${relativePath}\n\n`);
  writeStream.write("```" + ext + "\n");
  writeStream.write(content);
  writeStream.write("\n```\n\n---\n\n");
});

writeStream.end();

