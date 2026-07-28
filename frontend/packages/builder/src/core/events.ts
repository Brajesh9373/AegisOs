export enum BuilderEventType {
  SessionStarted = 'builder.session.started',
  SessionSaved = 'builder.session.saved',
  NodeAdded = 'builder.node.added',
  EdgeAdded = 'builder.edge.added',
  UndoPerformed = 'builder.undo',
  RedoPerformed = 'builder.redo',
}

export interface BuilderEvent {
  type: BuilderEventType;
  sessionId: string;
  timestamp: Date;
  payload?: Record<string, unknown>;
}
