"""Seed demo data by calling the AiLine API endpoints.

Standalone script that populates the demo teacher profile with sample data
(materials, plans, progress, tutors) and verifies the demo scenarios are
loaded from data/demo/ JSON files.

Usage:
    python runtime/scripts/seed_demo.py [BASE_URL]

    BASE_URL defaults to http://localhost:8000 if not provided.

Examples:
    # Against local dev server
    python runtime/scripts/seed_demo.py

    # Against Docker Compose
    python runtime/scripts/seed_demo.py http://localhost:8000

    # Against a deployed instance
    python runtime/scripts/seed_demo.py https://api.ailine.example.com
"""

from __future__ import annotations

import sys
import time

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
API_PREFIX = "/api/v1/demo"
TEACHER_ID = "demo-teacher-ms-johnson"
TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _url(path: str) -> str:
    return f"{BASE_URL}{API_PREFIX}{path}"


def _print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _print_result(label: str, status: int, detail: str) -> None:
    icon = "[OK]" if 200 <= status < 300 else "[FAIL]"
    print(f"  {icon} {label}: HTTP {status} -- {detail}")


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def check_health(client: httpx.Client) -> bool:
    """Verify the API is reachable before proceeding."""
    _print_header("Step 0: Health Check")
    try:
        resp = client.get(f"{BASE_URL}/health", timeout=10.0)
        _print_result("Health", resp.status_code, resp.text[:200])
        return resp.status_code == 200
    except httpx.ConnectError:
        print(f"  [FAIL] Cannot connect to {BASE_URL}")
        print("         Is the API server running?")
        return False


def seed_demo_data(client: httpx.Client) -> bool:
    """POST /demo/seed to populate stores with sample data."""
    _print_header("Step 1: Seed Demo Data")
    resp = client.post(
        _url("/seed"),
        headers={"X-Teacher-ID": TEACHER_ID},
        timeout=TIMEOUT,
    )
    if resp.status_code == 200:
        body = resp.json()
        created = body.get("created", {})
        detail = ", ".join(f"{k}={v}" for k, v in created.items())
        _print_result("Seed", resp.status_code, detail)
        return True
    else:
        _print_result("Seed", resp.status_code, resp.text[:300])
        return False


def verify_profiles(client: httpx.Client) -> bool:
    """GET /demo/profiles to verify all 6 demo personas are available."""
    _print_header("Step 2: Verify Demo Profiles")
    resp = client.get(_url("/profiles"), timeout=TIMEOUT)
    if resp.status_code == 200:
        body = resp.json()
        profiles = body.get("profiles", [])
        _print_result("Profiles", resp.status_code, f"{len(profiles)} profiles loaded")
        for p in profiles:
            role = p.get("role", "?")
            name = p.get("name", "?")
            acc = p.get("accessibility_label", "")
            suffix = f" ({acc})" if acc else ""
            print(f"    - [{role}] {name}{suffix}")
        return len(profiles) == 6
    else:
        _print_result("Profiles", resp.status_code, resp.text[:300])
        return False


def verify_scenarios(client: httpx.Client) -> bool:
    """GET /demo/scenarios to verify JSON scenario files are loaded."""
    _print_header("Step 3: Verify Demo Scenarios")
    resp = client.get(_url("/scenarios"), timeout=TIMEOUT)
    if resp.status_code == 200:
        scenarios = resp.json()
        _print_result("Scenarios", resp.status_code, f"{len(scenarios)} scenarios loaded")
        for s in scenarios:
            sid = s.get("id", "?")
            title = s.get("title", "?")
            tags = ", ".join(s.get("demo_tags", [])[:4])
            print(f"    - [{sid}] {title}")
            if tags:
                print(f"      Tags: {tags}")
        return len(scenarios) >= 2
    else:
        _print_result("Scenarios", resp.status_code, resp.text[:300])
        return False


def test_scenario_run(client: httpx.Client, scenario_id: str) -> bool:
    """POST /demo/scenarios/{id}/run to verify cached plan is served."""
    _print_header(f"Step 4: Test Scenario Run ({scenario_id})")
    resp = client.post(_url(f"/scenarios/{scenario_id}/run"), timeout=TIMEOUT)
    if resp.status_code == 200:
        body = resp.json()
        plan = body.get("plan", {})
        title = plan.get("title", "(no title)")
        score = body.get("score", "?")
        demo = body.get("demo_mode", False)
        _print_result(
            "Run",
            resp.status_code,
            f"plan='{title}', score={score}, demo_mode={demo}",
        )
        return demo is True
    else:
        _print_result("Run", resp.status_code, resp.text[:300])
        return False


def test_scenario_detail(client: httpx.Client, scenario_id: str) -> bool:
    """GET /demo/scenarios/{id} to verify full scenario data including cached_events."""
    _print_header(f"Step 5: Test Scenario Detail ({scenario_id})")
    resp = client.get(_url(f"/scenarios/{scenario_id}"), timeout=TIMEOUT)
    if resp.status_code == 200:
        body = resp.json()
        events = body.get("cached_events", [])
        skills = body.get("expected_skills", [])
        _print_result(
            "Detail",
            resp.status_code,
            f"{len(events)} cached events, {len(skills)} skills",
        )
        if events:
            first = events[0].get("type", "?")
            last = events[-1].get("type", "?")
            print(f"    Events: {first} ... {last} ({len(events)} total)")
        return len(events) > 0
    else:
        _print_result("Detail", resp.status_code, resp.text[:300])
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"AiLine Demo Seed Script")
    print(f"Target: {BASE_URL}")
    print(f"Teacher ID: {TEACHER_ID}")

    start = time.monotonic()
    results: list[bool] = []

    with httpx.Client() as client:
        # Step 0: Health check
        if not check_health(client):
            print("\nAborted: API not reachable.")
            return 1

        # Step 1: Seed data
        results.append(seed_demo_data(client))

        # Step 2: Verify profiles
        results.append(verify_profiles(client))

        # Step 3: Verify scenarios
        results.append(verify_scenarios(client))

        # Step 4: Test running the photosynthesis scenario
        results.append(test_scenario_run(client, "photosynthesis-5th-grade"))

        # Step 5: Test scenario detail with events
        results.append(test_scenario_detail(client, "photosynthesis-5th-grade"))

        # Step 4b: Test running the fractions scenario
        results.append(test_scenario_run(client, "fractions-math-adhd"))

    elapsed = time.monotonic() - start

    # Summary
    _print_header("Summary")
    passed = sum(results)
    total = len(results)
    status = "ALL PASSED" if all(results) else f"{passed}/{total} PASSED"
    print(f"  {status} in {elapsed:.1f}s")

    if all(results):
        print("\n  Demo system is ready for presentation!")
        print(f"  Open {BASE_URL} and log in with any demo profile.")
    else:
        print("\n  Some checks failed. Review output above.")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
