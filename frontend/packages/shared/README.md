# @aegis/shared

The foundational package for the aegisOS platform.

## Responsibilities

This package contains 100% reusable, agnostic infrastructure utilities. It strictly contains zero business logic, zero AI logic, and zero framework coupling.

Every other package in the aegisOS monorepo may depend on this package. This package depends on NOTHING.

## Modules

- **Core**: Contains `Result<T, E>` and `BaseError`.
- **Utils**: Contains pure utility functions for `uuid`, `string`, `object`, and `array`.
- **Async**: Contains `retry` and `Disposable` patterns.
- **Models**: Contains `Pagination` shapes and `Enums`.
- **Env**: Contains standard environment helpers.
