# Performance Metrics & Timing Plan

This document outlines how we will capture metrics during the JD Power PDF automation run and how to translate those metrics into end-user friendly timing reports. The plan focuses on providing a clear answer to, "How long will it take to download all PDFs?" even when the inventory contains ~2,000 vehicles.

## 1. Where metrics come from

The orchestration layer now emits structured metrics via `jdp_scraper.metrics.RunMetrics`. Key data points:

| Metric | Description | Source |
| --- | --- | --- |
| Step timings | Duration for each major orchestration step (login, export CSV, etc.) | `RunMetrics.track_step(...)` wrappers in `jdp_scraper/orchestration.py` |
| Vehicle timings | Start, end, outcome, and duration for every vehicle processed | `RunMetrics.start_vehicle` / `end_vehicle` invoked in `process_single_vehicle` |
| Run summary | Totals for attempted/succeeded/failed downloads, remaining vehicles, runtime | `RunMetrics.finalize(...)` |

Metrics are persisted to `<RUN_DIR>/metrics.json` (e.g., `downloads/04-18-2024/metrics.json`). This file stores per-step, per-vehicle, and summary information for later analysis.

## 2. How to collect metrics during a run

1. Run the automation as usual via `python main.py`.
2. The orchestration automatically:
   - Wraps each high-level step in a timing context.
   - Starts/stops a vehicle timer for every reference number processed.
   - Saves `metrics.json` and prints a console report at the end of the run.
3. No extra flags are required; metrics are always captured and saved alongside the daily download directory.

## 3. Producing a timing report

### Console output

At the end of each run, the console prints a "Performance Report" section that includes:

- Total runtime for the batch.
- Count of succeeded/failed PDFs.
- Average seconds per successful PDF.
- Estimated wall-clock time to process a 2,000-PDF workload (configurable target list).

Example (values illustrative):

```
=== PERFORMANCE REPORT ===
Run start (UTC): 2024-04-18T16:00:00
Run end   (UTC): 2024-04-18T16:45:00
Total runtime : 0:45:00
Total inventory records : 2500
Attempted this run       : 50
Succeeded                : 49
Failed                   : 1
Remaining                : 200
Average per-PDF duration : 52.34 seconds
Estimated time for 2,000 PDFs: 1 day, 5:02:40
===========================
```

### JSON summary for deeper analysis

`metrics.json` can be ingested into dashboards or spreadsheets. Each successful vehicle entry includes start time, duration, and status which can be aggregated to find:

- Throughput trends over time.
- Step-level bottlenecks (e.g., login latency vs. PDF generation time).
- Error frequency and causes.

## 4. Estimating full-inventory runtime (e.g., 2,000 PDFs)

1. After a representative batch run, note the average per-PDF duration from the performance report (e.g., 52.34 seconds).
2. Multiply the average by the total inventory count:

   ```text
   2,000 PDFs × 52.34 seconds ≈ 104,680 seconds ≈ 29.08 hours
   ```

3. Communicate this duration (rounded to hours/minutes) to stakeholders so they understand the end-to-end timeline once the automation is triggered.
4. If batching is used (e.g., `MAX_DOWNLOADS = 50` per run), multiply the per-batch runtime by the number of batches needed and include cooldown/setup time between runs.

## 5. Recommendations for ongoing monitoring

- **Store historical metrics**: Archive each day's `metrics.json` in long-term storage for trend analysis.
- **Visual dashboards**: Feed metrics into a BI tool to show rolling averages, percentile timings, and error rates.
- **Alerting**: Flag runs where average PDF duration spikes beyond a threshold (e.g., >2× rolling average).
- **Capacity planning**: Use the latest average duration to update "time to complete" estimates whenever inventory sizes change.

With this plan, end users can confidently report how long the automation needs to retrieve the entire PDF inventory and understand where improvements could further reduce runtime.
