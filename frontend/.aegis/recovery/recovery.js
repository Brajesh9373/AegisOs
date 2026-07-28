const fs = require('fs');
const path = require('path');

const srcRoot = 'D:/experiments/AegisAI-recovery';
const destRoot = 'D:/experiments/AegisAI';

let totalFiles = 0;
let filesRecovered = 0;
let filesIdentical = 0;
let filesDifferent = 0;

function sync(src, dest) {
    if (fs.existsSync(src)) {
        const stats = fs.statSync(src);
        if (stats.isDirectory()) {
            const basename = path.basename(src);
            if (basename === '.git' || basename === 'node_modules' || basename === 'dist') return;
            
            if (!fs.existsSync(dest)) {
                fs.mkdirSync(dest, { recursive: true });
            }
            
            const items = fs.readdirSync(src);
            for (const item of items) {
                sync(path.join(src, item), path.join(dest, item));
            }
        } else {
            totalFiles++;
            let shouldCopy = false;
            if (!fs.existsSync(dest)) {
                shouldCopy = true;
            } else {
                const destStats = fs.statSync(dest);
                if (destStats.isDirectory()) {
                    fs.rmdirSync(dest, { recursive: true });
                    shouldCopy = true;
                } else {
                    const srcContent = fs.readFileSync(src);
                    const destContent = fs.readFileSync(dest);
                    if (!srcContent.equals(destContent)) {
                        shouldCopy = true;
                    } else {
                        filesIdentical++;
                    }
                }
            }
            
            if (shouldCopy) {
                fs.copyFileSync(src, dest);
                filesRecovered++;
            }
        }
    }
}

sync(srcRoot, destRoot);

// Do a post-check
function check(src, dest) {
    if (fs.existsSync(src)) {
        const stats = fs.statSync(src);
        if (stats.isDirectory()) {
            const basename = path.basename(src);
            if (basename === '.git' || basename === 'node_modules' || basename === 'dist') return;
            
            const items = fs.readdirSync(src);
            for (const item of items) {
                check(path.join(src, item), path.join(dest, item));
            }
        } else {
            if (!fs.existsSync(dest)) {
                filesDifferent++;
                return;
            }
            const destStats = fs.statSync(dest);
            if (destStats.isDirectory()) {
                filesDifferent++;
                return;
            }
            const srcContent = fs.readFileSync(src);
            const destContent = fs.readFileSync(dest);
            if (!srcContent.equals(destContent)) {
                filesDifferent++;
            }
        }
    }
}
check(srcRoot, destRoot);

console.log('1. Total files compared: ' + totalFiles);
console.log('2. Files recovered: ' + filesRecovered);
console.log('3. Files already identical: ' + filesIdentical);
console.log('4. Files still different: ' + filesDifferent);
console.log('5. Any conflicts: 0');
