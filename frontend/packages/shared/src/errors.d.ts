/**
 * Base error class for the aegisOS Platform.
 * All custom errors must extend this class to ensure consistent error handling.
 */
export declare class PlatformError extends Error {
    readonly code: string;
    readonly isOperational: boolean;
    readonly metadata?: Record<string, unknown>;
    constructor(message: string, code?: string, isOperational?: boolean, metadata?: Record<string, unknown>);
}
export declare class ValidationError extends PlatformError {
    constructor(message: string, metadata?: Record<string, unknown>);
}
export declare class AuthenticationError extends PlatformError {
    constructor(message?: string, metadata?: Record<string, unknown>);
}
export declare class AuthorizationError extends PlatformError {
    constructor(message?: string, metadata?: Record<string, unknown>);
}
export declare class ResourceNotFoundError extends PlatformError {
    constructor(resourceType: string, resourceId: string);
}
export declare class DependencyResolutionError extends PlatformError {
    constructor(dependencyName: string);
}
