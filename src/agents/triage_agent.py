import sys
sys.path.append('../..')

from src.utils import call_claude, extract_json_from_response
from config.config import Config


class TriageAgent:
    """
    Triage Agent: Classifies customer queries and extracts key information
    """
    
    def __init__(self):
        self.categories = Config.CATEGORIES
        self.urgency_levels = Config.URGENCY_LEVELS
    
    def classify(self, query):
        """
        Classify customer query and extract entities
        
        Args:
            query: Customer's question/complaint
        
        Returns:
            Dict with category, urgency, manuscript_id, and issue_summary
        """
        
        system_prompt = f"""You are a customer service triage specialist for an academic journal. 
Your job is to analyze customer queries and extract key information.

Categories available:
{', '.join(self.categories)}

Urgency levels:
{', '.join(self.urgency_levels)}

Analyze the query and respond with ONLY a JSON object (no other text) in this format:
{{
    "category": "one of the available categories",
    "urgency": "low/medium/high",
    "manuscript_id": "extracted manuscript ID or null",
    "issue_summary": "brief 1-sentence summary of the issue"
}}

Rules:
- urgency is "high" if: customer is frustrated, mentions delays >8 weeks, needs immediate action
- urgency is "medium" if: standard timeline concerns, routine follow-ups
- urgency is "low" if: general questions, no time pressure
- Extract manuscript_id if present (format: MS-YYYY-NNNN)
- Keep issue_summary under 20 words
"""
        
        user_prompt = f"Customer Query: {query}"
        
        response = call_claude(user_prompt, system_prompt)
        result = extract_json_from_response(response)
        
        if result:
            return result
        else:
            # Fallback if JSON parsing fails
            return {
                "category": "status_inquiry",
                "urgency": "medium",
                "manuscript_id": None,
                "issue_summary": "Unable to classify query"
            }
    
    def extract_manuscript_id(self, text):
        """
        Extract manuscript ID from text using pattern matching
        
        Args:
            text: Text to search
        
        Returns:
            Manuscript ID or None
        """
        import re
        pattern = r'MS-\d{4}-\d{4}'
        match = re.search(pattern, text)
        return match.group(0) if match else None


# Test the agent if run directly
if __name__ == "__main__":
    agent = TriageAgent()
    
    # Test query
    test_query = "My manuscript MS-2024-1234 has been in review for 10 weeks. This is unacceptable!"
    
    print("Testing Triage Agent...")
    print(f"Query: {test_query}\n")
    
    result = agent.classify(test_query)
    print("Classification Result:")
    print(f"  Category: {result['category']}")
    print(f"  Urgency: {result['urgency']}")
    print(f"  Manuscript ID: {result['manuscript_id']}")
    print(f"  Issue Summary: {result['issue_summary']}")
