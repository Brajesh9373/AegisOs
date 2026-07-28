import { CanvasModel } from './canvas.js';
import { BuilderSerialization } from './serialization.js';

export class BuilderStateTracker {
  private history: string[] = [];
  private currentIndex: number = -1;
  private serializer = new BuilderSerialization();

  public pushState(canvas: CanvasModel): void {
    const serialized = this.serializer.export(canvas);
    this.history = this.history.slice(0, this.currentIndex + 1);
    this.history.push(serialized);
    this.currentIndex++;
  }

  public undo(): CanvasModel | null {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      return this.serializer.import(this.history[this.currentIndex]);
    }
    return null;
  }

  public redo(): CanvasModel | null {
    if (this.currentIndex < this.history.length - 1) {
      this.currentIndex++;
      return this.serializer.import(this.history[this.currentIndex]);
    }
    return null;
  }
}
