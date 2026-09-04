"""Executable native-versus-DSH Business Analyst benchmark.

Run directly after setting the GLM-5 Anthropic gateway environment variables:
    PYTHONPATH=backend python backend/tests/test_ba_benchmark.py

The module is deliberately not a pytest test: it performs live model calls and
writes its report outside the repository by default.
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("benchmark.ba_comparison")

TEST_CASES = [
    {
        "name": "Simple Migration Project",
        "source": """
Create a workspace for migrating 450 MySQL tables from Adrenaline HR to Frappe HR.
The system needs to handle real-time sync with <2s latency and support 500 concurrent users.
        """,
    },
    {
        "name": "Complex Integration Project",
        "source": """
Build a vendor invoice approval system that:
- Ingests invoices from Gmail and Outlook mailboxes
- Matches invoices against purchase orders in SAP
- Routes approvals based on amount thresholds
- Supports dual-write back to ERP
- Must comply with GDPR and SOC2
- Requires PII encryption at rest and in transit
        """,
    },
    {
        "name": "Ambiguous Requirements",
        "source": """
We need a real-time dashboard for our sales team that shows customer data.
It should be fast and secure.
        """,
    },
]

STAGES = ("understand", "clarify", "finalize")


@dataclass(slots=True)
class BenchmarkResult:
    """Outcome for one stage that was actually attempted."""

    test_name: str
    agent_type: str
    stage: str
    latency_seconds: float
    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_report(self) -> dict[str, Any]:
        """Serialize non-sensitive benchmark metrics and diagnostics."""
        return {
            "stage": self.stage,
            "latency_seconds": self.latency_seconds,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


class BAAgentBenchmark:
    """Run comparable staged BA workflows against native AegisOS and real DSH."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or (Path(tempfile.gettempdir()) / "aegisos-ba-benchmark")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _result(
        test_case: dict[str, str],
        agent_type: str,
        stage: str,
        started: float,
        *,
        output: dict[str, Any] | None = None,
        error: Exception | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        return BenchmarkResult(
            test_name=test_case["name"],
            agent_type=agent_type,
            stage=stage,
            latency_seconds=time.perf_counter() - started,
            success=error is None,
            output=output,
            error=str(error) if error else None,
            metadata=metadata or {},
        )

    async def benchmark_native_agent(self, test_case: dict[str, str]) -> list[BenchmarkResult]:
        """Run the native BA stages, stopping after the first failed dependency."""
        from ecms.agent.ba.agent import clarify, finalize, retrieve_knowledge, understand

        results: list[BenchmarkResult] = []
        source = test_case["source"]
        knowledge: str | None = None

        logger.info("[Native] Running understand for %s", test_case["name"])
        started = time.perf_counter()
        try:
            knowledge = await retrieve_knowledge(source)
            recap = await understand(source, knowledge)
        except Exception as exc:
            results.append(self._result(test_case, "native", "understand", started, error=exc))
            return results
        results.append(
            self._result(
                test_case,
                "native",
                "understand",
                started,
                output={"message": recap},
                metadata={"includes_knowledge_retrieval": True},
            )
        )

        logger.info("[Native] Running clarify")
        started = time.perf_counter()
        try:
            clarification = await clarify(source, knowledge)
        except Exception as exc:
            results.append(self._result(test_case, "native", "clarify", started, error=exc))
            return results
        results.append(
            self._result(
                test_case,
                "native",
                "clarify",
                started,
                output=clarification,
            )
        )

        conversation = [
            {"role": "assistant", "content": clarification["content"]},
            {"role": "user", "content": "Proceed with these requirements."},
        ]
        logger.info("[Native] Running finalize with clarification history")
        started = time.perf_counter()
        try:
            requirements = await finalize(source, conversation, knowledge)
        except Exception as exc:
            results.append(self._result(test_case, "native", "finalize", started, error=exc))
            return results
        results.append(
            self._result(
                test_case,
                "native",
                "finalize",
                started,
                output=requirements.to_frontend(),
            )
        )
        return results

    async def benchmark_dsh_agent(self, test_case: dict[str, str]) -> list[BenchmarkResult]:
        """Run strict BA stage helpers through one real DSH profile runtime."""
        from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
        from ecms.agent.dsh_runtime import (
            DSHRuntime,
            ba_clarify,
            ba_finalize,
            ba_understand,
        )

        results: list[BenchmarkResult] = []
        source = test_case["source"]
        timing_note = (
            "End-to-end wall time; includes profile synchronization and DSH CLI "
            "launch plus model/gateway execution. It is not a model-only latency."
        )

        # An isolated DSH home prevents a stale user-local generated cordis.yml
        # from affecting benchmark composition while keeping all stage calls in
        # this one scenario on the same real DSH profile state.
        with tempfile.TemporaryDirectory(prefix="aegisos-dsh-benchmark-") as home:
            dsh_home = Path(home)
            runtime = DSHRuntime(
                profile_spec=business_analyst_dsh_profile_spec(),
                timeout=120,
                dsh_home=dsh_home,
            )
            runtime_kwargs = {
                "dsh_executable": runtime.dsh_executable,
                "dsh_home": dsh_home,
            }

            logger.info("[DSH] Running understand for %s", test_case["name"])
            started = time.perf_counter()
            try:
                recap = await ba_understand(source, **runtime_kwargs)
            except Exception as exc:
                results.append(self._result(test_case, "dsh", "understand", started, error=exc))
                return results
            results.append(
                self._result(
                    test_case,
                    "dsh",
                    "understand",
                    started,
                    output={"message": recap},
                    metadata={"latency_scope": timing_note},
                )
            )

            logger.info("[DSH] Running strict clarify")
            started = time.perf_counter()
            try:
                clarification = await ba_clarify(source, **runtime_kwargs)
            except Exception as exc:
                results.append(self._result(test_case, "dsh", "clarify", started, error=exc))
                return results
            results.append(
                self._result(
                    test_case,
                    "dsh",
                    "clarify",
                    started,
                    output=clarification,
                    metadata={"latency_scope": timing_note},
                )
            )

            conversation = [
                {"role": "assistant", "content": clarification["content"]},
                {"role": "user", "content": "Proceed with these requirements."},
            ]
            logger.info("[DSH] Running strict finalize with clarification history")
            started = time.perf_counter()
            try:
                requirements = await ba_finalize(source, conversation, **runtime_kwargs)
            except Exception as exc:
                results.append(self._result(test_case, "dsh", "finalize", started, error=exc))
                return results
            results.append(
                self._result(
                    test_case,
                    "dsh",
                    "finalize",
                    started,
                    output=requirements,
                    metadata={"latency_scope": timing_note},
                )
            )
        return results

    @staticmethod
    def analyze_results(
        native_results: list[BenchmarkResult],
        dsh_results: list[BenchmarkResult],
        test_case: dict[str, str],
    ) -> dict[str, Any]:
        """Compare only stages that both implementations actually attempted."""
        comparison: dict[str, Any] = {}
        for stage in STAGES:
            native = next((item for item in native_results if item.stage == stage), None)
            dsh = next((item for item in dsh_results if item.stage == stage), None)
            if native is None or dsh is None:
                continue
            comparison[stage] = {
                "native_latency_seconds": native.latency_seconds,
                "dsh_latency_seconds": dsh.latency_seconds,
                "latency_difference_seconds": dsh.latency_seconds - native.latency_seconds,
                "latency_difference_percent": (
                    (dsh.latency_seconds - native.latency_seconds) / native.latency_seconds * 100
                    if native.latency_seconds
                    else None
                ),
                "native_success": native.success,
                "dsh_success": dsh.success,
            }

        native_finalize = next(
            (item for item in native_results if item.stage == "finalize" and item.success),
            None,
        )
        dsh_finalize = next(
            (item for item in dsh_results if item.stage == "finalize" and item.success),
            None,
        )
        if native_finalize and dsh_finalize:
            native_output = native_finalize.output or {}
            dsh_output = dsh_finalize.output or {}
            comparison["quality"] = {
                "native_phase_count": len(native_output.get("phases", [])),
                "dsh_phase_count": len(dsh_output.get("phases", [])),
                "native_skill_count": len(native_output.get("skills", [])),
                "dsh_skill_count": len(dsh_output.get("skills", [])),
                "native_governance_count": len(native_output.get("governance", [])),
                "dsh_governance_count": len(dsh_output.get("governance", [])),
            }
        return {"test_name": test_case["name"], "comparison": comparison}

    async def run_benchmarks(self) -> dict[str, Any]:
        """Run the fixed test corpus and persist a report outside the source tree."""
        test_cases: list[dict[str, Any]] = []
        all_native_results: list[BenchmarkResult] = []
        all_dsh_results: list[BenchmarkResult] = []

        for test_case in TEST_CASES:
            logger.info("=" * 80)
            logger.info("Test case: %s", test_case["name"])
            native_results = await self.benchmark_native_agent(test_case)
            dsh_results = await self.benchmark_dsh_agent(test_case)
            all_native_results.extend(native_results)
            all_dsh_results.extend(dsh_results)
            test_cases.append(
                {
                    "name": test_case["name"],
                    "native_results": [item.to_report() for item in native_results],
                    "dsh_results": [item.to_report() for item in dsh_results],
                    "analysis": self.analyze_results(native_results, dsh_results, test_case),
                }
            )

        def aggregate(results: list[BenchmarkResult]) -> dict[str, float | int]:
            attempted = len(results)
            successes = sum(item.success for item in results)
            total_latency = sum(item.latency_seconds for item in results)
            return {
                "attempted_stages": attempted,
                "successful_stages": successes,
                "average_latency_seconds": total_latency / attempted if attempted else 0.0,
                "success_rate_percent": successes / attempted * 100 if attempted else 0.0,
            }

        report = {
            "test_cases": test_cases,
            "summary": {
                "total_tests": len(TEST_CASES),
                "native": aggregate(all_native_results),
                "dsh": aggregate(all_dsh_results),
                "latency_interpretation": (
                    "DSH timings include profile synchronization, CLI launch, and "
                    "model/gateway execution. Native timings include its retrieval and "
                    "in-process orchestration. This benchmark does not claim model-only "
                    "latency from either path."
                ),
            },
        }
        output_file = self.output_dir / "benchmark_results.json"
        output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_file"] = str(output_file)
        return report

    @staticmethod
    def print_report(report: dict[str, Any]) -> None:
        """Print a concise summary while retaining full failure details in JSON."""
        summary = report["summary"]
        print("=" * 80)
        print("BA Agent Benchmark: Native AegisOS vs real DSH")
        print("=" * 80)
        for agent_type in ("native", "dsh"):
            metrics = summary[agent_type]
            print(
                f"{agent_type.title()}: {metrics['successful_stages']}/"
                f"{metrics['attempted_stages']} attempted stages succeeded "
                f"({metrics['success_rate_percent']:.1f}%); average "
                f"{metrics['average_latency_seconds']:.2f}s"
            )
        print(summary["latency_interpretation"])
        print(f"Full report: {report['output_file']}")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    benchmark = BAAgentBenchmark()
    report = await benchmark.run_benchmarks()
    benchmark.print_report(report)


if __name__ == "__main__":
    asyncio.run(main())
