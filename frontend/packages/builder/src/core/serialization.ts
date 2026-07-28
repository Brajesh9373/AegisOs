import { CanvasModel } from './canvas.js';

export class BuilderSerialization {
  public export(canvas: CanvasModel): string {
    return JSON.stringify(canvas, null, 2);
  }

  public import(payload: string): CanvasModel {
    return JSON.parse(payload) as CanvasModel;
  }
}
