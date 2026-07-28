import { SecurityEngine } from '@aegisos/security';
export const sec = new SecurityEngine();
export function evalAccess() {
  return sec.evaluateAccess({ userId: '1', token: '', claims: {} }, 'r1', 'read');
}
