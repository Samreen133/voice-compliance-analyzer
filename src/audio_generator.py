"""
Audio Call Generator & Scenario Manager
Generates and manages synthetic multi-speaker banking call recordings using gTTS.
"""

import os
import re
from typing import Dict, List, Any
from gtts import gTTS

SAMPLE_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_audio")
os.makedirs(SAMPLE_AUDIO_DIR, exist_ok=True)

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "compliant_loan": {
        "id": "SCN-001",
        "title": "Compliant Mortgage & Loan Inquiry",
        "call_type": "LOAN_INQUIRY",
        "audio_filename": "compliant_loan_call.mp3",
        "agent": "Sarah Jenkins",
        "customer": "David Miller",
        "expected_score": 96,
        "expected_verdict": "PASS",
        "description": "Standard mortgage inquiry. Agent executes TCPA recording disclosure within 5s, conducts strict 2-factor KYC before sharing data, and clearly states Truth in Lending APR & closing fees.",
        "turns": [
            {"timestamp": "00:04", "speaker": "Agent", "text": "Thank you for calling Apex Financial Mortgage Services. My name is Sarah. Please note that this call is recorded for quality, training, and regulatory compliance."},
            {"timestamp": "00:14", "speaker": "Customer", "text": "Hi Sarah, I'm calling to inquire about taking out a home equity loan on my property for some kitchen remodeling."},
            {"timestamp": "00:22", "speaker": "Agent", "text": "I would be delighted to assist you with that! For your security, before we review account options, may I please verify your full legal name, date of birth, and the last four digits of your Social Security Number?"},
            {"timestamp": "00:35", "speaker": "Customer", "text": "Sure, it is David Miller, date of birth is July 14th, 1984, and the last four digits are 8821."},
            {"timestamp": "00:46", "speaker": "Agent", "text": "Thank you Mr. Miller, your identity is authenticated. Based on your current home valuation, we offer a fixed home equity loan at an Annual Percentage Rate of 6.75% APR, with an estimated closing fee of $750. Terms are subject to final underwriting."},
            {"timestamp": "01:05", "speaker": "Customer", "text": "That rate sounds very reasonable. What would the monthly payment look like on fifty thousand dollars?"},
            {"timestamp": "01:14", "speaker": "Agent", "text": "On a $50,000 loan over 10 years, your estimated monthly principal and interest payment is approximately $574. Full Truth in Lending disclosures will be sent to your secure portal for your review."},
            {"timestamp": "01:29", "speaker": "Customer", "text": "Excellent, please send that over to my email portal."},
            {"timestamp": "01:35", "speaker": "Agent", "text": "I have transmitted the disclosures. Is there anything else I can assist you with today Mr. Miller?"},
            {"timestamp": "01:42", "speaker": "Customer", "text": "No, that covers everything. Thank you so much for the clear explanation!"},
            {"timestamp": "01:48", "speaker": "Agent", "text": "Thank you for choosing Apex Financial. Have a wonderful day!"}
        ]
    },
    "non_compliant_debt": {
        "id": "SCN-002",
        "title": "Non-Compliant Collections Call (FDCPA & Harassment)",
        "call_type": "COLLECTIONS",
        "audio_filename": "non_compliant_debt_call.mp3",
        "agent": "Marcus Vance",
        "customer": "Robert Chen",
        "expected_score": 35,
        "expected_verdict": "CRITICAL_FAIL",
        "description": "Debt recovery outreach. Agent skips Mini-Miranda disclosure, makes prohibited threats of arrest and employer harassment (violating FDCPA § 1692d/e), and refuses hardship evaluation.",
        "turns": [
            {"timestamp": "00:03", "speaker": "Agent", "text": "Is this Robert Chen? Listen Robert, you owe Apex Credit $1,420 and your account is 90 days past due."},
            {"timestamp": "00:11", "speaker": "Customer", "text": "Wait, who is this? How do I even know who you are? You haven't stated where you're calling from."},
            {"timestamp": "00:17", "speaker": "Agent", "text": "It doesn't matter who I am, you need to pay this balance right now or I am sending the sheriff to your workplace to arrest you tomorrow morning."},
            {"timestamp": "00:28", "speaker": "Customer", "text": "You cannot threaten me like that! I lost my job last month and I've been trying to set up a hardship repayment plan."},
            {"timestamp": "00:37", "speaker": "Agent", "text": "Excuses don't pay bills. If you don't give me a debit card number in the next 5 minutes, we will seize your bank accounts and destroy your life with your employer."},
            {"timestamp": "00:50", "speaker": "Customer", "text": "This is illegal harassment! I am reporting this call to the Consumer Financial Protection Bureau and my attorney."},
            {"timestamp": "00:58", "speaker": "Agent", "text": "Go ahead and report it, nobody cares! Pay the $1,420 today or face the consequences!"}
        ]
    },
    "high_risk_sales": {
        "id": "SCN-003",
        "title": "High-Risk Card Sales (Deceptive Promises & PII Exposure)",
        "call_type": "CARD_SALES",
        "audio_filename": "high_risk_sales_call.mp3",
        "agent": "Alex Rivera",
        "customer": "Elena Rostova",
        "expected_score": 42,
        "expected_verdict": "CRITICAL_FAIL",
        "description": "Outbound credit card upgrade. Agent omits recording disclosure, reveals account balance before identity verification, makes illegal 'guaranteed 0% APR forever' promises, and reads unmasked CVV out loud.",
        "turns": [
            {"timestamp": "00:04", "speaker": "Agent", "text": "Hey Elena, this is Alex from Apex Bank! I noticed your current card balance is $8,940, so I'm calling to upgrade you to our Platinum Elite Card."},
            {"timestamp": "00:15", "speaker": "Customer", "text": "Oh, hi Alex. Wait, did you say my balance is $8,940? Don't you need to verify my identity and security questions first?"},
            {"timestamp": "00:23", "speaker": "Agent", "text": "Oh don't worry about verification between us Elena! Look, with this new card, approval is guaranteed, and I promise you 0% interest forever with absolutely zero fees."},
            {"timestamp": "00:36", "speaker": "Customer", "text": "0% forever? That sounds too good to be true. Are there really no balance transfer fees or annual fees?"},
            {"timestamp": "00:44", "speaker": "Agent", "text": "Trust me, zero fees guaranteed! Just give me your existing card number to transfer the balance right now."},
            {"timestamp": "00:52", "speaker": "Customer", "text": "Okay, my card is 4532-8819-2041-9982, expiration 08/28, and CVV is 942."},
            {"timestamp": "01:03", "speaker": "Agent", "text": "Great, let me repeat that back: card 4532-8819-2041-9982 with security code 942, and Social Security 492-11-8921. You're all set!"},
            {"timestamp": "01:17", "speaker": "Customer", "text": "Will you send me the full terms in writing?"},
            {"timestamp": "01:21", "speaker": "Agent", "text": "Yeah yeah, don't worry about the fine print, you're golden! Have a great day."}
        ]
    }
}


