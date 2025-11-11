import streamlit as st
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(__file__))

from src.orchestrator import CustomerServiceOrchestrator
from config.config import Config

# Page configuration
st.set_page_config(
    page_title="AI Customer Service Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .customer-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .customer-header {
        color: #1976d2;
    }
    .bot-header {
        color: #424242;
    }
    .escalation-banner {
        background-color: #fff3cd;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .closed-banner {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    with st.spinner("🤖 Initializing AI agents..."):
        st.session_state.orchestrator = CustomerServiceOrchestrator()
        st.session_state.active_conversations = {}
        st.session_state.current_conv_id = None

# Sidebar - Agent Dashboard
with st.sidebar:
    st.header("🎛️ Agent Dashboard")
    
    # System stats
    stats = st.session_state.orchestrator.get_system_stats()
    st.metric("Knowledge Base", f"{stats['knowledge_base']['total_cases']} cases")
    st.metric("Active Chats", len(st.session_state.active_conversations))
    
    st.divider()
    
    # Active conversations list
    st.subheader("💬 Active Conversations")
    
    if st.session_state.active_conversations:
        for conv_id, conv in st.session_state.active_conversations.items():
            # Icons for status
            closed_icon = "🔒" if conv.context.get('closed', False) else ""
            escalation_icon = "⚠️" if conv.context['escalated'] else ""
            urgency = conv.context.get('urgency')
            urgency_color = {
                'low': '🟢',
                'medium': '🟡', 
                'high': '🔴'
            }.get(urgency, '') if urgency else ''
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"{closed_icon} {escalation_icon} {urgency_color} {conv_id}", 
                    key=f"conv_{conv_id}",
                    use_container_width=True
                ):
                    st.session_state.current_conv_id = conv_id
                    st.rerun()
            with col2:
                st.caption(f"{len(conv.messages)//2}msg")
        
        st.divider()
        
        # Show escalated conversations
        escalated = [c for c in st.session_state.active_conversations.values() if c.context['escalated']]
        closed = [c for c in st.session_state.active_conversations.values() if c.context.get('closed', False)]
        
        if escalated:
            st.warning(f"⚠️ {len(escalated)} chat(s) need attention")
        if closed:
            st.info(f"🔒 {len(closed)} conversation(s) closed")
    else:
        st.info("No active conversations")
    
    st.divider()
    
    # New conversation button
    if st.button("➕ New Conversation", type="primary", use_container_width=True):
        new_conv = st.session_state.orchestrator.create_conversation()
        st.session_state.active_conversations[new_conv.conversation_id] = new_conv
        st.session_state.current_conv_id = new_conv.conversation_id
        st.rerun()
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    show_metadata = st.checkbox("Show message metadata", value=False)
    auto_scroll = st.checkbox("Auto-scroll to bottom", value=True)

# Main area
st.title("💬 AI Customer Service Chatbot")
st.caption("Multi-agent system for academic publishing support")

# Create tabs
tab1, tab2 = st.tabs(["🗨️ Chat Interface", "📊 Analytics"])

