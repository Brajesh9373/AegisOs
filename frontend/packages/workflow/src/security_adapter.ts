import { SecurityEngine } from '@aegisos/security';
export const sec = new SecurityEngine();
export function filterPrompt(p: string) {
  return sec.redact(p);
}
