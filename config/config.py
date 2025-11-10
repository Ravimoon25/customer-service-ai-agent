import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the customer service agent system"""
    
    # Claude API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    
    # Agent Configuration
    MAX_TOKENS = 2000
    TEMPERATURE = 0.3  # Lower for consistent outputs
    
    # Paths
    DATA_DIR = "data"
    SYNTHETIC_DATA_PATH = os.path.join(DATA_DIR, "synthetic_data.csv")
    
    # Thresholds
    ESCALATION_THRESHOLD = 0.5  # Below this confidence, escalate to human
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    
    # Agent Categories
    CATEGORIES = [
        "status_inquiry",
        "review_delay", 
        "decision_timeline",
        "revision_submission",
        "withdrawal_request"
    ]
    
    URGENCY_LEVELS = ["low", "medium", "high"]
    
    @staticmethod
    def validate():
        """Validate that required configuration is present"""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Please create a .env file with your API key."
            )
        
        os.makedirs(Config.DATA_DIR, exist_ok=True)

# Validate configuration on import
Config.validate()
