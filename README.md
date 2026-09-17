# VoiceGuard AI: AI Monitoring for Regulatory Voice Compliance (UC234)

An enterprise-grade AI voice compliance monitoring, call summarization, and speech intelligence platform designed for banking and financial institutions.

This system addresses:
- **UC234:** AI Monitoring for Regulatory Voice Compliance
- **UC081:** Insurance & Banking Voice Call Summarization
- **UC624:** AI-Powered Call Transcription and Insights

---

## 🌟 Key Features

1. **100% Automated Regulatory Call Auditing:** Audits customer calls against strict financial regulations:
   - **TCPA § 227:** Mandatory recording disclosure in opening.
   - **USA PATRIOT Act / KYC:** Customer identity authentication before sensitive data sharing.
   - **Truth in Lending (TILA / Reg Z):** Transparent APR and fee disclosures.
   - **FDCPA § 1692:** Mini-Miranda disclosure & prohibition of harassment/threats on collection calls.
   - **CFPB UDAAP:** Anti-misselling and prohibition of unauthorized promises.
   - **GLBA & PCI-DSS:** Automatic detection and masking of credit card numbers, CVVs, and SSNs.
2. **Real-Time In-Call Guardian Simulator:** Demonstrates how the AI operates as an in-call copilot, dynamically ticking off compliance items and alerting the agent before violations occur.
3. **Synchronized Dialogue & Audio Playback:** Dual-speaker diarization (`Agent` vs `Customer`) with clickable timestamp flags that correspond to audio moments.
4. **Executive Summaries & CRM Insights (UC081 & UC624):** Generates structured FNOL/call summaries, customer sentiment analysis, and actionable follow-ups with JSON export.
5. **One-Click PDF Compliance Certificate:** Generates an official, immutable PDF audit report ready for regulatory submission.
6. **Zero-API-Key Offline Mode + Live Gemini 2.5 Flash:** Ready to demo immediately with zero cost; optionally connect a free Google AI Studio key for live generative evaluation.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure Python 3.12 or 3.14 virtual environment is activated.

### 2. Run the Dashboard
Open your terminal and execute:
```bash
& "C:\Users\samkaur\farmersproject\venv\Scripts\python.exe" -m streamlit run src/app.py
```

### 3. Open in Browser
Streamlit will launch locally at:
```
http://localhost:8501
```

---

## 📂 Project Structure

```
UC234-voice-compliance/
├── sample_audio/               # Pre-generated synthetic banking calls (.mp3)
│   ├── compliant_loan_call.mp3
│   ├── non_compliant_debt_call.mp3
│   └── high_risk_sales_call.mp3
├── reports/                    # Generated PDF compliance audit certificates
├── src/
│   ├── __init__.py
│   ├── audio_generator.py      # Audio speech generation and scenario manager
│   ├── compliance_engine.py    # Regulatory audit logic (Offline Rulebook + Gemini)
│   ├── summarizer.py           # Call summarization & action item extraction
│   ├── report_exporter.py      # PDF certificate compiler (ReportLab)
│   └── app.py                  # Streamlit web dashboard
├── requirements.txt
├── .env.example
└── README.md
```
