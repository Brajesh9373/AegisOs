
/**
 * Ensures generated output does not contain structural bugs (like unescaped literals).
 */
export async function validateOutput(source: string): Promise<void> {
    if (source.includes('\\n')) {
        throw new Error('Code generation error: Output contains literal escaped newline sequences');
    }
    if (source.includes('export interface') && source.includes('{}')) {
        throw new Error('Code generation error: Output contains forbidden empty interfaces');
    }
}
