/**
 * Base error class for the aegisOS Platform.
 * All custom errors must extend this class to ensure consistent error handling.
 */
export class PlatformError extends Error {
    code;
    isOperational;
    metadata;
    constructor(message, code = 'PLATFORM_ERROR', isOperational = true, metadata) {
        super(message);
        this.name = this.constructor.name;
        this.code = code;
        this.isOperational = isOperational;
        this.metadata = metadata;
        Error.captureStackTrace(this, this.constructor);
    }
}
export class ValidationError extends PlatformError {
    constructor(message, metadata) {
        super(message, 'VALIDATION_ERROR', true, metadata);
    }
}
export class AuthenticationError extends PlatformError {
    constructor(message = 'Authentication failed', metadata) {
        super(message, 'AUTHENTICATION_ERROR', true, metadata);
    }
}
export class AuthorizationError extends PlatformError {
    constructor(message = 'Not authorized to access this resource', metadata) {
        super(message, 'AUTHORIZATION_ERROR', true, metadata);
    }
}
export class ResourceNotFoundError extends PlatformError {
    constructor(resourceType, resourceId) {
        super(`${resourceType} with ID ${resourceId} was not found`, 'RESOURCE_NOT_FOUND', true, {
            resourceType,
            resourceId,
        });
    }
}
export class DependencyResolutionError extends PlatformError {
    constructor(dependencyName) {
        super(`Failed to resolve dependency: ${dependencyName}`, 'DEPENDENCY_RESOLUTION_ERROR', false);
    }
}
