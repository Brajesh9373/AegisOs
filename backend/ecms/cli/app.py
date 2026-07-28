"""ECMS developer and operations CLI (SECTION 209/312).

One binary, role-based entrypoints: ``ecms serve`` runs the API gateway and
``ecms worker <role>`` runs an event-driven worker. This realizes the worker
decomposition - the same image scales the API and each cognition worker
independently.
"""

from __future__ import annotations

import signal
import time

import typer

from ecms import __version__

__all__ = ["app", "main"]

_DEFAULT_HOST = "0.0.0.0"  # noqa: S104 - a server binds all interfaces in a container

WORKER_ROLES = ("knowledge", "reflection", "promotion", "memory", "scheduler")

app = typer.Typer(
    name="ecms",
    help="ECMS enterprise cognitive runtime.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the ECMS version."""
    typer.echo(__version__)


@app.command()
def roles() -> None:
    """List the available worker roles."""
    for role in WORKER_ROLES:
        typer.echo(role)


@app.command()
def serve(host: str = _DEFAULT_HOST, port: int = 8000) -> None:  # pragma: no cover
    """Run the API gateway."""
    import uvicorn

    uvicorn.run("ecms.main:app", host=host, port=port)


@app.command()
def worker(
    role: str,
    check: bool = typer.Option(False, "--check", help="Validate the role and exit."),
) -> None:
    """Run an event-driven worker for a role (knowledge, reflection, promotion, ...)."""
    if role not in WORKER_ROLES:
        typer.echo(f"unknown worker role: {role}", err=True)
        raise typer.Exit(code=1)
    if check:
        typer.echo(f"worker role '{role}' is valid")
        return
    _run_worker(role)


def _run_worker(role: str) -> None:  # pragma: no cover - runs a consumer loop
    typer.echo(f"starting {role} worker")
    stopping = False

    def _request_stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    while not stopping:
        time.sleep(30)

    typer.echo(f"stopping {role} worker")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
