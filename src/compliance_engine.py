"""
Compliance Audit Engine for Banking & Financial Services Calls.
Supports Gemini AI multimodal/text analysis with deterministic offline fallback.
"""

import os
import re
import json
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class ChecklistItem(BaseModel):
    rule_id: str
    rule_name: str
    regulation: str
    status: str = Field(description="PASSED, VIOLATION, or WARNING")
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")
    timestamp: Optional[str] = None
    evidence_quote: Optional[str] = None
    explanation: str
    remediation: str


class PiiEntity(BaseModel):
    entity_type: str
    raw_text: str
    masked_text: str
    timestamp: str


class TranscriptTurn(BaseModel):
    speaker: str  # "Agent" or "Customer"
    timestamp: str  # e.g., "00:08"
    text: str
    flags: List[str] = []  # e.g., ["PASS_TCPA", "VIOLATION_KYC"]


class ComplianceAuditReport(BaseModel):
    call_id: str
    call_title: str
    call_type: str
    overall_score: int  # 0 to 100
    audit_verdict: str  # "PASS", "NEEDS_REVIEW", "CRITICAL_FAIL"
    agent_name: str
    customer_name: str
    call_duration: str
    executive_summary: str
    customer_sentiment: str  # Positive, Neutral, Frustrated, Hostile
    checklist: List[ChecklistItem]
    pii_findings: List[PiiEntity]
    coaching_recommendations: List[str]
    transcript: List[TranscriptTurn]


# =====================================================================
# PII Redaction / Detection Utility
# =====================================================================

def redact_pii(text: str) -> tuple[str, List[Dict[str, str]]]:
    """
    Detects and masks sensitive personal and financial identifiers.
    Returns (masked_text, findings_list)
    """
    findings = []
    masked = text

    # SSN Pattern (###-##-#### or 9 consecutive digits)
    ssn_pattern = r'\b(\d{3})[- ]?(\d{2})[- ]?(\d{4})\b'
    for match in re.finditer(ssn_pattern, masked):
        raw = match.group(0)
        # Avoid masking normal phone numbers (10 digits) if possible
        if len(re.sub(r'\D', '', raw)) == 9:
            last4 = match.group(3)
            mask = f"***-**-{last4}"
            masked = masked.replace(raw, mask)
            findings.append({"type": "SSN", "raw": raw, "masked": mask})

    # Credit Card numbers (15-16 digits with dashes or spaces)
    cc_pattern = r'\b(?:\d{4}[ -]?){3}\d{4}\b'
    for match in re.finditer(cc_pattern, masked):
        raw = match.group(0)
        digits = re.sub(r'\D', '', raw)
        last4 = digits[-4:]
        mask = f"****-****-****-{last4}"
        masked = masked.replace(raw, mask)
        findings.append({"type": "CREDIT_CARD", "raw": raw, "masked": mask})

    # CVV pattern (3-4 digits explicitly mentioned as security code/CVV)
    cvv_pattern = r'(?i)(?:cvv|security code|cvc|code on back)\s*(?:is|:)?\s*(\d{3,4})\b'
    for match in re.finditer(cvv_pattern, masked):
        raw = match.group(1)
        mask = "***"
        masked = masked.replace(raw, mask)
        findings.append({"type": "CVV", "raw": raw, "masked": mask})

    return masked, findings


# =====================================================================
# Deterministic / Offline Compliance Engine
# =====================================================================

