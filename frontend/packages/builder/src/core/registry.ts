import { BuilderSession } from './session.js';
import { PlatformError } from '@aegisos/shared';

export class BuilderNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Builder Session ${id} not found`);
  }
}

export class BuilderRegistry {
  private sessions = new Map<string, BuilderSession>();

  public register(session: BuilderSession): void {
    this.sessions.set(session.sessionId, session);
  }

  public get(id: string): BuilderSession {
    const session = this.sessions.get(id);
    if (!session) {
      throw new BuilderNotFoundError(id);
    }
    return session;
  }

  public getAll(): BuilderSession[] {
    return Array.from(this.sessions.values());
  }

  public remove(id: string): void {
    this.sessions.delete(id);
  }
}
