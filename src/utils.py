import anthropic
from config.config import Config
import json

def call_claude(prompt, system_prompt=None, temperature=None):
    """
    Make a call to Claude API
    
    Args:
        prompt: User prompt/query
        system_prompt: System instructions for Claude
        temperature: Sampling temperature (default from config)
    
    Returns:
        Response text from Claude
    """
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    temp = temperature if temperature is not None else Config.TEMPERATURE
    
    try:
        message = client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=Config.MAX_TOKENS,
            temperature=temp,
            system=system_prompt if system_prompt else "",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
    
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"


def extract_json_from_response(response_text):
    """
    Extract JSON from Claude's response, handling markdown code blocks
    
    Args:
        response_text: Raw response from Claude
    
    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        return json.loads(response_text)
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        return None


def calculate_confidence_score(classification_result, kb_results):
    """
    Calculate confidence score based on classification and KB search results
    
    Args:
        classification_result: Dict with category, urgency from triage
        kb_results: List of similar cases from knowledge base
    
    Returns:
        Float confidence score between 0 and 1
    """
    confidence = 0.5  # Base confidence
    
    # Increase confidence if we found similar cases
    if kb_results and len(kb_results) > 0:
        confidence += 0.3
    
    # Increase confidence if category is clear
    if classification_result.get('category') in Config.CATEGORIES:
        confidence += 0.2
    
    return min(confidence, 1.0)  # Cap at 1.0


def format_kb_results(kb_results):
    """
    Format knowledge base results for display
    
    Args:
        kb_results: List of similar cases
    
    Returns:
        Formatted string for presentation
    """
    if not kb_results:
        return "No similar cases found."
    
    formatted = "Similar Cases Found:\n\n"
    for idx, case in enumerate(kb_results, 1):
        formatted += f"{idx}. Case ID: {case.get('id', 'N/A')}\n"
        formatted += f"   Category: {case.get('category', 'N/A')}\n"
        formatted += f"   Query: {case.get('query', 'N/A')[:100]}...\n"
        formatted += f"   Resolution: {case.get('resolution', 'N/A')[:150]}...\n\n"
    
    return formatted
