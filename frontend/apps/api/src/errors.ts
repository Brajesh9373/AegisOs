/** Shared API error with HTTP status, machine code, and details. */
export class ApiError extends Error {
  statusCode: number;
  code: string;
  details: any;
  constructor(statusCode: number, code: string, message: string, details: any = null) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
  }
}