with tab1:
    # Get current conversation
    if st.session_state.current_conv_id:
        conversation = st.session_state.active_conversations[st.session_state.current_conv_id]
    else:
        # Create first conversation if none exists
        if not st.session_state.active_conversations:
            new_conv = st.session_state.orchestrator.create_conversation()
            st.session_state.active_conversations[new_conv.conversation_id] = new_conv
            st.session_state.current_conv_id = new_conv.conversation_id
            conversation = new_conv
        else:
            # Use first available conversation
            st.session_state.current_conv_id = list(st.session_state.active_conversations.keys())[0]
            conversation = st.session_state.active_conversations[st.session_state.current_conv_id]
    
    # Conversation header
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.subheader(f"Conversation: {conversation.conversation_id}")
    with col2:
        if conversation.context.get('manuscript_id'):
            st.caption(f"📄 {conversation.context['manuscript_id']}")
    with col3:
        if conversation.context.get('category'):
            st.caption(f"🏷️ {conversation.context['category'].replace('_', ' ').title()}")
    with col4:
        urgency = conversation.context.get('urgency')
        if urgency:
            urgency_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(urgency, '⚪')
            st.caption(f"{urgency_emoji} {urgency.title()}")
        else:
            st.caption("⚪ Unknown")
    
    # Check if conversation is closed
    if conversation.context.get('closed', False):
        st.markdown(f"""
        <div class="closed-banner">
            <strong>🔒 THIS CONVERSATION HAS BEEN CLOSED</strong><br>
            <small>This conversation has ended. Please start a new conversation for additional questions.</small>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➕ Start New Conversation", type="primary", use_container_width=True, key="new_conv_closed"):
                new_conv = st.session_state.orchestrator.create_conversation()
                st.session_state.active_conversations[new_conv.conversation_id] = new_conv
                st.session_state.current_conv_id = new_conv.conversation_id
                st.rerun()
        
        # Show chat history but disable input
        st.divider()
        
        chat_container = st.container()
        
        with chat_container:
            if conversation.messages:
                for msg in conversation.messages:
                    if msg['role'] == 'customer':
                        st.markdown(f"""
                        <div class="chat-message customer-message">
                            <div class="message-header customer-header">👤 Customer</div>
                            <div>{msg['content']}</div>
                            {f"<small style='color: #666;'>{msg['timestamp']}</small>" if show_metadata else ""}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        metadata_html = ""
                        if show_metadata and 'metadata' in msg:
                            meta = msg['metadata']
                            if 'confidence' in meta:
                                metadata_html = f"<small style='color: #666;'>Confidence: {meta['confidence']:.0%}</small>"
                        
                        st.markdown(f"""
                        <div class="chat-message bot-message">
                            <div class="message-header bot-header">🤖 Support Bot</div>
                            <div>{msg['content']}</div>
                            {metadata_html}
                        </div>
                        """, unsafe_allow_html=True)
        
        st.stop()  # Prevent further interaction with closed conversation
    
    # Escalation banner (for open conversations)
    if conversation.context['escalated'] and not conversation.context.get('closed', False):
        st.markdown(f"""
        <div class="escalation-banner">
            <strong>⚠️ ESCALATED TO HUMAN AGENT</strong><br>
            <small>Reason: {conversation.context['escalation_reason']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Chat history display
    chat_container = st.container()
    
    with chat_container:
        if conversation.messages:
            for msg in conversation.messages:
                if msg['role'] == 'customer':
                    st.markdown(f"""
                    <div class="chat-message customer-message">
                        <div class="message-header customer-header">👤 Customer</div>
                        <div>{msg['content']}</div>
                        {f"<small style='color: #666;'>{msg['timestamp']}</small>" if show_metadata else ""}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    metadata_html = ""
                    if show_metadata and 'metadata' in msg:
                        meta = msg['metadata']
                        if 'confidence' in meta:
                            metadata_html = f"<small style='color: #666;'>Confidence: {meta['confidence']:.0%} | Similar cases: {meta.get('similar_cases_count', 0)}</small>"
                    
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <div class="message-header bot-header">🤖 Support Bot</div>
                        <div>{msg['content']}</div>
                        {metadata_html}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👋 Welcome! How can I help you today?")
    
    st.divider()
    
    # Example queries (shown only at start of conversation)
    if len(conversation.messages) == 0:
        st.caption("💡 Try these example queries:")
        example_cols = st.columns(3)
        examples = [
            "What's the status of my manuscript MS-2024-1234?",
            "My review for MS-2024-8903 has been taking over 8 weeks",
            "I need to submit revisions for MS-2024-1005"
        ]
        for idx, (col, example) in enumerate(zip(example_cols, examples)):
            with col:
                if st.button(example, key=f"example_{idx}", use_container_width=True):
                    with st.spinner("🤖 Processing..."):
                        result = st.session_state.orchestrator.process_message(
                            example,
                            conversation,
                            verbose=False
                        )
                    st.rerun()
    
    # Input area
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message...",
            key=f"input_{conversation.conversation_id}",
            placeholder="Ask about manuscript status, delays, revisions...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send 📤", type="primary", use_container_width=True)
    
    # Process message
    if send_button and user_input and user_input.strip():
        with st.spinner("🤖 Processing..."):
            result = st.session_state.orchestrator.process_message(
                user_input,
                conversation,
                verbose=False
            )
        st.rerun()
    
    # Agent actions panel (shown when escalated)
    if conversation.context['escalated'] and not conversation.context.get('closed', False):
        with st.expander("🎯 Agent Actions & Context", expanded=True):
            summary = conversation.get_escalation_summary()
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Conversation Details:**")
                st.write(f"• Messages: {summary['message_count']}")
                st.write(f"• Category: {summary['category']}")
                st.write(f"• Manuscript: {summary['manuscript_id']}")
                st.write(f"• Started: {summary['created_at'][:19]}")
            
            with col2:
                st.markdown("**Escalation Info:**")
                st.write(f"• Reason: {summary['escalation_reason']}")
                st.write(f"• Urgency: {summary['urgency']}")
                st.write(f"• Last update: {summary['last_updated'][:19]}")
            
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Take Over Chat", key="takeover", use_container_width=True):
                    st.success("Chat transferred to human agent")
            with col2:
                if st.button("🔄 Return to Bot", key="return", use_container_width=True):
                    conversation.context['escalated'] = False
                    st.rerun()
            with col3:
                if st.button("✓ Resolve & Close", key="resolve", use_container_width=True):
                    conversation.context['closed'] = True
                    st.rerun()

with tab2:
    st.subheader("📊 System Analytics")
    
    if st.session_state.active_conversations:
        all_convs = list(st.session_state.active_conversations.values())
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_messages = sum(len(c.messages) for c in all_convs)
            st.metric("Total Messages", total_messages)
        
        with col2:
            escalated_count = sum(1 for c in all_convs if c.context['escalated'])
            st.metric("Escalated Chats", escalated_count)
        
        with col3:
            closed_count = sum(1 for c in all_convs if c.context.get('closed', False))
            st.metric("Closed Chats", closed_count)
        
        with col4:
            avg_messages = total_messages / len(all_convs) if all_convs else 0
            st.metric("Avg Messages/Chat", f"{avg_messages:.1f}")
        
        st.divider()
        
        # Category breakdown
        st.subheader("📁 Category Distribution")
        categories = {}
        for conv in all_convs:
            cat = conv.context.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            import pandas as pd
            cat_df = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
            cat_df['Category'] = cat_df['Category'].str.replace('_', ' ').str.title()
            st.bar_chart(cat_df.set_index('Category'))
        
        st.divider()
        
        # Recent conversations
        st.subheader("🕐 Recent Activity")
        for conv in sorted(all_convs, key=lambda x: x.last_updated, reverse=True)[:5]:
            status_text = "🔒 Closed" if conv.context.get('closed', False) else ('⚠️ Escalated' if conv.context['escalated'] else '✅ Active')
            
            with st.expander(f"{conv.conversation_id} - {len(conv.messages)//2} exchanges - {status_text}"):
                st.write(f"**Status:** {status_text}")
                st.write(f"**Category:** {conv.context.get('category', 'N/A')}")
                st.write(f"**Manuscript:** {conv.context.get('manuscript_id', 'N/A')}")
                st.write(f"**Last updated:** {conv.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if conv.context.get('closed', False):
                    st.write(f"**Closed:** Yes")
    else:
        st.info("No conversation data yet. Start chatting to see analytics!")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>AI Customer Service Chatbot v2.0 | Powered by Claude Sonnet 4.5 + OpenAI Embeddings</small>
</div>
""", unsafe_allow_html=True)
