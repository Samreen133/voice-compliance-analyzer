# VoiceGuard: AI Monitoring for Regulatory Voice Compliance (UC234)

An enterprise-grade AI voice compliance monitoring, call summarization, and speech intelligence platform designed for banking and financial institutions.

This system addresses:
- AI Monitoring for Regulatory Voice Compliance
- Insurance & Banking Voice Call Summarization
- AI-Powered Call Transcription and Insights

## Features

### Audio Analysis
- Upload and analyze customer service call recordings.
- Process voice interactions for compliance evaluation.
- Support for sample audio demonstrations.

### Compliance Assessment
- Automated compliance checks against predefined policies.
- Risk categorization and scoring.
- Violation detection and reporting.

### Call Summarization
- Generate concise call summaries.
- Highlight key discussion points.
- Extract compliance-related observations.

### Reporting
- Detailed compliance reports.
- Scorecard generation.
- Exportable audit documentation.

### Interactive Dashboard
- Streamlit-based user interface.
- Real-time analysis workflow.
- Easy-to-understand compliance insights.

---

## Project Structure

```text
voice-compliance-analyzer/
│
├── sample_audio/
│   ├── compliant_loan_call.mp3
│   ├── high_risk_sales_call.mp3
│   └── non_compliant_debt_call.mp3
│
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── audio_generator.py
│   ├── compliance_engine.py
│   ├── report_exporter.py
│   └── summarizer.py
│
├── test_pipeline.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Samreen133/voice-compliance-analyzer.git
cd voice-compliance-analyzer
```

### Create Virtual Environment

Windows:

```powershell
python -m venv venv
```

Activate:

```powershell
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Setup

Create a `.env` file using the provided template:

```bash
copy .env.example .env
```

Configure the required environment variables in `.env`.

Example:

```env
API_KEY=your_api_key_here
```

---

## Running the Application

Launch the Streamlit dashboard:

```bash
streamlit run src/app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## Sample Workflow

1. Launch the application.
2. Upload or select a sample audio recording.
3. Run compliance analysis.
4. Review generated summary and compliance score.
5. Export detailed report.

---

## Example Outputs

- Compliance Score
- Risk Assessment
- Violation Summary
- Executive Call Summary
- Downloadable Report

---

## Technology Stack

- Python
- Streamlit
- gTTS
- Pydantic
- python-dotenv
- ReportLab

---

## Use Cases

- Financial Services Compliance
- Call Center Quality Assurance
- Customer Interaction Monitoring
- Internal Audit Reviews
- Training and Coaching Programs

---

## Future Enhancements

- Real-time transcription support
- Multi-language analysis
- Sentiment detection
- Advanced compliance intelligence
- Historical trend analytics
- Batch call processing

---

## Disclaimer

This project is intended for demonstration and educational purposes. Compliance evaluations are generated based on configured assessment logic and should be reviewed by qualified personnel before making business decisions.

---

## Author

**Samreen Kaur**

GitHub: https://github.com/Samreen133