# 🤖 Customer Service AI Agent System

A multi-agent orchestration system for automating customer service responses in academic publishing workflows.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-purple.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)

## 🎯 Overview

This POC demonstrates an intelligent customer service automation system that uses multiple AI agents to:
- ✅ Classify and triage incoming queries
- ✅ Search knowledge base for relevant solutions
- ✅ Generate personalized, context-aware responses
- ✅ Determine when to escalate to human agents

## 🏗️ Architecture
```
Customer Query
      ↓
Triage Agent (Classification & Entity Extraction)
      ↓
Knowledge Base Agent (Semantic Search)
      ↓
Response Generator (Personalized Reply)
      ↓
Generated Response + Confidence Score
```

## 🔧 Tech Stack

- **LLM**: Anthropic Claude API (Sonnet 4.5)
- **UI**: Streamlit
- **Data**: Synthetic OSVC-style customer service data
- **Language**: Python 3.9+

## 📦 Setup Instructions

### 1. Prerequisites
- Python 3.9 or higher
- Claude API key from [console.anthropic.com](https://console.anthropic.com/)

### 2. Installation

Clone and setup:
```bash
git clone <your-repo-url>
cd customer-service-ai-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Key

Create `.env` file:
```bash
cp .env.template .env
```

Edit `.env` and add your Claude API key:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 4. Generate Synthetic Data

Run the setup script:
```bash
python setup_data.py
```

This will create 31+ customer service cases in `data/synthetic_data.csv`

### 5. Launch the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 🚀 Usage

### Query Processor
1. Enter a customer query or select an example
2. Click "Process Query"
3. View the AI-generated response, classification, and similar cases
4. Check if escalation to human agent is recommended

### Example Queries
- "I submitted my manuscript MS-2024-1234 three weeks ago. What's the status?"
- "My manuscript has been in review for 10 weeks. This is taking too long!"
- "I received a revise and resubmit decision. How long do I have?"

## 📁 Project Structure
```
customer-service-ai-agent/
├── README.md
├── requirements.txt
├── .env.template
├── .gitignore
├── app.py                      # Streamlit UI
├── setup_data.py               # Data generation runner
├── config/
│   └── config.py               # Configuration settings
├── data/
│   └── synthetic_data.csv      # Generated customer service data
├── src/
│   ├── utils.py                # Helper functions
│   ├── orchestrator.py         # Agent coordination
│   └── agents/
│       ├── triage_agent.py     # Classification agent
│       ├── kb_agent.py         # Knowledge base search
│       └── response_agent.py   # Response generation
└── scripts/
    └── generate_data.py        # Synthetic data creation
```

## 🎓 Use Case: Manuscript Status Inquiries

The system handles common academic publishing queries:
- **Status Inquiries**: "What's the status of my manuscript?"
- **Review Delays**: "Why is my review taking so long?"
- **Decision Timelines**: "When will I hear back?"
- **Revision Submissions**: "How do I submit revisions?"
- **Withdrawal Requests**: "I want to withdraw my manuscript"

## 📊 Features

### Triage Agent
- Classifies queries into 5 categories
- Extracts manuscript IDs automatically
- Determines urgency level (low/medium/high)
- Creates issue summaries

### Knowledge Base Agent
- Searches 31+ historical cases
- Keyword-based relevance ranking
- Category filtering
- Returns top-k similar cases

### Response Generator
- Personalized, empathetic responses
- Adapts tone to urgency level
- References similar cases contextually
- Provides confidence scores

### Orchestrator
- Coordinates all agents seamlessly
- Tracks processing metrics
- Determines escalation needs
- Complete audit trail

## 📈 Metrics Tracked

- Classification Accuracy
- Response Confidence Score
- Processing Time
- Escalation Rate
- Category Distribution

## 🔐 Security Notes

- Never commit `.env` file with actual API keys
- API keys are loaded from environment variables
- Use `.env.template` for sharing configuration structure

## 🛠️ Development

### Adding New Categories
Edit `config/config.py`:
```python
CATEGORIES = [
    "your_new_category",
    # existing categories...
]
```

### Adding More Training Data
Edit `scripts/generate_data.py` and add new cases to the respective lists.

## 📝 Future Enhancements

- [ ] Replace keyword search with semantic embeddings (FAISS/Pinecone)
- [ ] Add conversation memory for multi-turn dialogues
- [ ] Implement A/B testing for response quality
- [ ] Add authentication and user management
- [ ] Connect to real OSVC/Salesforce data
- [ ] Deploy to cloud (AWS/Azure/GCP)

## 🤝 Contributing

This is a POC project. Feel free to fork and extend!

## 👤 Author

**Ravi**  
Senior Data Scientist specializing in AI automation for customer experience analytics

## 📄 License

MIT License

---

**Built with ❤️ using Claude Sonnet 4.5**
