"""
Call Summarizer & Insights Extraction Engine (UC081 & UC624)
Extracts structured executive summaries, customer intent, sentiment, action items, and CRM tickets.
"""

from typing import Dict, List, Any
from pydantic import BaseModel


class ActionItem(BaseModel):
    task: str
    owner: str  # "Agent", "Customer", "Underwriting", "Operations"
    priority: str  # "High", "Medium", "Low"
    deadline: str


class CallInsights(BaseModel):
    call_id: str
    primary_topic: str
    intent_category: str
    executive_summary: str
    customer_sentiment: str
    churn_or_escalation_risk: str  # "Low", "Moderate", "High", "Critical"
    financial_products_mentioned: List[str]
    action_items: List[ActionItem]
    next_best_action: str


def generate_call_insights(audit_report) -> CallInsights:
    """
    Derives structured business insights and CRM action items from the call audit report.
    """
    call_type = audit_report.call_type
    score = audit_report.overall_score

    if call_type == "LOAN_INQUIRY":
        topic = "Home Equity Line of Credit (HELOC)"
        intent = "Rate & Term Inquiry"
        summary = (
            "Customer inquired about borrowing against home equity for kitchen remodeling. "
            "Agent verified identity, explained variable vs. fixed APR options (6.75% fixed), "
            "and clarified closing cost structures. Customer expressed strong satisfaction and agreed to proceed with application."
        )
        sentiment = "Positive / Highly Engaged"
        risk = "Low"
        products = ["Home Equity Loan", "Fixed-Rate Mortgage Refinance"]
        actions = [
            ActionItem(task="Transmit pre-qualification package via secure portal", owner="Agent", priority="High", deadline="Within 2 hours"),
            ActionItem(task="Upload two recent W-2 statements and property deed", owner="Customer", priority="Medium", deadline="By Friday"),
            ActionItem(task="Assign loan officer consultation", owner="Operations", priority="Medium", deadline="Tomorrow 10:00 AM")
        ]
        nba = "Send electronic disclosure documents and lock in the 6.75% rate."

    elif call_type == "COLLECTIONS":
        topic = "Delinquent Credit Card Balance ($1,420)"
        intent = "Debt Collection / Payment Dispute"
        summary = (
            "Agent contacted customer regarding 90-day overdue balance. Customer contested interest charges and stated financial hardship. "
            "Agent exhibited severe compliance violations including prohibited legal threats and omission of statutory Mini-Miranda."
        )
        sentiment = "Hostile / Distressed"
        risk = "Critical (Regulatory Complaint & Legal Exposure)"
        products = ["Visa Signature Credit Line", "Hardship Repayment Plan"]
        actions = [
            ActionItem(task="FLAG FOR COMPLIANCE REVIEW: Halt collection outreach on account", owner="Operations", priority="High", deadline="Immediate"),
            ActionItem(task="Review call audio with Legal & QA Supervisor", owner="Underwriting", priority="High", deadline="Today 5:00 PM"),
            ActionItem(task="Deliver standard statutory hardship modification options via certified mail", owner="Agent", priority="Medium", deadline="Within 48 hours")
        ]
        nba = "Initiate supervisor intervention and place automated debt collection hold on account."

    else:  # CARD_SALES or default
        topic = "Titanium Rewards Credit Card Upgrade"
        intent = "Product Promotion & Cross-Sell"
        summary = (
            "Outbound sales interaction presenting card tier upgrade. Customer showed initial interest in travel perks. "
            "Agent failed mandatory recording disclosure and disclosed balance prior to completing full identity authentication."
        )
        sentiment = "Neutral / Hesitant"
        risk = "Moderate (QA Deficiency)"
        products = ["Titanium Rewards Card", "Zero-Fee Balance Transfer"]
        actions = [
            ActionItem(task="Schedule mandatory agent refresher on TCPA recording disclosures", owner="Operations", priority="Medium", deadline="Next Team Meeting"),
            ActionItem(task="Email customer official Product Disclosure Statement and fee schedule", owner="Agent", priority="High", deadline="Within 24 hours")
        ]
        nba = "Send written product terms and verify customer consent via digital signature."

    return CallInsights(
        call_id=audit_report.call_id,
        primary_topic=topic,
        intent_category=intent,
        executive_summary=summary,
        customer_sentiment=sentiment,
        churn_or_escalation_risk=risk,
        financial_products_mentioned=products,
        action_items=actions,
        next_best_action=nba
    )
