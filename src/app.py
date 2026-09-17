"""
VoiceGuard: Regulatory Voice Compliance & Intelligence Platform (UC234, UC081, UC624)
Main Streamlit Application
"""

import os
import sys
import time
import json
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.compliance_engine import audit_call_offline, audit_call_mock_ai, ComplianceAuditReport, redact_pii
from src.summarizer import generate_call_insights
from src.audio_generator import SCENARIOS, get_scenario, generate_audio_for_scenario, ensure_all_sample_audios
from src.report_exporter import generate_pdf_report

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Custom CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VoiceGuard - Banking Voice Compliance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F2942;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #5A6A85;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-pass {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-fail {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warn {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .chat-bubble-agent {
        background-color: #EFF6FF;
        border-left: 4px solid #2563EB;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .chat-bubble-customer {
        background-color: #F0FDF4;
        border-left: 4px solid #16A34A;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .timestamp-badge {
        color: #64748B;
        font-family: monospace;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=64)
st.sidebar.title("VoiceGuard")
st.sidebar.caption("Voice Compliance Monitoring")

st.sidebar.markdown("---")

engine_choice = st.sidebar.radio(
    "Compliance Audit",
    [
        "Risk Evaluation Engine"
        # "Simulated Enterprise AI (Demo Mode)"
    ]
)

if "Simulated" in engine_choice:
    st.sidebar.success("✅ Demo Mode Active (No downloads required)")

st.sidebar.markdown("---")
st.sidebar.subheader("Call Scenario")
scenario_key = st.sidebar.selectbox(
    "Select Banking Scenario",
    options=["compliant_loan", "non_compliant_debt", "high_risk_sales", "custom_upload"],
    format_func=lambda k: {
        "compliant_loan": "🟢 Scenario 1: Compliant Mortgage Call",
        "non_compliant_debt": "🔴 Scenario 2: Collections Call (FDCPA Violations)",
        "high_risk_sales": "🟡 Scenario 3: Sales Call (Deceptive & PII Leak)",
        "custom_upload": "📁 Upload Custom Audio / Transcript"
    }.get(k, k)
)

# Pre-generate sample audios if not done
if "sample_audio_ready" not in st.session_state:
    with st.sidebar:
        with st.spinner("Initializing sample audio recordings..."):
            ensure_all_sample_audios()
            st.session_state["sample_audio_ready"] = True

# -----------------------------------------------------------------------------
# Load Call Scenario Data
# -----------------------------------------------------------------------------
custom_transcript = ""
audio_path = None

if scenario_key != "custom_upload":
    scenario_data = get_scenario(scenario_key)
    audio_path = os.path.join(PROJECT_ROOT, "sample_audio", scenario_data["audio_filename"])
    turns_data = scenario_data["turns"]
    call_title = scenario_data["title"]
    call_type = scenario_data["call_type"]
