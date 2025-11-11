import sys
sys.path.append('..')

from src.agents.triage_agent import TriageAgent
from src.agents.kb_agent import KnowledgeBaseAgent
from src.agents.response_agent import ResponseAgent
from src.agents.manuscript_lookup_agent import ManuscriptLookupAgent
from src.conversation_manager import ConversationManager
from config.config import Config
import time
import re


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
        self.manuscript_lookup_agent = ManuscriptLookupAgent()
        print("✓ All agents initialized\n")
    
    def process_message(self, customer_message, conversation, verbose=True):
        """
        Process a single message in an ongoing conversation with structured workflow
        
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
        
        # STEP 1: Extract manuscript ID from message
        manuscript_id = self._extract_manuscript_id(customer_message)
        
        if verbose and manuscript_id:
            print(f"STEP 1: Extracted manuscript ID: {manuscript_id}")
        
        # STEP 2: Check if we have manuscript ID in context
        if not manuscript_id and not conversation.context.get('manuscript_id'):
            if verbose:
                print("STEP 2: No manuscript ID found - asking customer\n")
            
            bot_response = self._ask_for_manuscript_id()
            conversation.add_message('bot', bot_response)
            
            result = self._build_result(
                customer_message, bot_response, conversation,
                confidence=0.3, should_escalate=False,
                processing_time=time.time() - start_time
            )
            
            if verbose:
                self._print_result(bot_response, result)
            
            return result
        
        # Update context with manuscript ID if found
        if manuscript_id:
            conversation.update_context(manuscript_id=manuscript_id)
        
        manuscript_id = conversation.context['manuscript_id']
        
        if verbose:
            print(f"STEP 2: Using manuscript ID: {manuscript_id}\n")
        
        # STEP 3: Look up REAL manuscript status
        if verbose:
            print("STEP 3: Looking up manuscript in database...")
        
        manuscript_data = self.manuscript_lookup_agent.lookup(manuscript_id)
        
        if not manuscript_data:
            if verbose:
                print(f"  ✗ Manuscript {manuscript_id} not found in database\n")
            
            bot_response = self._manuscript_not_found(manuscript_id)
            conversation.add_message('bot', bot_response)
            conversation.mark_escalated(f"Manuscript {manuscript_id} not found in system")
            
            result = self._build_result(
                customer_message, bot_response, conversation,
                confidence=0.0, should_escalate=True,
                processing_time=time.time() - start_time
            )
            
            if verbose:
                self._print_result(bot_response, result)
            
            return result
        
        if verbose:
            print(f"  ✓ Found manuscript: {manuscript_data['current_status']}")
            print(f"  ✓ Author: {manuscript_data['author_name']}")
            print(f"  ✓ Submission: {manuscript_data['submission_date']}\n")
        
        # STEP 4: Classify the query type
        if verbose:
            print("STEP 4: Triage Agent - Classifying query type...")
        
        triage_result = self.triage_agent.classify(customer_message)
        conversation.update_context(
            category=triage_result['category'],
            urgency=triage_result['urgency']
        )
        
        if verbose:
            print(f"  ✓ Category: {triage_result['category']}")
            print(f"  ✓ Urgency: {triage_result['urgency']}\n")
        
        # STEP 5: Check if query is relevant/on-topic
        if verbose:
            print("STEP 5: Checking query relevance...")
        
        if self._is_irrelevant_query(customer_message, triage_result):
            if verbose:
                print("  ✗ Query is off-topic - escalating to human\n")
            
            bot_response = self._escalate_irrelevant_query()
            conversation.add_message('bot', bot_response)
            conversation.mark_escalated("Off-topic query - outside scope")
            conversation.context['closed'] = True
            
            result = self._build_result(
                customer_message, bot_response, conversation,
                confidence=0.0, should_escalate=True,
                processing_time=time.time() - start_time
            )
            
            if verbose:
                self._print_result(bot_response, result)
            
            return result
        
        if verbose:
            print("  ✓ Query is relevant\n")
        
        # STEP 6: Search KB for similar cases (for better responses)
        if verbose:
            print("STEP 6: Knowledge Base Agent - Searching similar cases...")
        
        kb_results = self.kb_agent.search(
            customer_message,
            category=triage_result['category'],
            top_k=3
        )
        
        if verbose:
            print(f"  ✓ Found {len(kb_results)} similar cases\n")
        
        # STEP 7: Generate response using REAL manuscript data
        if verbose:
            print("STEP 7: Response Agent - Generating response from real data...")
        
        bot_response, confidence = self._generate_response_from_real_data(
            customer_message,
            manuscript_data,
            triage_result,
            kb_results,
            conversation
        )
        
        if verbose:
            print(f"  ✓ Response generated")
            print(f"  ✓ Confidence: {confidence:.2f}\n")
        
        # Add bot response to conversation
        conversation.add_message('bot', bot_response, metadata={
            'confidence': confidence,
            'triage': triage_result,
            'manuscript_data': manuscript_data,
            'similar_cases_count': len(kb_results)
        })
        
        # STEP 8: Check if customer is satisfied (conversation close signal)
        if verbose:
            print("STEP 8: Checking for satisfaction/close signals...")
        
        if self._customer_satisfied(customer_message):
            if verbose:
                print("  ✓ Customer satisfaction detected - closing conversation\n")
            
            closing_message = "\n\n✓ I'm glad I could help! If you have any other questions in the future, feel free to start a new conversation. Have a great day!"
            bot_response += closing_message
            conversation.context['closed'] = True
        else:
            if verbose:
                print("  ✓ Conversation continues\n")
        
        # STEP 9: Check for escalation needs
        should_escalate = (
            confidence < Config.ESCALATION_THRESHOLD or
            conversation.should_escalate()
        )
        
        if should_escalate and not conversation.context['escalated']:
            escalation_reason = self._determine_escalation_reason(
                confidence, triage_result, conversation
            )
            conversation.mark_escalated(escalation_reason)
            if verbose:
                print(f"  ⚠️  ESCALATED: {escalation_reason}\n")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Build result
        result = self._build_result(
            customer_message, bot_response, conversation,
            confidence, should_escalate, processing_time
        )
        
        if verbose:
            self._print_result(bot_response, result)
        
        return result
    
    def _extract_manuscript_id(self, text):
        """
        Extract manuscript ID from text using regex
        
        Args:
            text: Text to search
        
        Returns:
            Manuscript ID or None
        """
        pattern = r'MS-\d{4}-\d{4}'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0).upper() if match else None
    
    def _ask_for_manuscript_id(self):
        """Generate message asking for manuscript ID"""
        return """To help you with your query, I'll need your manuscript ID.

