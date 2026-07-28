import { CanvasModel } from './canvas.js';
import { BuilderStateTracker } from './tracking.js';
import { BuilderValidationEngine } from './validation.js';

export class BuilderSession {
  public canvas: CanvasModel;
  private tracker: BuilderStateTracker;
  private validator: BuilderValidationEngine;

  constructor(
    public sessionId: string,
    initialCanvas?: CanvasModel,
  ) {
    this.tracker = new BuilderStateTracker();
    this.validator = new BuilderValidationEngine();
    this.canvas = initialCanvas || { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } };
    this.tracker.pushState(this.canvas);
  }

  public updateCanvas(canvas: CanvasModel): void {
    this.validator.validate(canvas);
    this.canvas = canvas;
    this.tracker.pushState(this.canvas);
  }

  public undo(): void {
    const prevState = this.tracker.undo();
    if (prevState) this.canvas = prevState;
  }

  public redo(): void {
    const nextState = this.tracker.redo();
    if (nextState) this.canvas = nextState;
  }
}
