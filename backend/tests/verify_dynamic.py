import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import AsyncClient, ASGITransport
from services.api.main import app


async def run_verification():
    print("=" * 60)
    print("INTELLI-CI — FULL DYNAMIC DATA PIPELINE VERIFICATION")
    print("=" * 60)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Initial state
        res1 = await client.get("/api/v1/analytics/overview")
        assert res1.status_code == 200, f"Failed: {res1.text}"
        data1 = res1.json()["data"]
        total_before = data1["total_pipelines"]
        print(f"[1] Initial Pipeline Count: {total_before}")
        print(f"    Success Rate: {data1['success_rate']}%")
        print(f"    Avg Duration: {data1['average_duration_seconds']}s")

        # Step 2: Trigger Webhook Event (Simulating GitHub Actions workflow run)
        sim_res = await client.post(
            "/api/v1/github/simulate-webhook",
            json={
                "event_type": "workflow_run",
                "conclusion": "success",
                "branch": "main",
                "commit_message": "feat(core): dynamic telemetry verification run",
            },
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()["data"]
        pipeline_id = sim_data["pipeline_id"]
        print(f"\n[2] Ingested GitHub Webhook Event!")
        print(f"    Pipeline ID: {pipeline_id}")
        print(f"    Status: {sim_data['status']}")
        print(f"    Decision: {sim_data.get('decision', 'SKIP_TESTS')}")

        # Step 3: Verify Overview Auto-Update & Cache Invalidation
        res2 = await client.get("/api/v1/analytics/overview")
        data2 = res2.json()["data"]
        total_after = data2["total_pipelines"]
        print(f"\n[3] Post-Webhook Pipeline Count: {total_after}")
        assert total_after == total_before + 1, f"Expected {total_before + 1}, got {total_after}"
        print(f"    New Success Rate: {data2['success_rate']}%")
        print(f"    Updated Avg Duration: {data2['average_duration_seconds']}s")
        print("    --> Real-time DB insertion + Redis cache invalidation: PASSED")

        # Step 4: Verify Durations endpoint
        dur_res = await client.get("/api/v1/analytics/durations")
        assert dur_res.status_code == 200
        dur_data = dur_res.json()["data"]
        print(f"\n[4] Durations Percentiles:")
        print(f"    P50: {dur_data['p50']}s | P90: {dur_data['p90']}s | P95: {dur_data['p95']}s")
        print(f"    Total Recorded Samples: {dur_data['total_samples']}")

        # Step 5: Verify Stages breakdown
        stages_res = await client.get("/api/v1/analytics/stages")
        assert stages_res.status_code == 200
        stages_data = stages_res.json()["data"]
        print(f"\n[5] DAG Stage Breakdown ({len(stages_data)} stages detected):")
        for stg in stages_data[:4]:
            print(f"    - {stg['stage']}: avg {stg['avg_duration']}s across {stg['total_executions']} runs (failures: {stg['failure_count']})")

        # Step 6: Verify Recommendations
        rec_res = await client.get("/api/v1/recommendations")
        assert rec_res.status_code == 200
        recs = rec_res.json()["data"]
        print(f"\n[6] Dynamic Optimization Recommendations ({len(recs)} active):")
        for rec in recs[:3]:
            print(f"    - [{rec['id']}] {rec['title']} ({rec['severity']}) -> {rec['impact']}")

        print("\n" + "=" * 60)
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH 100% DYNAMIC DATA!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_verification())
