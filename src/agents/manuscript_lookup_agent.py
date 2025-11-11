import pandas as pd
from config.config import Config
import os

class ManuscriptLookupAgent:
    """
    Agent to look up REAL manuscript status from database
    """
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(Config.DATA_DIR, "manuscript_status_db.csv")
        
        try:
            self.db = pd.read_csv(db_path)
            print(f"✓ Loaded manuscript database: {len(self.db)} manuscripts")
        except FileNotFoundError:
            print(f"⚠ Manuscript database not found at {db_path}")
            self.db = pd.DataFrame()
    
    def lookup(self, manuscript_id):
        """
        Look up manuscript by ID
        
        Returns:
            Dict with manuscript details or None if not found
        """
        if self.db.empty or not manuscript_id:
            return None
        
        result = self.db[self.db['manuscript_id'] == manuscript_id]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def exists(self, manuscript_id):
        """Check if manuscript exists"""
        return self.lookup(manuscript_id) is not None
