import { SecurityEngine } from '@aegisos/security';
export const sec = new SecurityEngine();
export function encrypt(data: Record<string, string>) {
  return sec.encryptPayload(data);
}
