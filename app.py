import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(__file__))

from src.orchestrator import CustomerServiceOrchestrator
from config.config import Config
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="AI Customer Service Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    with st.spinner("Initializing AI agents..."):
        st.session_state.orchestrator = CustomerServiceOrchestrator()
        st.session_state.history = []

# Title
st.markdown('<p class="main-header">🤖 AI Customer Service Agent System</p>', unsafe_allow_html=True)
st.markdown("### Multi-Agent System for Academic Publishing Support")

# Sidebar
with st.sidebar:
    st.header("📊 System Information")
    
    # Get system stats
    stats = st.session_state.orchestrator.get_system_stats()
    
    st.metric("Knowledge Base Cases", stats['knowledge_base']['total_cases'])
    st.metric("Categories", len(stats['categories']))
    st.metric("Model", "Claude Sonnet 4.5")
    
    st.divider()
    
    st.subheader("📁 Categories")
    for cat in stats['categories']:
        st.text(f"• {cat.replace('_', ' ').title()}")
    
    st.divider()
    
    st.subheader("⚙️ Settings")
    show_details = st.checkbox("Show detailed processing", value=True)
    show_kb_results = st.checkbox("Show similar cases", value=True)
    
    st.divider()
    
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()

# Main area - tabs
tab1, tab2, tab3 = st.tabs(["💬 Query Processor", "📜 Query History", "ℹ️ About"])