else:
    call_title = "Custom Audited Call"
    call_type = "GENERAL_SUPPORT"
    uploaded_file = st.sidebar.file_uploader("Upload Call Audio (.wav, .mp3)", type=["wav", "mp3"])
    if uploaded_file is not None:
        save_path = os.path.join(PROJECT_ROOT, "sample_audio", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        audio_path = save_path

    custom_transcript = st.sidebar.text_area(
        "Or Paste Transcript (with timestamps)",
        value="[00:05] Agent: Hello, thank you for calling. This call is monitored.\n[00:15] Customer: Hi, I want to check my balance.\n[00:20] Agent: May I verify your name and DOB?",
        height=150
    )
    # Parse transcript turns
    import re
    turns_data = []
    for line in custom_transcript.strip().split("\n"):
        m = re.match(r"\[(\d{2}:\d{2})\]\s*([^:]+):\s*(.*)", line.strip())
        if m:
            turns_data.append({"timestamp": m.group(1), "speaker": m.group(2).strip(), "text": m.group(3).strip()})
        elif line.strip():
            turns_data.append({"timestamp": "00:00", "speaker": "Speaker", "text": line.strip()})


# -----------------------------------------------------------------------------
# Run Compliance Audit Engine
# -----------------------------------------------------------------------------
if "Simulated" in engine_choice:
    transcript_text = "\n".join([f"[{t['timestamp']}] {t['speaker']}: {t['text']}" for t in turns_data])
    with st.spinner("Enterprise AI is analyzing the call locally... (this may take a moment)"):
        audit_report = audit_call_mock_ai(transcript_text, call_type=call_type, original_turns=turns_data)
else:
    audit_report = audit_call_offline(turns_data, call_type=call_type, call_title=call_title)

insights = generate_call_insights(audit_report)


# -----------------------------------------------------------------------------
# Main Header & Overview
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🛡️ VoiceGuard: Regulatory Voice Compliance Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated 100% Quality Assurance, Regulatory Violation Detection & Call Intelligence for Financial Services</div>', unsafe_allow_html=True)

# Top KPI Summary Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    verdict_badge = (
        '<span class="badge-pass">PASSED (LOW RISK)</span>' if audit_report.audit_verdict == "PASS"
        else ('<span class="badge-fail">CRITICAL FAIL</span>' if audit_report.audit_verdict == "CRITICAL_FAIL" else '<span class="badge-warn">NEEDS REVIEW</span>')
    )
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.85rem; color:#64748B;">AUDIT VERDICT</div>
        <div style="font-size:1.6rem; font-weight:700; margin:4px 0;">{audit_report.overall_score} / 100</div>
        <div>{verdict_badge}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    total_rules = len(audit_report.checklist)
    passed_rules = sum(1 for c in audit_report.checklist if c.status == "PASSED")
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.85rem; color:#64748B;">REGULATORY CHECKLIST</div>
        <div style="font-size:1.6rem; font-weight:700; margin:4px 0;">{passed_rules} / {total_rules}</div>
        <div style="font-size:0.85rem; color:#64748B;">Mandatory Rules Verified</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    pii_count = len(audit_report.pii_findings)
    pii_color = "#10B981" if pii_count == 0 else "#F59E0B"
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.85rem; color:#64748B;">PII LEAKAGE INTERCEPT</div>
        <div style="font-size:1.6rem; font-weight:700; color:{pii_color}; margin:4px 0;">{pii_count} Intercepted</div>
        <div style="font-size:0.85rem; color:#64748B;">PCI-DSS / GLBA Masked</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.85rem; color:#64748B;">CUSTOMER SENTIMENT</div>
        <div style="font-size:1.4rem; font-weight:700; margin:4px 0;">{audit_report.customer_sentiment}</div>
        <div style="font-size:0.85rem; color:#64748B;">Agent: {audit_report.agent_name}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# Navigation Tabs
# -----------------------------------------------------------------------------
tab_audit, tab_realtime, tab_insights, tab_rulebook = st.tabs([
    "📊 Post-Call Compliance Audit",
    "🎙️ Live Call Compliance Assistant",
    "💡 Call Summarization & CRM Insights",
    "📜 Banking Regulatory Rulebook"
])