def get_scenario(key: str) -> Dict[str, Any]:
    """Retrieve scenario definition by key."""
    return SCENARIOS.get(key, SCENARIOS["compliant_loan"])


def generate_audio_for_scenario(key: str) -> str:
    """
    Synthesizes MP3 audio for the given scenario using gTTS and saves to sample_audio/ directory.
    Returns the absolute path to the generated audio file.
    """
    scenario = get_scenario(key)
    filepath = os.path.join(SAMPLE_AUDIO_DIR, scenario["audio_filename"])

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return filepath

    # Stitch the dialogue for speech synthesis
    dialogue_script = " ... ".join([f"{t['speaker']}: {t['text']}" for t in scenario["turns"]])

    try:
        tts = gTTS(text=dialogue_script, lang="en", tld="com", slow=False)
        tts.save(filepath)
        print(f"Generated synthetic audio: {filepath}")
    except Exception as e:
        print(f"Error generating audio with gTTS: {e}. Creating fallback audio placeholder.")
        # Create dummy file if network issue
        with open(filepath, "wb") as f:
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

    return filepath


def ensure_all_sample_audios():
    """Generates all scenario audio files on startup."""
    paths = {}
    for key in SCENARIOS:
        paths[key] = generate_audio_for_scenario(key)
    return paths


if __name__ == "__main__":
    ensure_all_sample_audios()