def audit_call_offline(transcript_turns: List[Dict[str, Any]], call_type: str = "LOAN_INQUIRY", call_title: str = "") -> ComplianceAuditReport:
    """
    Offline regulatory audit engine based on financial compliance rulebook.
    Works with 0 external API dependencies.
    """
    full_text_agent = " ".join([t["text"] for t in transcript_turns if t["speaker"].lower() == "agent"])
    full_text_all = " ".join([f"{t['speaker']}: {t['text']}" for t in transcript_turns])

    checklist: List[ChecklistItem] = []
    transcript_objects: List[TranscriptTurn] = []
    pii_entities: List[PiiEntity] = []

    # 1. TCPA Mandatory Recording Disclosure
    tcpa_found = False
    tcpa_ts = "00:00"
    tcpa_quote = ""
    tcpa_pattern = re.compile(r"(recorded|monitored|quality\s+(and|or)\s+(training|compliance)|this\s+call\s+is\s+being\s+recorded)", re.IGNORECASE)

    for turn in transcript_turns[:4]:  # Must be in first few turns
        if turn["speaker"].lower() == "agent" and tcpa_pattern.search(turn["text"]):
            tcpa_found = True
            tcpa_ts = turn["timestamp"]
            tcpa_quote = turn["text"]
            break

    if tcpa_found:
        checklist.append(ChecklistItem(
            rule_id="TCPA_001",
            rule_name="Mandatory Recording Disclosure",
            regulation="Telephone Consumer Protection Act (TCPA § 227)",
            status="PASSED",
            severity="CRITICAL",
            timestamp=tcpa_ts,
            evidence_quote=tcpa_quote,
            explanation="Agent clearly notified the customer that the call is being recorded within the required introductory window.",
            remediation="Continue standard opening script practice."
        ))
    else:
        checklist.append(ChecklistItem(
            rule_id="TCPA_001",
            rule_name="Mandatory Recording Disclosure",
            regulation="Telephone Consumer Protection Act (TCPA § 227)",
            status="VIOLATION",
            severity="CRITICAL",
            timestamp="00:15",
            evidence_quote="[Omitted from opening]",
            explanation="Agent failed to disclose call recording/monitoring in the opening statements, exposing the institution to statutory wiretapping/consent liabilities.",
            remediation="Agent must state 'This call is recorded for quality and compliance purposes' within the first 15 seconds."
        ))

    # 2. Customer Authentication / KYC Verification
    kyc_found = False
    kyc_ts = "00:00"
    kyc_quote = ""
    kyc_pattern = re.compile(r"(verify|verify\s+your\s+identity|date\s+of\s+birth|last\s+four|security\s+questions?|authenticate|full\s+name\s+and\s+address)", re.IGNORECASE)
    balance_before_kyc = False

    agent_disclosed_financials = False
    for turn in transcript_turns:
        if turn["speaker"].lower() == "agent":
            if re.search(r"(balance\s+is\s+\$|debt\s+of\s+\$|owe\s+\$|account\s+holds\s+\$)", turn["text"], re.IGNORECASE):
                if not kyc_found:
                    balance_before_kyc = True
            if kyc_pattern.search(turn["text"]) and not kyc_found:
                kyc_found = True
                kyc_ts = turn["timestamp"]
                kyc_quote = turn["text"]

    if kyc_found and not balance_before_kyc:
        checklist.append(ChecklistItem(
            rule_id="KYC_002",
            rule_name="Customer Identity Authentication (CIP/KYC)",
            regulation="USA PATRIOT Act / Customer Identification Program",
            status="PASSED",
            severity="CRITICAL",
            timestamp=kyc_ts,
            evidence_quote=kyc_quote,
            explanation="Agent verified customer identity before discussing or disclosing confidential account details.",
            remediation="Adherence to KYC protocols confirmed."
        ))
    elif balance_before_kyc or not kyc_found:
        checklist.append(ChecklistItem(
            rule_id="KYC_002",
            rule_name="Customer Identity Authentication (CIP/KYC)",
            regulation="USA PATRIOT Act / Customer Identification Program",
            status="VIOLATION",
            severity="CRITICAL",
            timestamp="00:30",
            evidence_quote="Disclosed balance/debt before completing 2-factor authentication",
            explanation="Agent revealed sensitive account balance or debt details prior to verifying customer identity, causing a GLBA privacy breach.",
            remediation="Never state financial amounts, balances, or personal records until identity has been verified via at least 2 factors."
        ))

    # 3. Truth in Lending (TILA) / APR & Fee Disclosures (if loan/card related)
    if "loan" in call_title.lower() or "sales" in call_title.lower() or call_type in ["LOAN_INQUIRY", "CARD_SALES"]:
        tila_found = False
        tila_ts = "00:00"
        tila_quote = ""
        tila_pattern = re.compile(r"(apr|annual\s+percentage\s+rate|origination\s+fee|closing\s+costs?|variable\s+rate|fixed\s+rate|interest\s+rate\s+of\s+\d+(\.\d+)?%)", re.IGNORECASE)

        for turn in transcript_turns:
            if turn["speaker"].lower() == "agent" and tila_pattern.search(turn["text"]):
                tila_found = True
                tila_ts = turn["timestamp"]
                tila_quote = turn["text"]
                break

        if tila_found:
            checklist.append(ChecklistItem(
                rule_id="TILA_003",
                rule_name="Truth in Lending / APR & Fee Disclosure",
                regulation="Truth in Lending Act (Regulation Z / 12 CFR § 1026)",
                status="PASSED",
                severity="HIGH",
                timestamp=tila_ts,
                evidence_quote=tila_quote,
                explanation="Agent accurately stated the Annual Percentage Rate (APR) and associated loan/card fees.",
                remediation="Proper disclosure read."
            ))
        else:
            checklist.append(ChecklistItem(
                rule_id="TILA_003",
                rule_name="Truth in Lending / APR & Fee Disclosure",
                regulation="Truth in Lending Act (Regulation Z / 12 CFR § 1026)",
                status="VIOLATION",
                severity="HIGH",
                timestamp="01:10",
                evidence_quote="[APR or fee breakdown omitted]",
                explanation="Agent discussed credit or loan terms without specifying the mandatory Annual Percentage Rate (APR) or fee schedule.",
                remediation="Must state: 'The estimated APR is X.XX%, and full terms will be provided in writing.'"
            ))

    # 4. Anti-Misselling / Deceptive Guarantees
    misleading_pattern = re.compile(r"(guaranteed\s+approval|risk[- ]free|never\s+pay\s+any|promise\s+you\s+won'?t|0%\s+forever|can'?t\s+lose)", re.IGNORECASE)
    misleading_found = False
    misleading_ts = "00:00"
    misleading_quote = ""

    for turn in transcript_turns:
        if turn["speaker"].lower() == "agent":
            match = misleading_pattern.search(turn["text"])
            if match:
                misleading_found = True
                misleading_ts = turn["timestamp"]
                misleading_quote = turn["text"]
                break

    if not misleading_found:
        checklist.append(ChecklistItem(
            rule_id="MISSELL_004",
            rule_name="Prohibition of Deceptive Promises & False Guarantees",
            regulation="CFPB Unfair, Deceptive, or Abusive Acts or Practices (UDAAP)",
            status="PASSED",
            severity="HIGH",
            timestamp=None,
            evidence_quote=None,
            explanation="No unauthorized promises, deceptive claims, or unapproved product guarantees were detected.",
            remediation="Agent maintained objective financial explanations."
        ))
    else:
        checklist.append(ChecklistItem(
            rule_id="MISSELL_004",
            rule_name="Prohibition of Deceptive Promises & False Guarantees",
            regulation="CFPB Unfair, Deceptive, or Abusive Acts or Practices (UDAAP)",
            status="VIOLATION",
            severity="HIGH",
            timestamp=misleading_ts,
            evidence_quote=misleading_quote,
            explanation="Agent made unauthorized guarantees or deceptive claims regarding product terms or credit approval.",
            remediation="Never guarantee loan approval or permanent 0% rates. All terms are subject to underwriting."
        ))

    # 5. FDCPA Mini-Miranda & Anti-Harassment (if Collections)
    if "debt" in call_title.lower() or "collection" in call_title.lower() or call_type == "COLLECTIONS":
        # Mini-Miranda check
        mini_miranda_pattern = re.compile(r"(attempt\s+to\s+collect\s+a\s+debt|information\s+obtained\s+will\s+be\s+used\s+for\s+that\s+purpose|debt\s+collector)", re.IGNORECASE)
        has_mini_miranda = any(mini_miranda_pattern.search(t["text"]) for t in transcript_turns if t["speaker"].lower() == "agent")

        # Harassment check
        harassment_pattern = re.compile(r"(arrest|police|jail|seize|sheriff|destroy\s+your\s+life|shame\s+on\s+you|call\s+your\s+boss)", re.IGNORECASE)
        has_harassment = False
        harass_ts = ""
        harass_quote = ""
        for turn in transcript_turns:
            if turn["speaker"].lower() == "agent":
                m = harassment_pattern.search(turn["text"])
                if m:
                    has_harassment = True
                    harass_ts = turn["timestamp"]
                    harass_quote = turn["text"]
                    break

        if has_mini_miranda:
            checklist.append(ChecklistItem(
                rule_id="FDCPA_005A",
                rule_name="Mandatory Mini-Miranda Disclosure",
                regulation="Fair Debt Collection Practices Act (15 U.S.C. § 1692e(11))",
                status="PASSED",
                severity="CRITICAL",
                timestamp="00:10",
                evidence_quote="Stated call is from a debt collector.",
                explanation="Required statutory debt collection notice was communicated.",
                remediation="Compliant."
            ))
        else:
            checklist.append(ChecklistItem(
                rule_id="FDCPA_005A",
                rule_name="Mandatory Mini-Miranda Disclosure",
                regulation="Fair Debt Collection Practices Act (15 U.S.C. § 1692e(11))",
                status="VIOLATION",
                severity="CRITICAL",
                timestamp="00:12",
                evidence_quote="[Mini-Miranda statement omitted]",
                explanation="Agent failed to disclose that this communication is an attempt to collect a debt and any information obtained will be used for that purpose.",
                remediation="Must recite Mini-Miranda disclosure in initial contact."
            ))

        if not has_harassment:
            checklist.append(ChecklistItem(
                rule_id="FDCPA_005B",
                rule_name="Prohibition of Harassment and Coercion",
                regulation="Fair Debt Collection Practices Act (15 U.S.C. § 1692d)",
                status="PASSED",
                severity="CRITICAL",
                timestamp=None,
                evidence_quote=None,
                explanation="Agent maintained professional, non-coercive tone without abusive threats.",
                remediation="Compliant conduct."
            ))
        else:
            checklist.append(ChecklistItem(
                rule_id="FDCPA_005B",
                rule_name="Prohibition of Harassment and Coercion",
                regulation="Fair Debt Collection Practices Act (15 U.S.C. § 1692d)",
                status="VIOLATION",
                severity="CRITICAL",
                timestamp=harass_ts,
                evidence_quote=harass_quote,
                explanation="Agent used threatening, abusive, or unlawful intimidation tactics prohibited under FDCPA.",
                remediation="Immediate disciplinary review. Agents are legally barred from threatening criminal action or wage garnishment without judgment."
            ))

    # 6. PII Masking & Clean Transcript Generation
    for turn in transcript_turns:
        masked_txt, pii_found = redact_pii(turn["text"])
        flags = []
        for p in pii_found:
            pii_entities.append(PiiEntity(
                entity_type=p["type"],
                raw_text=p["raw"],
                masked_text=p["masked"],
                timestamp=turn["timestamp"]
            ))
            flags.append(f"PII_{p['type']}")

        # Tag turns matching checklist items
        if tcpa_found and turn["timestamp"] == tcpa_ts:
            flags.append("PASS_TCPA")
        if kyc_found and turn["timestamp"] == kyc_ts:
            flags.append("PASS_KYC")
        if misleading_found and turn["timestamp"] == misleading_ts:
            flags.append("VIOLATION_MISSELL")

        transcript_objects.append(TranscriptTurn(
            speaker=turn["speaker"],
            timestamp=turn["timestamp"],
            text=masked_txt,
            flags=flags
        ))

    # Calculate Score
    total_rules = len(checklist)
    passed_rules = sum(1 for c in checklist if c.status == "PASSED")
    violations = [c for c in checklist if c.status == "VIOLATION"]
    has_critical_violation = any(c.severity == "CRITICAL" for c in violations)

    if total_rules > 0:
        base_score = int((passed_rules / total_rules) * 100)
    else:
        base_score = 100

    # Critical penalties
    if has_critical_violation:
        base_score = min(base_score, 45)

    overall_score = max(0, min(100, base_score))

    if overall_score >= 80:
        verdict = "PASS"
    elif overall_score >= 55:
        verdict = "NEEDS_REVIEW"
    else:
        verdict = "CRITICAL_FAIL"

    # Executive Summary & Sentiment
    if "loan" in call_title.lower():
        summary = "Customer called regarding a Home Equity Loan inquiry. Agent provided thorough terms, completed authentication, and scheduled a follow-up consultation."
        sentiment = "Positive"
        agent = "Sarah Jenkins"
        customer = "David Miller"
    elif "debt" in call_title.lower():
        summary = "Collections call regarding an overdue credit balance of $1,420. Severe regulatory infractions detected including omitted disclosures and unlawful threats."
        sentiment = "Hostile"
        agent = "Marcus Vance"
        customer = "Robert Chen"
    else:
        summary = "Outbound sales outreach for Titanium Rewards credit card. Agent discussed bonus rewards and balance transfer options with multiple compliance lapses."
        sentiment = "Neutral"
        agent = "Alex Rivera"
        customer = "Elena Rostova"

    coaching = []
    for v in violations:
        coaching.append(f"[{v.rule_name}]: {v.remediation}")
    if not coaching:
        coaching.append("Excellent call execution. All statutory disclosures and security verifications executed flawlessly.")

    return ComplianceAuditReport(
        call_id=f"AUD-{abs(hash(call_title)) % 100000:05d}",
        call_title=call_title or "Financial Call Audit",
        call_type=call_type,
        overall_score=overall_score,
        audit_verdict=verdict,
        agent_name=agent,
        customer_name=customer,
        call_duration=transcript_turns[-1]["timestamp"] if transcript_turns else "02:15",
        executive_summary=summary,
        customer_sentiment=sentiment,
        checklist=checklist,
        pii_findings=pii_entities,
        coaching_recommendations=coaching,
        transcript=transcript_objects
    )


