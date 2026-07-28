import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

// Dynamically create aliases for all @aegisos packages to point to their src/index.ts
const packagesDir = path.resolve(__dirname, '../../packages');
const packages = fs.readdirSync(packagesDir).filter(p => fs.statSync(path.join(packagesDir, p)).isDirectory());
const aliases = packages.reduce((acc, pkg) => {
  acc[`@aegisos/${pkg}`] = path.resolve(packagesDir, pkg, 'src/index.ts');
  return acc;
}, {} as Record<string, string>);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: aliases
  },
  server: {
    port: 5173
  }
});
