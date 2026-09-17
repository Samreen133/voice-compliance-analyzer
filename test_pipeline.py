"""
Automated Test Verification for Voice Compliance Pipeline
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.compliance_engine import audit_call_offline
from src.summarizer import generate_call_insights
from src.report_exporter import generate_pdf_report
from src.audio_generator import get_scenario

def test_compliant_scenario():
    scenario = get_scenario("compliant_loan")
    report = audit_call_offline(scenario["turns"], call_type=scenario["call_type"], call_title=scenario["title"])
    assert report.overall_score >= 80, f"Expected compliant score >= 80, got {report.overall_score}"
    assert report.audit_verdict == "PASS", f"Expected PASS, got {report.audit_verdict}"
    print(f"[PASS] Scenario 1 (Compliant): Score = {report.overall_score}, Verdict = {report.audit_verdict}")

    insights = generate_call_insights(report)
    assert len(insights.action_items) > 0
    print(f"[PASS] Insights extracted: Topic = {insights.primary_topic}, Action items = {len(insights.action_items)}")

    pdf_path = generate_pdf_report(report)
    assert os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000
    print(f"[PASS] PDF generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

def test_non_compliant_scenario():
    scenario = get_scenario("non_compliant_debt")
    report = audit_call_offline(scenario["turns"], call_type=scenario["call_type"], call_title=scenario["title"])
    assert report.overall_score < 60, f"Expected non-compliant score < 60, got {report.overall_score}"
    assert report.audit_verdict == "CRITICAL_FAIL", f"Expected CRITICAL_FAIL, got {report.audit_verdict}"
    violations = [c for c in report.checklist if c.status == "VIOLATION"]
    assert len(violations) >= 2, f"Expected at least 2 violations, got {len(violations)}"
    print(f"[PASS] Scenario 2 (Non-Compliant): Score = {report.overall_score}, Violations = {len(violations)}")

if __name__ == "__main__":
    print("Running compliance pipeline tests...")
    test_compliant_scenario()
    test_non_compliant_scenario()
    print("All tests passed successfully!")
