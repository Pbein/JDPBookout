"""Utilities for capturing runtime metrics and producing performance reports.

The orchestration layer records each major step in the automation as well as
per-vehicle download timings. Metrics are persisted alongside the run output
so that we can provide accurate reporting on throughput for large inventories
of PDFs (e.g., full 2,000 vehicle downloads).
"""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from jdp_scraper import config


@dataclass
class StepMetric:
    """Represents timing information for a discrete orchestration step."""

    name: str
    started_at: datetime
    duration_seconds: float


@dataclass
class VehicleMetric:
    """Stores timing and status data for a single vehicle download."""

    reference_number: str
    started_at: datetime
    duration_seconds: float
    status: str
    error: Optional[str] = None


@dataclass
class RunSummary:
    """Aggregate view of the entire automation run."""

    total_inventory: int
    attempted: int
    succeeded: int
    failed: int
    remaining: int
    started_at: datetime
    completed_at: datetime

    @property
    def runtime(self) -> timedelta:
        return self.completed_at - self.started_at

    @property
    def runtime_seconds(self) -> float:
        return self.runtime.total_seconds()


class RunMetrics:
    """Capture high-level and per-vehicle timing metrics for a run."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.started_at: datetime = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.steps: List[StepMetric] = []
        self.vehicles: List[VehicleMetric] = []
        self._vehicle_starts: Dict[str, float] = {}
        self._vehicle_start_times: Dict[str, datetime] = {}
        self.summary: Optional[RunSummary] = None
        self.metadata: Dict[str, str] = {}
        self.output_dir = Path(output_dir or config.RUN_DIR)

    def add_metadata(self, **kwargs) -> None:
        """Attach additional metadata about the run (e.g., settings)."""

        for key, value in kwargs.items():
            if value is None:
                continue
            self.metadata[key] = str(value)

    @contextmanager
    def track_step(self, name: str) -> Iterable[None]:
        """Context manager to record duration of a named orchestration step."""

        start_time = datetime.utcnow()
        start_perf = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_perf
            self.steps.append(
                StepMetric(name=name, started_at=start_time, duration_seconds=duration)
            )

    def start_vehicle(self, reference_number: str) -> None:
        """Mark the beginning of a vehicle download."""

        self._vehicle_start_times[reference_number] = datetime.utcnow()
        self._vehicle_starts[reference_number] = time.perf_counter()

    def end_vehicle(
        self, reference_number: str, status: str, error: Optional[str] = None
    ) -> None:
        """Mark the completion of a vehicle download."""

        start_perf = self._vehicle_starts.pop(reference_number, None)
        start_time = self._vehicle_start_times.pop(reference_number, datetime.utcnow())
        duration = 0.0 if start_perf is None else time.perf_counter() - start_perf
        self.vehicles.append(
            VehicleMetric(
                reference_number=reference_number,
                started_at=start_time,
                duration_seconds=duration,
                status=status,
                error=error,
            )
        )

    def finalize(
        self,
        *,
        total_inventory: int,
        attempted: int,
        succeeded: int,
        failed: int,
        remaining: int,
    ) -> None:
        """Record summary data and mark the run as completed."""

        self.completed_at = datetime.utcnow()
        self.summary = RunSummary(
            total_inventory=total_inventory,
            attempted=attempted,
            succeeded=succeeded,
            failed=failed,
            remaining=remaining,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

    # Reporting helpers -------------------------------------------------
    def average_vehicle_duration(self, *, statuses: Iterable[str]) -> Optional[float]:
        """Return the average duration (in seconds) for vehicles matching statuses."""

        durations = [
            metric.duration_seconds
            for metric in self.vehicles
            if metric.status in statuses and metric.duration_seconds > 0
        ]
        if not durations:
            return None
        return sum(durations) / len(durations)

    def estimate_total_time(self, target_total: int) -> Optional[timedelta]:
        """Estimate wall-clock time required to process ``target_total`` vehicles."""

        avg_seconds = self.average_vehicle_duration(statuses=("success",))
        if avg_seconds is None:
            return None
        total_seconds = avg_seconds * target_total
        return timedelta(seconds=total_seconds)

    def to_dict(self) -> Dict[str, object]:
        """Serialize metrics to a JSON-friendly dictionary."""

        vehicles = [
            {
                "reference_number": metric.reference_number,
                "started_at": metric.started_at.isoformat(),
                "duration_seconds": metric.duration_seconds,
                "status": metric.status,
                "error": metric.error,
            }
            for metric in self.vehicles
        ]
        steps = [
            {
                "name": step.name,
                "started_at": step.started_at.isoformat(),
                "duration_seconds": step.duration_seconds,
            }
            for step in self.steps
        ]
        summary_dict = None
        if self.summary is not None:
            summary_dict = {
                "total_inventory": self.summary.total_inventory,
                "attempted": self.summary.attempted,
                "succeeded": self.summary.succeeded,
                "failed": self.summary.failed,
                "remaining": self.summary.remaining,
                "started_at": self.summary.started_at.isoformat(),
                "completed_at": self.summary.completed_at.isoformat(),
                "runtime_seconds": self.summary.runtime_seconds,
            }

        return {
            "metadata": self.metadata,
            "steps": steps,
            "vehicles": vehicles,
            "summary": summary_dict,
        }

    def save(self, filename: str = "metrics.json") -> Path:
        """Persist metrics to ``filename`` within the run directory."""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=2)
        return output_path

    def print_console_report(self, *, additional_targets: Optional[List[int]] = None) -> None:
        """Display a concise summary of the run and throughput estimates."""

        if self.summary is None:
            print("[METRICS] Summary unavailable; run did not complete cleanly.")
            return

        runtime_str = str(self.summary.runtime).split(".")[0]
        avg_success = self.average_vehicle_duration(statuses=("success",))
        print("\n=== PERFORMANCE REPORT ===")
        print(f"Run start (UTC): {self.summary.started_at.isoformat()}" )
        print(f"Run end   (UTC): {self.summary.completed_at.isoformat()}" )
        print(f"Total runtime : {runtime_str}")
        print(f"Total inventory records : {self.summary.total_inventory}")
        print(f"Attempted this run       : {self.summary.attempted}")
        print(f"Succeeded                : {self.summary.succeeded}")
        print(f"Failed                   : {self.summary.failed}")
        print(f"Remaining                : {self.summary.remaining}")
        if avg_success is None:
            print("Average per-PDF duration : N/A (no successful downloads recorded)")
        else:
            print(
                f"Average per-PDF duration : {avg_success:.2f} seconds"
            )

        if additional_targets:
            for target in additional_targets:
                estimate = self.estimate_total_time(target)
                if estimate is None:
                    continue
                estimate_str = str(estimate).split(".")[0]
                print(
                    f"Estimated time for {target:,} PDFs: {estimate_str}"
                )
        print("===========================\n")

