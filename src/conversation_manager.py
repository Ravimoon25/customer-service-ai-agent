import sys
sys.path.append('..')

from datetime import datetime
import json


class ConversationManager:
    """
    Manages conversation state and history for multi-turn dialogues
    """
    
    def __init__(self, conversation_id=None):
        self.conversation_id = conversation_id or self._generate_id()
        self.messages = []
        self.context = {
            'manuscript_id': None,
            'category': None,
            'urgency': None,
            'customer_name': None,
            'escalated': False,
            'escalation_reason': None
        }
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_message(self, role, content, metadata=None):
        """
        Add a message to conversation history
        
        Args:
            role: 'customer' or 'bot'
            content: Message text
            metadata: Optional dict with triage info, confidence, etc.
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.messages.append(message)
        self.last_updated = datetime.now()
    
    def update_context(self, **kwargs):
        """
        Update conversation context with extracted information
        
        Args:
            **kwargs: Key-value pairs to update (manuscript_id, category, etc.)
        """
        for key, value in kwargs.items():
            if key in self.context and value is not None:
                self.context[key] = value
        self.last_updated = datetime.now()
    
    def get_conversation_history(self, max_messages=10):
        """
        Get recent conversation history
        
        Args:
            max_messages: Number of recent messages to return
        
        Returns:
            List of recent messages
        """
        return self.messages[-max_messages:]
    
    def get_context_string(self):
        """
        Format conversation context as a string for LLM prompts
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if self.context['manuscript_id']:
            context_parts.append(f"Manuscript ID: {self.context['manuscript_id']}")
        
        if self.context['category']:
            context_parts.append(f"Issue Category: {self.context['category']}")
        
        if self.context['urgency']:
            context_parts.append(f"Urgency Level: {self.context['urgency']}")
        
        if self.context['customer_name']:
            context_parts.append(f"Customer Name: {self.context['customer_name']}")
        
        # Add conversation history
        if self.messages:
            context_parts.append("\nConversation History:")
            for msg in self.get_conversation_history(5):
                role_label = "Customer" if msg['role'] == 'customer' else "Bot"
                context_parts.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(context_parts) if context_parts else "No prior context"
    
    def should_escalate(self):
        """
        Determine if conversation should be escalated
        
        Returns:
            Boolean
        """
        # Already escalated
        if self.context['escalated']:
            return True
        
        # High urgency with multiple messages
        if self.context['urgency'] == 'high' and len(self.messages) > 2:
            return True
        
        # Customer frustration indicators
        frustrated_keywords = ['unacceptable', 'ridiculous', 'angry', 'complaint', 
                               'manager', 'escalate', 'disappointed']
        recent_messages = self.get_conversation_history(3)
        for msg in recent_messages:
            if msg['role'] == 'customer':
                content_lower = msg['content'].lower()
                if any(keyword in content_lower for keyword in frustrated_keywords):
                    return True
        
        return False
    
    def mark_escalated(self, reason):
        """
        Mark conversation as escalated to human agent
        
        Args:
            reason: Reason for escalation
        """
        self.context['escalated'] = True
        self.context['escalation_reason'] = reason
        self.last_updated = datetime.now()
    
    def get_escalation_summary(self):
        """
        Get summary for human agent handoff
        
        Returns:
            Dict with escalation details
        """
        return {
            'conversation_id': self.conversation_id,
            'manuscript_id': self.context['manuscript_id'],
            'category': self.context['category'],
            'urgency': self.context['urgency'],
            'escalation_reason': self.context['escalation_reason'],
            'message_count': len(self.messages),
            'conversation_history': self.get_conversation_history(),
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    def to_dict(self):
        """
        Serialize conversation to dictionary
        
        Returns:
            Dict representation
        """
        return {
            'conversation_id': self.conversation_id,
            'messages': self.messages,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @staticmethod
    def _generate_id():
        """Generate unique conversation ID"""
        import uuid
        return f"CONV_{uuid.uuid4().hex[:8].upper()}"


# Test the conversation manager
if __name__ == "__main__":
    conv = ConversationManager()
    
    print(f"Conversation ID: {conv.conversation_id}\n")
    
    # Simulate conversation
    conv.add_message('customer', 'What is the status of my manuscript MS-2024-1234?')
    conv.update_context(manuscript_id='MS-2024-1234', category='status_inquiry', urgency='medium')
    
    conv.add_message('bot', 'Your manuscript MS-2024-1234 is currently under review...')
    
    conv.add_message('customer', 'This is taking too long! I need an update now!')
    conv.update_context(urgency='high')
    
    print("Conversation Context:")
    print(conv.get_context_string())
    print(f"\nShould Escalate: {conv.should_escalate()}")
    
    if conv.should_escalate():
        conv.mark_escalated("Customer frustration + high urgency")
        print("\nEscalation Summary:")
        print(json.dumps(conv.get_escalation_summary(), indent=2))
