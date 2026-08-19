import { rm } from "node:fs/promises";

for (const path of [".next", ".turbo"]) {
  await rm(path, { recursive: true, force: true });
}
console.log("AegisOS build cache cleared.");
