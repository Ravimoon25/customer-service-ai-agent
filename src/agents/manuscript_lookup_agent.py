import sys
sys.path.append('../..')

import pandas as pd
from config.config import Config
import os


class ManuscriptLookupAgent:
    """
    Manuscript Lookup Agent: Retrieves REAL manuscript status from database
    """
    
    def __init__(self, db_path=None):
        """
        Initialize with manuscript status database
        
        Args:
            db_path: Path to manuscript status CSV file
        """
        if db_path is None:
            db_path = os.path.join(Config.DATA_DIR, "manuscript_status_db.csv")
        
        self.db_path = db_path
        
        try:
            self.db = pd.read_csv(db_path)
            print(f"✓ Loaded manuscript database: {len(self.db)} manuscripts")
        except FileNotFoundError:
            print(f"⚠ Warning: Manuscript database not found at {db_path}")
            self.db = pd.DataFrame()
    
    def lookup(self, manuscript_id):
        """
        Look up manuscript by ID
        
        Args:
            manuscript_id: Manuscript identifier (e.g., MS-2024-1234)
        
        Returns:
            Dict with manuscript details or None if not found
        """
        if self.db.empty or not manuscript_id:
            return None
        
        # Case-insensitive search
        result = self.db[self.db['manuscript_id'].str.upper() == manuscript_id.upper()]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def exists(self, manuscript_id):
        """
        Check if manuscript exists in database
        
        Args:
            manuscript_id: Manuscript identifier
        
        Returns:
            Boolean
        """
        return self.lookup(manuscript_id) is not None
    
    def get_by_author(self, author_name):
        """
        Get all manuscripts by author name
        
        Args:
            author_name: Author name (partial match)
        
        Returns:
            List of manuscript dicts
        """
        if self.db.empty:
            return []
        
        results = self.db[self.db['author_name'].str.contains(author_name, case=False, na=False)]
        
        return results.to_dict('records')
    
    def get_by_status(self, status):
        """
        Get all manuscripts with given status
        
        Args:
            status: Current status (e.g., "Under Review")
        
        Returns:
            List of manuscript dicts
        """
        if self.db.empty:
            return []
        
        results = self.db[self.db['current_status'].str.contains(status, case=False, na=False)]
        
        return results.to_dict('records')
    
    def get_stats(self):
        """
        Get database statistics
        
        Returns:
            Dict with stats
        """
        if self.db.empty:
            return {"total_manuscripts": 0, "status_distribution": {}}
        
        return {
            "total_manuscripts": len(self.db),
            "status_distribution": self.db['current_status'].value_counts().to_dict(),
            "average_review_time_days": self._calculate_avg_review_time()
        }
    
    def _calculate_avg_review_time(self):
        """Calculate average time manuscripts spend in review"""
        # Simple placeholder - you can enhance this
        return 45  # days


# Test the agent if run directly
if __name__ == "__main__":
    agent = ManuscriptLookupAgent()
    
    print("\nManuscript Database Statistics:")
    stats = agent.get_stats()
    print(f"  Total Manuscripts: {stats['total_manuscripts']}")
    print(f"  Status Distribution: {stats['status_distribution']}")
    
    # Test lookup
    test_id = "MS-2024-1234"
    print(f"\nLooking up: {test_id}")
    result = agent.lookup(test_id)
    
    if result:
        print(f"  ✓ Found:")
        print(f"    Author: {result['author_name']}")
        print(f"    Status: {result['current_status']}")
        print(f"    Submission: {result['submission_date']}")
    else:
        print(f"  ✗ Not found")
