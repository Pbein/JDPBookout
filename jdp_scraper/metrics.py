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

    def print_console_report(self, *, additional_targets: Optional[List[int]] = None, checkpoint_data: Optional[dict] = None) -> None:
        """Display a comprehensive summary of the run with performance metrics and checkpoint data."""

        if self.summary is None:
            print("[METRICS] Summary unavailable; run did not complete cleanly.")
            return

        runtime_str = str(self.summary.runtime).split(".")[0]
        avg_success = self.average_vehicle_duration(statuses=("success",))
        
        # Calculate additional statistics
        failed_vehicles = [v for v in self.vehicles if v.status == "failed"]
        success_vehicles = [v for v in self.vehicles if v.status == "success"]
        
        # Get min/max/median for successful downloads
        if success_vehicles:
            success_durations = sorted([v.duration_seconds for v in success_vehicles])
            min_duration = success_durations[0]
            max_duration = success_durations[-1]
            median_duration = success_durations[len(success_durations) // 2]
        else:
            min_duration = max_duration = median_duration = 0
        
        # Count error types
        error_counts = {}
        for vehicle in failed_vehicles:
            error_type = vehicle.error or "unknown"
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        print("\n" + "="*70)
        print(" "*20 + "📊 FINAL RUN REPORT")
        print("="*70)
        
        # Section 1: Run Overview
        print("\n🕐 RUN OVERVIEW")
        print("-" * 70)
        print(f"  Started at (UTC)    : {self.summary.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Completed at (UTC)  : {self.summary.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Total runtime       : {runtime_str}")
        print(f"  Total inventory     : {self.summary.total_inventory:,} vehicles")
        
        # Section 2: Processing Results
        print(f"\n📈 PROCESSING RESULTS")
        print("-" * 70)
        print(f"  Attempted this run  : {self.summary.attempted}")
        print(f"  ✓ Succeeded         : {self.summary.succeeded} ({self.summary.succeeded/self.summary.attempted*100:.1f}%)")
        print(f"  ✗ Failed            : {self.summary.failed} ({self.summary.failed/self.summary.attempted*100:.1f}%)")
        print(f"  Remaining           : {self.summary.remaining:,}")
        
        # Section 3: Performance Metrics
        print(f"\n⚡ PERFORMANCE METRICS")
        print("-" * 70)
        if avg_success is None:
            print("  Average per-vehicle : N/A (no successful downloads)")
        else:
            print(f"  Average per-vehicle : {avg_success:.2f} seconds")
            print(f"  Fastest vehicle     : {min_duration:.2f} seconds")
            print(f"  Slowest vehicle     : {max_duration:.2f} seconds")
            print(f"  Median vehicle      : {median_duration:.2f} seconds")
            
            # Calculate throughput
            vehicles_per_hour = 3600 / avg_success
            print(f"  Throughput          : {vehicles_per_hour:.1f} vehicles/hour")
        
        # Section 4: Checkpoint/Recovery Data
        if checkpoint_data:
            print(f"\n🔄 RECOVERY & CHECKPOINT DATA")
            print("-" * 70)
            print(f"  Total processed     : {checkpoint_data.get('total_processed', 0)}")
            print(f"  Checkpoint saves    : {checkpoint_data.get('total_processed', 0)} (after each vehicle)")
            print(f"  Last successful     : {checkpoint_data.get('last_successful_ref', 'N/A')}")
            print(f"  Consecutive failures: {checkpoint_data.get('consecutive_failures', 0)}")
            print(f"  Browser restarts    : {checkpoint_data.get('browser_restarts', 0)}")
            success_rate = checkpoint_data.get('success_rate', 0)
            print(f"  Overall success rate: {success_rate:.1f}%")
        
        # Section 5: Error Breakdown
        if error_counts:
            print(f"\n❌ ERROR BREAKDOWN")
            print("-" * 70)
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error_type:20s}: {count} occurrences")
        
        # Section 6: Projections
        if avg_success and additional_targets:
            print(f"\n🎯 PROJECTIONS FOR FULL INVENTORY")
            print("-" * 70)
            for target in additional_targets:
                estimate = self.estimate_total_time(target)
                if estimate is None:
                    continue
                estimate_str = str(estimate).split(".")[0]
                hours = estimate.total_seconds() / 3600
                print(f"  {target:,} vehicles: {estimate_str} (~{hours:.1f} hours)")
        
        # Section 7: Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 70)
        if self.summary.failed > 0:
            fail_rate = self.summary.failed / self.summary.attempted * 100
            if fail_rate > 20:
                print("  ⚠️  High failure rate detected (>20%)")
                print("     Consider investigating network/server issues")
            elif fail_rate > 10:
                print("  ⚠️  Moderate failure rate (>10%)")
                print("     Monitor for patterns in error types")
            else:
                print("  ✓ Acceptable failure rate (<10%)")
        else:
            print("  ✓ Perfect run - no failures!")
        
        if self.summary.remaining > 0:
            print(f"  → Run again to process remaining {self.summary.remaining:,} vehicles")
            print(f"     Program will resume from checkpoint automatically")
        else:
            print("  ✓ All vehicles processed!")
        
        print("\n" + "="*70 + "\n")
    
    def get_detailed_stats(self) -> dict:
        """Get detailed statistics for programmatic access."""
        if not self.vehicles:
            return {}
        
        success_vehicles = [v for v in self.vehicles if v.status == "success"]
        failed_vehicles = [v for v in self.vehicles if v.status == "failed"]
        
        stats = {
            "total_vehicles": len(self.vehicles),
            "successful": len(success_vehicles),
            "failed": len(failed_vehicles),
        }
        
        if success_vehicles:
            durations = [v.duration_seconds for v in success_vehicles]
            stats["avg_duration"] = sum(durations) / len(durations)
            stats["min_duration"] = min(durations)
            stats["max_duration"] = max(durations)
            stats["median_duration"] = sorted(durations)[len(durations) // 2]
        
        return stats

