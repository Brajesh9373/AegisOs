import { SecurityEngine } from '@aegisos/security';
export const sec = new SecurityEngine();
export function checkACL() {
  return sec.checkKnowledgeACL('u1', 'n1');
}