with tab1:
    st.subheader("Enter Customer Query")
    
    # Example queries
    example_queries = [
        "I submitted my manuscript MS-2024-1234 three weeks ago. What's the status?",
        "My manuscript MS-2024-5678 has been in review for 10 weeks. This is taking too long!",
        "I received a revise and resubmit decision for MS-2024-9012. How long do I have?",
        "I want to withdraw my manuscript MS-2024-3456 and submit it elsewhere.",
        "Can I get an extension for submitting revisions? Manuscript MS-2024-7890."
    ]
    
    selected_example = st.selectbox(
        "Or select an example query:",
        [""] + example_queries,
        index=0
    )
    
    # Query input
    if selected_example:
        query_input = st.text_area(
            "Customer Query:",
            value=selected_example,
            height=100,
            key="query_input"
        )
    else:
        query_input = st.text_area(
            "Customer Query:",
            placeholder="Enter customer question here...",
            height=100,
            key="query_input"
        )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        process_button = st.button("🚀 Process Query", type="primary", use_container_width=True)
    
    if process_button and query_input.strip():
        with st.spinner("Processing query through AI agents..."):
            # Process the query
            result = st.session_state.orchestrator.process_query(
                query_input,
                verbose=False
            )
            
            # Add to history
            st.session_state.history.append(result)
        
        st.success("✅ Query processed successfully!")
        
        # Display results
        st.divider()
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Category", result['triage']['category'].replace('_', ' ').title())
        
        with col2:
            urgency = result['triage']['urgency']
            urgency_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            st.metric("Urgency", f"{urgency_color.get(urgency, '')} {urgency.title()}")
        
        with col3:
            confidence = result['confidence_score']
            st.metric("Confidence", f"{confidence:.0%}")
        
        with col4:
            st.metric("Processing Time", f"{result['processing_time_seconds']:.2f}s")
        
        st.divider()
        
        # Show detailed processing if enabled
        if show_details:
            with st.expander("🔍 Detailed Classification", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Extracted Information:**")
                    st.write(f"• Manuscript ID: `{result['triage'].get('manuscript_id', 'N/A')}`")
                    st.write(f"• Issue Summary: {result['triage']['issue_summary']}")
                
                with col2:
                    st.write("**Agent Analysis:**")
                    st.write(f"• Similar cases found: {len(result['similar_cases'])}")
                    st.write(f"• Should escalate: {'Yes ⚠️' if result['should_escalate'] else 'No ✅'}")
        
        # Show similar cases if enabled
        if show_kb_results and result['similar_cases']:
            with st.expander("📚 Similar Past Cases", expanded=False):
                for idx, case in enumerate(result['similar_cases'], 1):
                    st.write(f"**Case {idx}: {case['id']}** (Relevance: {case['relevance_score']:.0%})")
                    st.write(f"*Query:* {case['query']}")
                    st.write(f"*Resolution:* {case['resolution']}")
                    st.divider()
        
        # Generated response
        st.subheader("📝 Generated Response")
        
        if result['should_escalate']:
            st.warning("⚠️ **Recommendation:** This query should be escalated to a human agent for review.")
        
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4;">
        {result['response']}
        </div>
        """, unsafe_allow_html=True)
        
    elif process_button:
        st.warning("⚠️ Please enter a customer query.")

with tab2:
    st.subheader("Query History")
    
    if st.session_state.history:
        st.write(f"Total queries processed: **{len(st.session_state.history)}**")
        
        # Summary statistics
        avg_confidence = sum(h['confidence_score'] for h in st.session_state.history) / len(st.session_state.history)
        escalations = sum(1 for h in st.session_state.history if h['should_escalate'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Confidence", f"{avg_confidence:.0%}")
        with col2:
            st.metric("Total Escalations", escalations)
        with col3:
            st.metric("Success Rate", f"{(1 - escalations/len(st.session_state.history)):.0%}")
        
        st.divider()
        
        # Display history in reverse order (newest first)
        for idx, item in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"Query {len(st.session_state.history) - idx + 1}: {item['query'][:60]}..."):
                st.write(f"**Category:** {item['triage']['category']}")
                st.write(f"**Urgency:** {item['triage']['urgency']}")
                st.write(f"**Confidence:** {item['confidence_score']:.0%}")
                st.write(f"**Manuscript ID:** {item['triage'].get('manuscript_id', 'N/A')}")
                st.divider()
                st.write("**Response:**")
                st.write(item['response'])
    else:
        st.info("No queries processed yet. Go to the Query Processor tab to get started!")

with tab3:
    st.subheader("About This System")
    
    st.markdown("""
    ### 🎯 Overview
    This is a **Multi-Agent AI System** for automating customer service responses in academic publishing workflows.
    
    ### 🏗️ Architecture
    The system uses three specialized AI agents:
    
    1. **🎯 Triage Agent**
       - Classifies incoming queries into categories
       - Extracts key information (manuscript ID, urgency)
       - Determines priority level
    
    2. **📚 Knowledge Base Agent**
       - Searches through historical resolved cases
       - Finds similar past queries and solutions
       - Ranks results by relevance
    
    3. **✍️ Response Generator Agent**
       - Creates personalized, empathetic responses
       - Adapts tone based on urgency
       - Incorporates solutions from similar cases
    
    ### 🔧 Technology Stack
    - **LLM:** Anthropic Claude Sonnet 4.5
    - **Framework:** Streamlit
    - **Data:** Synthetic OSVC-style customer service data
    - **Language:** Python 3.9+
    
    ### 📊 Use Case
    Handles manuscript status inquiries including:
    - Status updates
    - Review delays
    - Decision timelines
    - Revision submissions
    - Withdrawal requests
    
    ### 👤 Built by
    Ravi - Senior Data Scientist specializing in AI automation for customer experience analytics
    """)
    
    st.divider()
    
    st.subheader("📈 Knowledge Base Statistics")
    kb_stats = stats['knowledge_base']
    
    if kb_stats['total_cases'] > 0:
        # Category distribution
        st.write("**Category Distribution:**")
        cat_df = pd.DataFrame(
            list(kb_stats['categories'].items()),
            columns=['Category', 'Count']
        )
        cat_df['Category'] = cat_df['Category'].str.replace('_', ' ').str.title()
        st.bar_chart(cat_df.set_index('Category'))

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>AI Customer Service Agent System v1.0 | Powered by Claude Sonnet 4.5</small>
</div>
""", unsafe_allow_html=True)