It's typically in the format: **MS-YYYY-NNNN** (e.g., MS-2024-1234)

You can find it in:
- Your submission confirmation email
- The journal submission portal
- Any correspondence from the editorial office

Please provide your manuscript ID so I can look up the current status for you."""
    
    def _manuscript_not_found(self, manuscript_id):
        """Generate message when manuscript not found"""
        return f"""I couldn't find manuscript **{manuscript_id}** in our system.

This could mean:
- The manuscript ID might be incorrect (please double-check the format)
- It may have been submitted to a different journal
- It might not be in our tracking system yet (very recent submissions)

**What you can do:**
1. Verify the manuscript ID and try again
2. Contact our editorial office directly: editorial@journal.com
3. Check the submission portal for the correct ID

I've flagged this for our team to investigate. Would you like to speak with a human agent?"""
    
    def _is_irrelevant_query(self, message, triage_result):
        """
        Check if query is off-topic/irrelevant
        
        Args:
            message: Customer message
            triage_result: Classification from triage agent
        
        Returns:
            Boolean
        """
        # List of clearly off-topic keywords
        irrelevant_keywords = [
            'weather', 'recipe', 'cook', 'sports', 'movie', 'film',
            'stock market', 'crypto', 'bitcoin', 'programming help',
            'homework', 'travel', 'shopping', 'restaurant', 'hotel',
            'game', 'music', 'song', 'celebrity'
        ]
        
        message_lower = message.lower()
        
        # Check for irrelevant keywords
        if any(keyword in message_lower for keyword in irrelevant_keywords):
            return True
        
        # If triage couldn't categorize it properly
        if triage_result['category'] not in Config.CATEGORIES:
            return True
        
        # Check if it's a greeting without substance
        greeting_only = ['hi', 'hello', 'hey', 'good morning', 'good afternoon']
        if message_lower.strip() in greeting_only and len(message.split()) <= 3:
            return False  # Greetings are fine
        
        return False
    
    def _customer_satisfied(self, message):
        """
        Detect if customer is satisfied/done
        
        Args:
            message: Customer message
        
        Returns:
            Boolean
        """
        satisfied_phrases = [
            'thank you', 'thanks', 'thank u', 'thx',
            'that helps', 'that help', 'perfect', 'great',
            'appreciate', 'got it', 'understood', 'clear',
            'that\'s all', 'no more questions', 'all set',
            'good to know', 'makes sense', 'helpful'
        ]
        
        message_lower = message.lower()
        
        # Check for satisfaction phrases
        return any(phrase in message_lower for phrase in satisfied_phrases)
    
    def _escalate_irrelevant_query(self):
        """Generate escalation message for off-topic queries"""
        return """I notice your question is outside my area of expertise. I specialize in:
- Manuscript status inquiries
- Review timelines and delays
- Submission and revision processes
- Editorial decisions

For other inquiries, I'm connecting you with a human agent who can better assist you.

**This conversation will be closed**, but feel free to start a new chat for manuscript-related questions.

A team member will reach out to you shortly."""
    
    def _generate_response_from_real_data(self, customer_message, manuscript_data,
                                          triage_result, kb_results, conversation):
        """
        Generate response using REAL manuscript data
        
        Args:
            customer_message: Customer's question
            manuscript_data: Real data from database
            triage_result: Classification
            kb_results: Similar cases from KB
            conversation: Conversation context
        
        Returns:
            Tuple of (response_text, confidence_score)
        """
        # Build context with real data
        context_string = conversation.get_context_string()
        
        # Format manuscript data for prompt
        manuscript_info = f"""
REAL MANUSCRIPT DATA:
- Manuscript ID: {manuscript_data['manuscript_id']}
- Author: {manuscript_data['author_name']}
- Submission Date: {manuscript_data['submission_date']}
- Current Status: {manuscript_data['current_status']}
- Reviewers: {manuscript_data['reviewer_count']}
- Expected Decision: {manuscript_data.get('decision_date', 'TBD')}
- Notes: {manuscript_data.get('notes', 'None')}
"""
        
        # Use response agent with real data
        response, confidence, _ = self.response_agent.generate_with_real_data(
            customer_message,
            manuscript_info,
            triage_result,
            kb_results,
            context_string
        )
        
        return response, confidence
    
    def _determine_escalation_reason(self, confidence, triage_result, conversation):
        """Determine specific reason for escalation"""
        reasons = []
        
        if confidence < Config.ESCALATION_THRESHOLD:
            reasons.append(f"Low confidence ({confidence:.0%})")
        
        if triage_result['urgency'] == 'high':
            reasons.append("High urgency issue")
        
        if len(conversation.messages) > 8:
            reasons.append("Extended conversation (>4 exchanges)")
        
        # Check for frustration keywords
        recent_customer_messages = [
            msg['content'] for msg in conversation.get_conversation_history(3)
            if msg['role'] == 'customer'
        ]
        frustrated_keywords = ['unacceptable', 'ridiculous', 'angry', 'complaint',
                              'manager', 'escalate', 'disappointed', 'frustrated']
        
        for msg in recent_customer_messages:
            if any(keyword in msg.lower() for keyword in frustrated_keywords):
                reasons.append("Customer frustration detected")
                break
        
        return " | ".join(reasons) if reasons else "Agent recommendation"
    
    def _build_result(self, customer_message, bot_response, conversation,
                     confidence, should_escalate, processing_time):
        """Build result dictionary"""
        return {
            "customer_message": customer_message,
            "bot_response": bot_response,
            "conversation_id": conversation.conversation_id,
            "confidence_score": confidence,
            "should_escalate": conversation.context['escalated'],
            "escalation_reason": conversation.context['escalation_reason'],
            "conversation_closed": conversation.context.get('closed', False),
            "context": conversation.context,
            "processing_time_seconds": round(processing_time, 2),
            "message_count": len(conversation.messages)
        }
    
    def _print_result(self, bot_response, result):
        """Print formatted result"""
        print("=" * 70)
        print("BOT RESPONSE")
        print("=" * 70)
        print(bot_response)
        print("=" * 70)
        print(f"\n⏱️  Processing time: {result['processing_time_seconds']:.2f} seconds")
        if result['should_escalate']:
            print(f"⚠️  ESCALATED: {result['escalation_reason']}")
        if result['conversation_closed']:
            print("✓ CONVERSATION CLOSED")
        print()
    
    def create_conversation(self):
        """Create a new conversation instance"""
        return ConversationManager()
    
    def get_system_stats(self):
        """Get statistics about the system"""
        kb_stats = self.kb_agent.get_stats()
        
        return {
            "knowledge_base": kb_stats,
            "categories": Config.CATEGORIES,
            "urgency_levels": Config.URGENCY_LEVELS,
            "model": Config.CLAUDE_MODEL
        }
