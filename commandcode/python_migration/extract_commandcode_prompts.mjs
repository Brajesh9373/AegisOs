import fs from "node:fs";

const bundlePath = process.argv[2];
if (!bundlePath) {
  console.error("Usage: node extract_commandcode_prompts.mjs <dist/cli.mjs>");
  process.exit(2);
}

const source = fs.readFileSync(bundlePath, "utf8");

function readStringLiteral(start) {
  const quote = source[start];
  let i = start + 1;
  let escaped = false;

  while (i < source.length) {
    const ch = source[i];
    if (escaped) {
      escaped = false;
      i++;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      i++;
      continue;
    }
    if (ch === quote) {
      const raw = source.slice(start, i + 1);
      return { raw, end: i };
    }
    i++;
  }

  return null;
}

function evaluateLiteral(raw) {
  return Function(`"use strict"; return (${raw});`)();
}

const items = [];
for (const pattern of ["systemPrompt:", "system:"]) {
  let idx = 0;
  while ((idx = source.indexOf(pattern, idx)) !== -1) {
    let j = idx + pattern.length;
    while (j < source.length && /\s/.test(source[j])) j++;

    if (source[j] === "'" || source[j] === '"') {
      const literal = readStringLiteral(j);
      if (literal) {
        items.push({
          kind: pattern.slice(0, -1),
          index: idx,
          chars: literal.raw.length,
          text: evaluateLiteral(literal.raw),
        });
        idx = literal.end + 1;
        continue;
      }
    }

    idx += pattern.length;
  }
}

for (const item of items.sort((a, b) => a.index - b.index)) {
  console.log(`===== ${item.kind} at ${item.index} chars=${item.chars} =====`);
  console.log(item.text);
  console.log();
}