# =============================================================================
# TAB 1: Post-Call Compliance Audit
# =============================================================================
with tab_audit:
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.subheader("🎧 Call Audio & Synchronized Dialogue")
        
        # Audio Player
        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path, format="audio/mp3")
            st.caption(f"Audio Track: `{os.path.basename(audio_path)}` | Duration: `{audit_report.call_duration}`")
        else:
            st.info("Audio preview generated synthetic speech placeholder.")

        # Transcript Options
        mask_pii = st.checkbox("🔒 Auto-Mask Sensitive PII (PCI-DSS Mode)", value=True)

        st.markdown("##### Synchronized Dialogue")
        for turn in audit_report.transcript:
            display_text = turn.text if mask_pii else turn.text  # Already redacted in report
            speaker_class = "chat-bubble-agent" if turn.speaker.lower() == "agent" else "chat-bubble-customer"
            speaker_color = "#2563EB" if turn.speaker.lower() == "agent" else "#16A34A"
            
            flag_badges = ""
            for f in turn.flags:
                if "PASS" in f:
                    flag_badges += f' <span class="badge-pass">{f}</span>'
                elif "VIOLATION" in f:
                    flag_badges += f' <span class="badge-fail">{f}</span>'
                elif "PII" in f:
                    flag_badges += f' <span class="badge-warn">{f}</span>'

            st.markdown(f"""
            <div class="{speaker_class}">
                <span class="timestamp-badge">[{turn.timestamp}]</span>
                <strong style="color:{speaker_color}">{turn.speaker}:</strong> {display_text}
                <div style="margin-top:4px;">{flag_badges}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.subheader("📋 Regulatory Checklist Audit")
        
        for item in audit_report.checklist:
            is_pass = item.status == "PASSED"
            badge = '<span class="badge-pass">PASSED</span>' if is_pass else '<span class="badge-fail">VIOLATION</span>'
            time_str = f" • ⏱️ {item.timestamp}" if item.timestamp else ""
            
            with st.expander(f"{'✅' if is_pass else '⚠️'} {item.rule_name} ({item.severity}){time_str}", expanded=(not is_pass)):
                st.markdown(f"**Regulation:** `{item.regulation}`")
                st.markdown(f"**Audit Status:** {badge}", unsafe_allow_html=True)
                st.markdown(f"**Finding:** {item.explanation}")
                if item.evidence_quote and item.evidence_quote != "[Omitted from opening]":
                    st.info(f"**Recorded Evidence:** \"{item.evidence_quote}\"")
                if not is_pass:
                    st.warning(f"**Mandatory Remediation:** {item.remediation}")

        # PII Findings Table
        if audit_report.pii_findings:
            st.markdown("##### 🔐 PII Intercept Log (Auto-Redacted)")
            pii_table_data = [
                {"Type": p.entity_type, "Time": p.timestamp, "Masked Value": p.masked_text, "Action": "Auto-Redacted"}
                for p in audit_report.pii_findings
            ]
            st.table(pii_table_data)

        # PDF Download Section
        st.markdown("---")
        st.subheader("📄 Official Compliance Certificate")
        st.caption("Generate an immutable, timestamped audit certificate for CFPB/regulatory defense.")
        
        if st.button("Generate Official PDF Audit Report", type="primary"):
            with st.spinner("Compiling PDF certificate..."):
                pdf_path = generate_pdf_report(audit_report)
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="⬇️ Download Compliance Audit Certificate (PDF)",
                    data=pdf_bytes,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
                st.success(f"Certificate generated successfully! ({os.path.basename(pdf_path)})")


# =============================================================================
# TAB 2: In-Call Real-Time Copilot Simulation
# =============================================================================
with tab_realtime:
    st.subheader("🎙️ Real-Time In-Call Guardian Simulator")
    st.write(
        "This view simulates the **Agent's Real-Time Screen** during a live phone call. "
        "As the conversation progresses, the AI continuously monitors audio frames, verifies required statutory disclosures, "
        "and triggers **live visual warnings** before the agent commits a regulatory violation."
    )

    col_sim_ctrl, col_sim_view = st.columns([1, 2])

    with col_sim_ctrl:
        st.markdown("##### 🕹️ Simulation Controls")
        st.write(f"Active Scenario: **{call_title}**")
        
        sim_turns = audit_report.transcript
        max_steps = len(sim_turns)
        
        if max_steps <= 1:
            st.warning("⚠️ Timeline requires at least 2 dialogue turns to simulate a live call.")
            step_idx = max_steps if max_steps > 0 else 0
            if max_steps == 1:
                current_turn = sim_turns[0]
                st.metric("Live Call Elapsed Time", current_turn.timestamp)
                st.metric("Current Speaker", current_turn.speaker)
        else:
            step_idx = st.slider("Step Through Call Timeline", min_value=1, max_value=max_steps, value=max_steps)
            current_turn = sim_turns[step_idx - 1]
            st.metric("Live Call Elapsed Time", current_turn.timestamp)
            st.metric("Current Speaker", current_turn.speaker)

    with col_sim_view:
        st.markdown("##### 🖥️ Agent Real-Time Copilot Screen")
        if max_steps > 0:
            # Determine live compliance alerts based on current timestamp
            current_sec = int(current_turn.timestamp.split(":")[0]) * 60 + int(current_turn.timestamp.split(":")[1])
            
            # Alert 1: TCPA Disclosure check
            tcpa_passed = any(c.rule_id == "TCPA_001" and c.status == "PASSED" for c in audit_report.checklist)
            if current_sec >= 15 and not tcpa_passed:
                st.error("🚨 **CRITICAL IN-CALL ALERT [TCPA Violation Risk]:** You have exceeded the 15-second opening threshold without stating the mandatory recording disclosure!")
            elif current_sec < 15 and not tcpa_passed:
                st.warning("⚠️ **TIMED NUDGE:** 15-second statutory deadline approaching. State: *'This call is recorded for quality and compliance.'*")
            else:
                st.success("✅ **MANDATORY DISCLOSURE:** Call recording disclosure acknowledged and logged.")
    
            # Alert 2: KYC Check
            kyc_violated = any(c.rule_id == "KYC_002" and c.status == "VIOLATION" for c in audit_report.checklist)
            if kyc_violated and current_sec >= 20:
                st.error("🚫 **DATA SECURITY INTERCEPT:** You mentioned account balance / confidential terms before customer completed 2FA authentication! Halt financial disclosures immediately.")
            
            # Alert 3: Anti-Harassment / Coercion
            harass_violated = any(c.rule_id == "FDCPA_005B" and c.status == "VIOLATION" for c in audit_report.checklist)
            if harass_violated and current_sec >= 17:
                st.error("⛔ **PROHIBITED CONDUCT ALERT (FDCPA § 1692d):** Threatening language / arrest statements detected. Supervisors have been notified.")
    
            st.markdown("##### 📜 Live Streaming Dialogue")
            for t in sim_turns[:step_idx]:
                spk_color = "#2563EB" if t.speaker.lower() == "agent" else "#16A34A"
                st.markdown(f"**<font color='{spk_color}'>[{t.timestamp}] {t.speaker}:</font>** {t.text}", unsafe_allow_html=True)


# =============================================================================
# TAB 3: Call Summarization & CRM Insights (UC081 & UC624)
# =============================================================================
with tab_insights:
    st.subheader("💡 Executive Call Summary & CRM Insights")
    st.caption("Fulfills UC081 (Voice Call Summarization) and UC624 (AI-Powered Call Insights)")

    ins_col1, ins_col2 = st.columns([1.2, 0.8])

    with ins_col1:
        st.markdown("##### 📝 Executive Summary")
        st.info(insights.executive_summary)

        st.markdown("##### 🎯 Call Intent & Core Topic")
        st.write(f"• **Primary Topic:** {insights.primary_topic}")
        st.write(f"• **Customer Intent:** {insights.intent_category}")
        st.write(f"• **Financial Products Mentioned:** {', '.join(insights.financial_products_mentioned)}")

        st.markdown("##### 🚀 Recommended Next Best Action")
        st.success(f"👉 **{insights.next_best_action}**")

    with ins_col2:
        st.markdown("##### 📈 Risk & Retention Analysis")
        st.metric("Customer Sentiment", insights.customer_sentiment)
        st.metric("Escalation / Churn Risk", insights.churn_or_escalation_risk)

        st.markdown("##### 📋 Extracted Action Items & CRM Tasks")
        action_data = [
            {"Task": a.task, "Owner": a.owner, "Priority": a.priority, "Deadline": a.deadline}
            for a in insights.action_items
        ]
        st.dataframe(action_data, use_container_width=True)

        st.markdown("##### 📤 CRM Webhook Export")
        crm_payload = {
            "call_id": insights.call_id,
            "agent": audit_report.agent_name,
            "customer": audit_report.customer_name,
            "compliance_score": audit_report.overall_score,
            "verdict": audit_report.audit_verdict,
            "summary": insights.executive_summary,
            "action_items": [a.model_dump() for a in insights.action_items]
        }
        st.download_button(
            label="Export CRM Ticket Payload (JSON)",
            data=json.dumps(crm_payload, indent=2),
            file_name=f"crm_ticket_{insights.call_id}.json",
            mime="application/json"
        )


# =============================================================================
# TAB 4: Banking Regulatory Rulebook
# =============================================================================
with tab_rulebook:
    st.subheader("📚 Banking & Financial Regulatory Standards Monitored")
    
    st.markdown("""
    | Regulation | Legal Reference | Purpose & Statutory Mandate | Automated Check Logic |
    | :--- | :--- | :--- | :--- |
    | **Telephone Consumer Protection Act (TCPA)** | 47 U.S.C. § 227 | Prohibits non-consensual voice recording; requires clear notification of recording/monitoring. | Checks that disclosure is verbalized in the first 15 seconds of the call. |
    | **USA PATRIOT Act / CIP** | 31 CFR § 1020.220 | Customer Identification Program (CIP); mandates 2-factor identity verification prior to account data disclosure. | Verifies that authentication occurs before balance or account details are shared. |
    | **Truth in Lending Act (TILA)** | 12 CFR Part 1026 (Reg Z) | Requires accurate and conspicuous disclosure of credit terms, Annual Percentage Rate (APR), and finance charges. | Detects loan/credit terms and verifies explicit APR and fee breakdown. |
    | **Fair Debt Collection Practices Act (FDCPA)** | 15 U.S.C. § 1692 | Prohibits abusive, deceptive, or unfair debt collection practices; mandates 'Mini-Miranda' statement. | Flags threats of arrest, improper employer contact, and verifies Mini-Miranda disclosure. |
    | **UDAAP / Anti-Misselling** | Dodd-Frank Act § 1036 | Prohibits unfair, deceptive, or abusive acts or practices in consumer financial products. | Detects unauthorized guarantees (e.g., 'guaranteed approval', '0% forever'). |
    | **PCI-DSS & GLBA** | 15 U.S.C. § 6801 | Protects consumer non-public personal information (NPI) and cardholder security codes. | Automatically detects and masks Credit Card numbers, CVVs, and SSNs. |
    """)

st.markdown("---")
st.caption("VoiceGuard • Enterprise Voice Compliance & Intelligence • Built for Banks, Lenders & Insurers")
