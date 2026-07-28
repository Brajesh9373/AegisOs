import { SecurityEngine } from '@aegisos/security';
export const sec = new SecurityEngine();
export function validateID() {
  return sec.authenticate('token');
}
