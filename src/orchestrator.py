import sys
sys.path.append('..')

from src.agents.triage_agent import TriageAgent
from src.agents.kb_agent import KnowledgeBaseAgent
from src.agents.response_agent import ResponseAgent
from src.conversation_manager import ConversationManager
from config.config import Config
import time


class CustomerServiceOrchestrator:
    """
    Orchestrator: Coordinates all agents to process customer queries in conversational mode
    """
    
    def __init__(self):
        """Initialize all agents"""
        print("Initializing Customer Service Agent System...")
        self.triage_agent = TriageAgent()
        self.kb_agent = KnowledgeBaseAgent()
        self.response_agent = ResponseAgent()
        print("✓ All agents initialized\n")
    
    def process_message(self, customer_message, conversation, verbose=True):
        """
        Process a single message in an ongoing conversation
        
        Args:
            customer_message: Customer's current message
            conversation: ConversationManager instance
            verbose: Print step-by-step progress
        
        Returns:
            Dict with bot response and metadata
        """
        start_time = time.time()
        
        if verbose:
            print("=" * 70)
            print(f"PROCESSING MESSAGE (Conversation: {conversation.conversation_id})")
            print("=" * 70)
            print(f"Customer: {customer_message}\n")
        
        # Add customer message to conversation
        conversation.add_message('customer', customer_message)
        
        # Step 1: Triage (only if context not already established)
        if not conversation.context['category'] or conversation.context['urgency'] == 'low':
            if verbose:
                print("STEP 1: Triage Agent - Analyzing message...")
            
            triage_result = self.triage_agent.classify(customer_message)
            
            # Update conversation context
            conversation.update_context(
                manuscript_id=triage_result.get('manuscript_id') or conversation.context['manuscript_id'],
                category=triage_result['category'],
                urgency=triage_result['urgency']
            )
            
            if verbose:
                print(f"  ✓ Category: {triage_result['category']}")
                print(f"  ✓ Urgency: {triage_result['urgency']}")
                print(f"  ✓ Manuscript ID: {conversation.context['manuscript_id']}\n")
        else:
            if verbose:
                print("STEP 1: Using existing conversation context...\n")
            triage_result = {
                'category': conversation.context['category'],
                'urgency': conversation.context['urgency'],
                'manuscript_id': conversation.context['manuscript_id'],
                'issue_summary': 'Continuing conversation'
            }
        
        # Step 2: Knowledge Base Search
        if verbose:
            print("STEP 2: Knowledge Base Agent - Searching similar cases...")
        
        kb_results = self.kb_agent.search(
            customer_message,
            category=conversation.context['category'],
            top_k=3
        )
        
        if verbose:
            print(f"  ✓ Found {len(kb_results)} similar cases\n")
        
        # Step 3: Generate Conversational Response
        if verbose:
            print("STEP 3: Response Agent - Generating response...")
        
        bot_response, confidence, should_escalate = self._generate_conversational_response(
            customer_message,
            conversation,
            triage_result,
            kb_results
        )
        
        if verbose:
            print(f"  ✓ Response generated")
            print(f"  ✓ Confidence: {confidence:.2f}")
            print(f"  ✓ Should escalate: {should_escalate}\n")
        
        # Add bot response to conversation
        conversation.add_message('bot', bot_response, metadata={
            'confidence': confidence,
            'triage': triage_result,
            'similar_cases_count': len(kb_results)
        })
        
        # Check for escalation
        if should_escalate or conversation.should_escalate():
            if not conversation.context['escalated']:
                escalation_reason = self._determine_escalation_reason(
                    confidence, 
                    triage_result, 
                    conversation
                )
                conversation.mark_escalated(escalation_reason)
                if verbose:
                    print(f"  ⚠️  ESCALATED: {escalation_reason}\n")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Compile result
        result = {
            "customer_message": customer_message,
            "bot_response": bot_response,
            "conversation_id": conversation.conversation_id,
            "confidence_score": confidence,
            "should_escalate": conversation.context['escalated'],
            "escalation_reason": conversation.context['escalation_reason'],
            "context": conversation.context,
            "processing_time_seconds": round(processing_time, 2),
            "message_count": len(conversation.messages)
        }
        
        if verbose:
            print("=" * 70)
            print("BOT RESPONSE")
            print("=" * 70)
            print(bot_response)
            print("=" * 70)
            print(f"\n⏱️  Processing time: {processing_time:.2f} seconds")
            if conversation.context['escalated']:
                print(f"⚠️  ESCALATED: {conversation.context['escalation_reason']}")
            print()
        
        return result
    
    def _generate_conversational_response(self, customer_message, conversation, 
                                         triage_result, kb_results):
        """
        Generate response with conversation context
        
        Args:
            customer_message: Current customer message
            conversation: ConversationManager instance
            triage_result: Triage classification
            kb_results: Similar cases from KB
        
        Returns:
            Tuple of (response, confidence, should_escalate)
        """
        # Build enhanced context for response generation
        context_string = conversation.get_context_string()
        
        # Enhance the customer query with conversation context
        enhanced_query = f"""
Conversation Context:
{context_string}

Current Customer Message: {customer_message}

Generate a response that:
1. Acknowledges the conversation history
2. Directly addresses the current question
3. Maintains consistent information across the conversation
4. Uses the customer's manuscript ID if mentioned before
"""
        
        response, confidence, should_escalate = self.response_agent.generate_with_confidence(
            enhanced_query,
            triage_result,
            kb_results
        )
        
        return response, confidence, should_escalate
    
    def _determine_escalation_reason(self, confidence, triage_result, conversation):
        """
        Determine specific reason for escalation
        
        Args:
            confidence: Response confidence score
            triage_result: Triage classification
            conversation: ConversationManager instance
        
        Returns:
            String describing escalation reason
        """
        reasons = []
        
        if confidence < Config.ESCALATION_THRESHOLD:
            reasons.append(f"Low confidence ({confidence:.0%})")
        
        if triage_result['urgency'] == 'high':
            reasons.append("High urgency issue")
        
        if len(conversation.messages) > 6:
            reasons.append("Extended conversation (>3 exchanges)")
        
        # Check for frustration keywords
        recent_customer_messages = [
            msg['content'] for msg in conversation.get_conversation_history(3)
            if msg['role'] == 'customer'
        ]
        frustrated_keywords = ['unacceptable', 'ridiculous', 'angry', 'complaint', 
                              'manager', 'escalate', 'disappointed']
        
        for msg in recent_customer_messages:
            if any(keyword in msg.lower() for keyword in frustrated_keywords):
                reasons.append("Customer frustration detected")
                break
        
        return " | ".join(reasons) if reasons else "Agent recommendation"
    
    def create_conversation(self):
        """
        Create a new conversation instance
        
        Returns:
            ConversationManager instance
        """
        return ConversationManager()
    
    def get_system_stats(self):
        """
        Get statistics about the system
        
        Returns:
            Dict with system stats
        """
        kb_stats = self.kb_agent.get_stats()
        
        return {
            "knowledge_base": kb_stats,
            "categories": Config.CATEGORIES,
            "urgency_levels": Config.URGENCY_LEVELS,
            "model": Config.CLAUDE_MODEL
        }


# Test the orchestrator if run directly
if __name__ == "__main__":
    orchestrator = CustomerServiceOrchestrator()
    
    # Create a conversation
    conversation = orchestrator.create_conversation()
    
    # Simulate multi-turn conversation
    messages = [
        "I submitted my manuscript MS-2024-1234 three weeks ago. What's the status?",
        "How much longer will it take?",
        "This is taking too long! I need an answer now!"
    ]
    
    print("Testing multi-turn conversation...\n")
    
    for msg in messages:
        result = orchestrator.process_message(msg, conversation)
        print("\n" + "="*70 + "\n")
    
    # Show escalation summary
    if conversation.context['escalated']:
        print("\n" + "="*70)
        print("ESCALATION SUMMARY FOR HUMAN AGENT")
        print("="*70)
        import json
        print(json.dumps(conversation.get_escalation_summary(), indent=2))