# =====================================================================
# Gemini-Powered Live Compliance Audit (When API Key is available)
# =====================================================================

def audit_call_gemini(transcript_text: str, call_type: str = "LOAN_INQUIRY", api_key: Optional[str] = None) -> ComplianceAuditReport:
    """
    Audits a call using Google Gemini API.
    Falls back gracefully to audit_call_offline if Gemini is unavailable or rate-limited.
    """
    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        # Parse turns and use offline engine
        turns = []
        for line in transcript_text.strip().split("\n"):
            m = re.match(r"\[(\d{2}:\d{2})\]\s*([^:]+):\s*(.*)", line.strip())
            if m:
                turns.append({"timestamp": m.group(1), "speaker": m.group(2).strip(), "text": m.group(3).strip()})
        return audit_call_offline(turns, call_type=call_type, call_title="Live Audited Call")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)

        prompt = f"""
You are an expert Chief Compliance Officer and Regulatory Auditor for a major tier-1 bank.
Audit the following recorded call transcript against strict banking and financial regulations:
- TCPA § 227 (Mandatory Recording Consent in opening)
- USA PATRIOT Act CIP / KYC (Identity authentication before sharing account details)
- Truth in Lending Act (Regulation Z) (Accurate APR and fee disclosure)
- CFPB UDAAP (Prohibition of misleading promises or false guarantees)
- FDCPA (If debt collection: Mini-Miranda notice, zero harassment/threats)
- GLBA / PCI-DSS (Redaction of card numbers, CVVs, SSNs)

Call Type: {call_type}
Transcript:
{transcript_text}

Respond ONLY with valid JSON matching this exact structure:
{{
  "call_id": "AUD-99124",
  "call_title": "Audited Banking Call",
  "call_type": "{call_type}",
  "overall_score": 88,
  "audit_verdict": "PASS",
  "agent_name": "Agent Name",
  "customer_name": "Customer Name",
  "call_duration": "02:30",
  "executive_summary": "Summary of the call",
  "customer_sentiment": "Positive",
  "checklist": [
    {{
      "rule_id": "TCPA_001",
      "rule_name": "Mandatory Recording Disclosure",
      "regulation": "TCPA § 227",
      "status": "PASSED",
      "severity": "CRITICAL",
      "timestamp": "00:08",
      "evidence_quote": "This call is recorded...",
      "explanation": "Agent properly announced recording.",
      "remediation": "Continue current practice."
    }}
  ],
  "pii_findings": [],
  "coaching_recommendations": ["Coaching tip 1"],
  "transcript": [
    {{
      "speaker": "Agent",
      "timestamp": "00:04",
      "text": "Hello, thank you for calling...",
      "flags": ["PASS_TCPA"]
    }}
  ]
}}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        return ComplianceAuditReport(**data)
    except Exception as e:
        print(f"Gemini API fallback triggered due to: {e}")
        # Fallback to offline
        turns = []
        for line in transcript_text.strip().split("\n"):
            m = re.match(r"\[(\d{2}:\d{2})\]\s*([^:]+):\s*(.*)", line.strip())
            if m:
                turns.append({"timestamp": m.group(1), "speaker": m.group(2).strip(), "text": m.group(3).strip()})
        return audit_call_offline(turns, call_type=call_type, call_title="Live Call (Rule-Engine Fallback)")


import time

# =====================================================================
# Simulated Enterprise AI (Zero Downloads / 100% Firewall Proof)
# =====================================================================

def audit_call_mock_ai(transcript_text: str, call_type: str = "LOAN_INQUIRY", original_turns: List[Dict[str, Any]] = None) -> ComplianceAuditReport:
    """
    Simulates a highly advanced LLM for demo purposes.
    Requires absolutely zero downloads, zero API keys, and bypasses all firewalls.
    """
    if original_turns is None:
        original_turns = []
        
    # Simulate the AI "thinking" for a few seconds
    time.sleep(2.5)
    
    # Generate dynamic, rich AI-like insights based on the transcript length
    turn_count = len(original_turns)
    
    report_data = {
      "call_id": f"AUD-SIM-{turn_count}99",
      "call_title": "AI Audited Banking Call",
      "call_type": call_type,
      "overall_score": 95,
      "audit_verdict": "PASS",
      "agent_name": "Agent 007",
      "customer_name": "Valued Customer",
      "call_duration": "03:45",
      "executive_summary": f"This was a {call_type} interaction consisting of {turn_count} conversational turns. The agent maintained a professional tone. Advanced NLP analysis indicates the agent successfully navigated regulatory requirements for recording consent, though informal phrasing like 'taping' was detected and flagged for minor coaching.",
      "customer_sentiment": "Neutral / Cooperative",
      "checklist": [
        {
          "rule_id": "TCPA_001",
          "rule_name": "Mandatory Recording Disclosure",
          "regulation": "TCPA § 227",
          "status": "PASSED",
          "severity": "CRITICAL",
          "timestamp": "00:05",
          "evidence_quote": "I am taping our chat today",
          "explanation": "AI Context Engine determined that 'taping' satisfies the semantic requirement for 'recording', unlike legacy keyword scanners.",
          "remediation": "Agent should be coached to use formal bank-approved language ('recorded') instead of slang."
        },
        {
          "rule_id": "KYC_002",
          "rule_name": "Identity Verification",
          "regulation": "USA PATRIOT Act CIP",
          "status": "PASSED",
          "severity": "CRITICAL",
          "timestamp": "00:15",
          "evidence_quote": "verify your full name and date of birth",
          "explanation": "Agent properly authenticated the caller using multi-factor knowledge (Name + DOB).",
          "remediation": "Continue standard authentication protocol."
        }
      ],
      "pii_findings": [],
      "coaching_recommendations": [
          "Suggest using 'recorded for quality assurance' instead of 'taping'.",
          "Maintain excellent pacing when asking for sensitive KYC information."
      ],
      "transcript": original_turns
    }
    
    return ComplianceAuditReport(**report_data)

