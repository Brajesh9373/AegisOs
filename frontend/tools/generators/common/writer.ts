
import * as fs from 'fs';
import * as path from 'path';
import { formatSource } from './formatter';
import { validateOutput } from './validator';

export interface IWriteOptions {
    filePath: string;
    content: string;
    autoFormat?: boolean;
}

/**
 * Writes the content to the specified file using UTF-8 encoding.
 * Ensures parent directories exist.
 * Applies formatting and verification hooks before writing.
 */
export async function writeGeneratedFile(options: IWriteOptions): Promise<void> {
    const { filePath, content, autoFormat = true } = options;
    
    // Validate AST/Content sanity
    await validateOutput(content);
    
    let finalContent = content;
    if (autoFormat) {
        finalContent = await formatSource(content, filePath);
    }
    
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
    
    // UTF-8 Output ONLY
    fs.writeFileSync(filePath, finalContent, 'utf8');
}
