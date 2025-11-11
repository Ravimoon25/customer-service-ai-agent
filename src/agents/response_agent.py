import sys
sys.path.append('../..')

from src.utils import call_claude
from config.config import Config


class ResponseAgent:
    """
    Response Generator Agent: Creates personalized customer responses
    """
    
    def __init__(self):
        pass
    
    def generate(self, customer_query, triage_result, kb_results):
        """
        Generate personalized response based on context
        
        Args:
            customer_query: Original customer question
            triage_result: Dict from triage agent (category, urgency, etc.)
            kb_results: List of similar cases from KB agent
        
        Returns:
            Generated response string
        """
        
        # Build context from KB results
        kb_context = self._format_kb_context(kb_results)
        
        system_prompt = f"""You are a professional customer service agent for an academic journal.

Your tone should be:
- Empathetic and understanding
- Professional but warm
- Clear and specific
- Apologetic when there are delays
- Helpful with actionable information

Guidelines:
- Address the customer's specific concern
- Provide concrete timelines when possible
- Be honest about delays or issues
- Offer next steps or alternatives
- Keep response concise (3-4 paragraphs max)
- Use the similar cases as reference but personalize for this specific query
- If urgency is HIGH, acknowledge the concern immediately

DO NOT:
- Make promises you can't keep
- Use overly formal language
- Copy-paste resolution text verbatim
- Ignore the customer's emotional state
"""

        user_prompt = f"""Customer Query: {customer_query}

Classification:
- Category: {triage_result.get('category', 'N/A')}
- Urgency: {triage_result.get('urgency', 'medium')}
- Manuscript ID: {triage_result.get('manuscript_id', 'Not specified')}
- Issue: {triage_result.get('issue_summary', 'N/A')}

{kb_context}

Generate a helpful, empathetic response to this customer based on the context above."""

        response = call_claude(user_prompt, system_prompt, temperature=0.5)
        
        return response
    
    def _format_kb_context(self, kb_results):
        """
        Format KB results into context for response generation
        
        Args:
            kb_results: List of similar cases
        
        Returns:
            Formatted string
        """
        if not kb_results or len(kb_results) == 0:
            return "Similar Cases: None found. Generate response based on general best practices."
        
        context = "Similar Past Cases (for reference):\n\n"
        
        for idx, case in enumerate(kb_results[:3], 1):  # Use top 3
            context += f"Case {idx}:\n"
            context += f"  Query: {case['query']}\n"
            context += f"  Resolution: {case['resolution']}\n"
            context += f"  Tags: {case.get('tags', 'N/A')}\n\n"
        
        return context
    
    def generate_with_confidence(self, customer_query, triage_result, kb_results):
        """
        Generate response and calculate confidence score
        
        Args:
            customer_query: Original query
            triage_result: Triage classification
            kb_results: KB search results
        
        Returns:
            Tuple of (response_text, confidence_score, should_escalate)
        """
        response = self.generate(customer_query, triage_result, kb_results)
        
        # Calculate confidence
        confidence = self._calculate_confidence(triage_result, kb_results)
        
        # Determine if should escalate
        should_escalate = (
            confidence < Config.ESCALATION_THRESHOLD or
            triage_result.get('urgency') == 'high' and len(kb_results) == 0
        )
        
        return response, confidence, should_escalate
    
    def generate_with_real_data(self, customer_query, manuscript_info, triage_result, 
                               kb_results, conversation_context):
        """
        Generate response using REAL manuscript data (no hallucination)
        
        Args:
            customer_query: Customer's question
            manuscript_info: Formatted string with real manuscript data
            triage_result: Classification from triage
            kb_results: Similar cases from KB
            conversation_context: Conversation history string
        
        Returns:
            Tuple of (response_text, confidence_score, should_escalate)
        """
        # Build KB context
        kb_context = self._format_kb_context(kb_results)
        
        system_prompt = f"""You are a professional customer service agent for an academic journal.
    
    CRITICAL RULE: You have access to REAL manuscript data below. Use ONLY this information.
    DO NOT make up statuses, dates, or details. If information is missing, say so honestly.
    
    Your tone should be:
    - Empathetic and understanding
    - Professional but warm  
    - Clear and specific
    - Based ONLY on the provided data
    
    Guidelines:
    - Answer based on the REAL manuscript data provided
    - Reference similar cases for additional context
    - If data is incomplete, acknowledge it
    - Provide actionable next steps
    - Keep response concise (2-3 paragraphs)
    
    DO NOT:
    - Invent information not in the data
    - Make up reviewer names, dates, or decisions
    - Promise things not supported by the data
    """
    
        user_prompt = f"""Customer Query: {customer_query}
    
    {manuscript_info}
    
    Conversation Context:
    {conversation_context}
    
    Classification:
    - Category: {triage_result.get('category', 'N/A')}
    - Urgency: {triage_result.get('urgency', 'medium')}
    
    {kb_context}
    
    Generate a helpful response based ONLY on the real manuscript data provided above."""
    
        response = call_claude(user_prompt, system_prompt, temperature=0.3)
        
        # Calculate confidence
        confidence = self._calculate_confidence_with_data(triage_result, kb_results, manuscript_info)
        
        # Escalation logic
        should_escalate = (
            confidence < Config.ESCALATION_THRESHOLD or
            triage_result.get('urgency') == 'high'
        )
        
        return response, confidence, should_escalate

    def _calculate_confidence_with_data(self, triage_result, kb_results, manuscript_info):
        """Calculate confidence when we have real data"""
        confidence = 0.7  # Higher base because we have real data
        
        # Increase if we found similar cases
        if kb_results and len(kb_results) > 0:
            confidence += 0.15
        
        # Increase if category is clear
        if triage_result.get('category') in Config.CATEGORIES:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _calculate_confidence(self, triage_result, kb_results):
        """
        Calculate confidence score for the response
        
        Args:
            triage_result: Classification from triage
            kb_results: KB search results
        
        Returns:
            Float between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Increase if we found similar cases
        if kb_results and len(kb_results) > 0:
            confidence += 0.2
            
            # More confidence with higher relevance scores
            avg_relevance = sum(c.get('relevance_score', 0) for c in kb_results) / len(kb_results)
            confidence += avg_relevance * 0.2
        
        # Increase if category is clear
        if triage_result.get('category') in Config.CATEGORIES:
            confidence += 0.1
        
        return min(confidence, 1.0)


# Test the agent if run directly
if __name__ == "__main__":
    agent = ResponseAgent()
    
    # Mock test data
    test_query = "My manuscript MS-2024-1234 has been in review for 10 weeks. This is taking too long!"
    
    test_triage = {
        "category": "review_delay",
        "urgency": "high",
        "manuscript_id": "MS-2024-1234",
        "issue_summary": "Review exceeding normal timeline"
    }
    
    test_kb_results = [
        {
            "id": "CASE_0001",
            "query": "My manuscript has been in review for 8 weeks",
            "resolution": "We apologize for the delay. One reviewer had to withdraw. We assigned a replacement and expedited the process.",
            "tags": ["reviewer_replacement", "expedited"],
            "relevance_score": 0.75
        }
    ]
    
    print("Testing Response Agent...")
    print(f"Query: {test_query}\n")
    
    response, confidence, escalate = agent.generate_with_confidence(
        test_query, test_triage, test_kb_results
    )
    
    print("Generated Response:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print(f"\nConfidence Score: {confidence:.2f}")
    print(f"Should Escalate: {escalate}")
