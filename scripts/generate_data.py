import pandas as pd
import json
from datetime import datetime, timedelta
import random

def generate_synthetic_data():
    """Generate synthetic customer service data for manuscript status inquiries"""
    
    conversations = []
    
    # Status Inquiry Cases (10 examples)
    status_cases = [
        {
            "query": "I submitted my manuscript MS-2024-1234 three weeks ago and haven't heard back. Can you update me on its status?",
            "category": "status_inquiry",
            "urgency": "medium",
            "manuscript_id": "MS-2024-1234",
            "resolution": "Your manuscript MS-2024-1234 is currently under review. It was assigned to reviewers on October 20, 2024. The typical review period is 4-6 weeks. You should receive feedback by November 15, 2024.",
            "tags": ["initial_review", "timeline_query"]
        },
        {
            "query": "Hello, I would like to know the current status of manuscript MS-2024-2156. It's been 2 months since submission.",
            "category": "status_inquiry",
            "urgency": "high",
            "manuscript_id": "MS-2024-2156",
            "resolution": "Thank you for your inquiry. MS-2024-2156 has completed peer review. The Associate Editor is currently preparing the decision letter. You can expect to receive the decision within 3-5 business days.",
            "tags": ["post_review", "decision_pending"]
        },
        {
            "query": "Can you tell me what's happening with MS-2024-3401? I submitted it on September 1st.",
            "category": "status_inquiry",
            "urgency": "medium",
            "manuscript_id": "MS-2024-3401",
            "resolution": "MS-2024-3401 is currently with the Editor-in-Chief for final review. Initial peer reviews were positive with minor revisions recommended. The editorial decision will be communicated by November 12, 2024.",
            "tags": ["editor_review", "positive_feedback"]
        },
        {
            "query": "What's the current status of MS-2024-4501? I need to update my CV for a job application.",
            "category": "status_inquiry",
            "urgency": "high",
            "manuscript_id": "MS-2024-4501",
            "resolution": "MS-2024-4501 is in the final production stage. Your manuscript has been accepted and is scheduled for publication in the December 2024 issue. You will receive the page proofs within 5 business days.",
            "tags": ["accepted", "production_stage"]
        },
        {
            "query": "I submitted MS-2024-5602 on October 1st. Can you please check the status?",
            "category": "status_inquiry",
            "urgency": "low",
            "manuscript_id": "MS-2024-5602",
            "resolution": "MS-2024-5602 is currently in the initial screening phase with the Editorial Office. The manuscript is being checked for formatting and journal scope compliance. You should receive an update within 7 business days.",
            "tags": ["initial_screening", "editorial_office"]
        }
    ]
    
    # Review Delay Cases (8 examples)
    delay_cases = [
        {
            "query": "My manuscript MS-2024-6701 has been in review for 8 weeks. This is longer than the promised timeline. What's causing the delay?",
            "category": "review_delay",
            "urgency": "high",
            "manuscript_id": "MS-2024-6701",
            "resolution": "We apologize for the delay with MS-2024-6701. One reviewer had to withdraw due to unforeseen circumstances. We have assigned a replacement reviewer and expedited the process. You should receive reviews by November 18, 2024.",
            "tags": ["reviewer_replacement", "expedited"]
        },
        {
            "query": "It's been 10 weeks since I submitted MS-2024-7802. The journal website says typical review time is 4-6 weeks. Should I be concerned?",
            "category": "review_delay",
            "urgency": "high",
            "manuscript_id": "MS-2024-7802",
            "resolution": "Thank you for your patience. MS-2024-7802 experienced a delay because the topic required specialized reviewers. We have now received both reviews and the Associate Editor is preparing the decision. You will hear from us within 48 hours.",
            "tags": ["specialized_review", "decision_imminent"]
        },
        {
            "query": "MS-2024-8903 has been under review for 12 weeks now. This is unacceptable. I want an update immediately.",
            "category": "review_delay",
            "urgency": "high",
            "manuscript_id": "MS-2024-8903",
            "resolution": "We sincerely apologize for the extended delay with MS-2024-8903. We have escalated this to the Editor-in-Chief. One review has been received, and we are actively following up with the second reviewer. We will provide you with a definitive timeline within 24 hours.",
            "tags": ["escalated", "editor_followup"]
        },
        {
            "query": "The review for MS-2024-9104 is taking much longer than expected. Can you expedite this?",
            "category": "review_delay",
            "urgency": "medium",
            "manuscript_id": "MS-2024-9104",
            "resolution": "We understand your concern regarding MS-2024-9104. The delay was due to the holiday season affecting reviewer availability. We have sent reminders to both reviewers and set a deadline of November 20, 2024. If we don't receive reviews by then, we will assign new reviewers.",
            "tags": ["holiday_delay", "reminder_sent"]
        }
    ]
    
    # Decision Timeline Cases (7 examples)
    decision_cases = [
        {
            "query": "I received a 'revise and resubmit' decision for MS-2024-1005. How long do I have to submit revisions?",
            "category": "decision_timeline",
            "urgency": "low",
            "manuscript_id": "MS-2024-1005",
            "resolution": "Congratulations on the revise and resubmit decision for MS-2024-1005. You have 60 days from the decision date (October 15, 2024) to submit your revised manuscript. If you need an extension, please contact us at least one week before the deadline.",
            "tags": ["revision_deadline", "major_revision"]
        },
        {
            "query": "When can I expect a final decision on MS-2024-1106? I submitted revisions 3 weeks ago.",
            "category": "decision_timeline",
            "urgency": "medium",
            "manuscript_id": "MS-2024-1106",
            "resolution": "Your revised manuscript MS-2024-1106 is currently being reviewed by the Associate Editor. Since this is a revision review, the process typically takes 2-3 weeks. You should receive the final decision by November 22, 2024.",
            "tags": ["revision_review", "associate_editor"]
        },
        {
            "query": "How long does the decision process take after peer review? My manuscript is MS-2024-1207.",
            "category": "decision_timeline",
            "urgency": "low",
            "manuscript_id": "MS-2024-1207",
            "resolution": "For MS-2024-1207, after peer reviews are completed, the Associate Editor typically takes 5-7 business days to review the feedback and make a recommendation. The Editor-in-Chief then makes the final decision within 3-5 business days. Total timeline is usually 10-14 business days.",
            "tags": ["decision_process", "timeline_explanation"]
        },
        {
            "query": "I got minor revisions for MS-2024-1308. Is the revision deadline the same as major revisions?",
            "category": "decision_timeline",
            "urgency": "low",
            "manuscript_id": "MS-2024-1308",
            "resolution": "For minor revisions on MS-2024-1308, you have 30 days from the decision date to submit your revised manuscript (rather than 60 days for major revisions). Your deadline is December 1, 2024. The re-review process for minor revisions is typically faster, around 1-2 weeks.",
            "tags": ["minor_revision", "shorter_deadline"]
        }
    ]
    
    # Revision Submission Cases (6 examples)
    revision_cases = [
        {
            "query": "I'm ready to submit my revised manuscript for MS-2024-1409. What's the process?",
            "category": "revision_submission",
            "urgency": "low",
            "manuscript_id": "MS-2024-1409",
            "resolution": "To submit your revisions for MS-2024-1409: 1) Log into the submission portal, 2) Click 'Revisions' and find MS-2024-1409, 3) Upload your revised manuscript and response to reviewers letter, 4) Click 'Submit Revision'. Please ensure you address all reviewer comments in your response letter.",
            "tags": ["submission_process", "instructions"]
        },
        {
            "query": "Can I get an extension for submitting revisions? My manuscript is MS-2024-1510 and the deadline is in 5 days.",
            "category": "revision_submission",
            "urgency": "medium",
            "manuscript_id": "MS-2024-1510",
            "resolution": "We can grant a 2-week extension for MS-2024-1510 revisions. Your new deadline will be December 8, 2024. Please note that this is typically the maximum extension we can offer. If you need additional time beyond this, please provide justification to the handling editor.",
            "tags": ["extension_request", "deadline_extended"]
        },
        {
            "query": "I submitted my revisions for MS-2024-1611 but forgot to include the response to reviewers letter. Can I upload it separately?",
            "category": "revision_submission",
            "urgency": "medium",
            "manuscript_id": "MS-2024-1611",
            "resolution": "Yes, you can upload the response letter for MS-2024-1611. Please log back into the submission system, navigate to MS-2024-1611, and use the 'Upload Additional File' option. Select 'Response to Reviewers' as the file type. We'll notify the editor once it's uploaded.",
            "tags": ["missing_document", "additional_upload"]
        },
        {
            "query": "Do I need to submit a clean copy and tracked changes version for MS-2024-1712 revisions?",
            "category": "revision_submission",
            "urgency": "low",
            "manuscript_id": "MS-2024-1712",
            "resolution": "Yes, for MS-2024-1712 revisions, please submit both: 1) A clean manuscript file without tracked changes, 2) A marked-up version showing all changes. This helps reviewers quickly identify your modifications while having a clean version for final review.",
            "tags": ["submission_requirements", "file_formats"]
        }
    ]
    
    # Withdrawal Request Cases (5 examples)
    withdrawal_cases = [
        {
            "query": "I need to withdraw my manuscript MS-2024-1813. We've decided to submit it elsewhere.",
            "category": "withdrawal_request",
            "urgency": "medium",
            "manuscript_id": "MS-2024-1813",
            "resolution": "We've processed the withdrawal request for MS-2024-1813. The manuscript has been removed from the review process, and reviewers have been notified. You are free to submit it to another journal. We've sent a withdrawal confirmation email to your registered address.",
            "tags": ["withdrawal_processed", "confirmation"]
        },
        {
            "query": "Can I withdraw MS-2024-1914 and resubmit it later with additional data?",
            "category": "withdrawal_request",
            "urgency": "low",
            "manuscript_id": "MS-2024-1914",
            "resolution": "Yes, you can withdraw MS-2024-1914 now and resubmit later. However, please note that upon resubmission, it will be treated as a new submission and will go through the full review process again. If the additional data is minor, you might consider waiting for the review decision and incorporating it during revisions.",
            "tags": ["withdrawal_advice", "resubmission_option"]
        },
        {
            "query": "I want to withdraw MS-2024-2015 immediately. My co-author disagrees with submission to this journal.",
            "category": "withdrawal_request",
            "urgency": "high",
            "manuscript_id": "MS-2024-2015",
            "resolution": "We've received your withdrawal request for MS-2024-2015. However, since this involves a co-author dispute, we require written confirmation from all listed authors before processing the withdrawal. Please have all authors send their consent to editorial@journal.com within 48 hours.",
            "tags": ["coauthor_dispute", "confirmation_required"]
        }
    ]
    
    # Combine all cases
    all_cases = status_cases + delay_cases + decision_cases + revision_cases + withdrawal_cases
    
    # Add metadata
    for idx, case in enumerate(all_cases):
        case['id'] = f"CASE_{idx+1:04d}"
        case['created_date'] = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
        case['resolution_time_hours'] = random.uniform(1, 5)
    
    # Create DataFrame
    df = pd.DataFrame(all_cases)
    
    return df

if __name__ == "__main__":
    print("Generating synthetic customer service data...")
    df = generate_synthetic_data()
    
    # Save to CSV
    output_path = "../data/synthetic_data.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✓ Generated {len(df)} customer service cases")
    print(f"✓ Saved to: {output_path}")
    print(f"\nCategory breakdown:")
    print(df['category'].value_counts())
