import { SecurityEngine } from '@aegisos/security';
export const sec = new SecurityEngine();
export function getSec() {
  return sec.getSecretReference('test');
}
