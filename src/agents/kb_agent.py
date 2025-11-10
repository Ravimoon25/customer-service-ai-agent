import sys
sys.path.append('../..')

import pandas as pd
from config.config import Config


class KnowledgeBaseAgent:
    """
    Knowledge Base Agent: Searches for similar past cases
    """
    
    def __init__(self, data_path=None):
        """
        Initialize with synthetic data
        
        Args:
            data_path: Path to CSV file with historical cases
        """
        if data_path is None:
            data_path = Config.SYNTHETIC_DATA_PATH
        
        try:
            self.data = pd.read_csv(data_path)
            print(f"✓ Loaded {len(self.data)} cases from knowledge base")
        except FileNotFoundError:
            print(f"⚠ Warning: Data file not found at {data_path}")
            self.data = pd.DataFrame()
    
    def search(self, query, category=None, top_k=3):
        """
        Search for similar cases in knowledge base
        
        Args:
            query: Customer query text
            category: Category from triage (optional filter)
            top_k: Number of results to return
        
        Returns:
            List of similar cases (dicts)
        """
        if self.data.empty:
            return []
        
        # Filter by category if provided
        if category and category in Config.CATEGORIES:
            filtered_data = self.data[self.data['category'] == category]
        else:
            filtered_data = self.data
        
        if filtered_data.empty:
            return []
        
        # Simple keyword matching (for POC - in production use embeddings)
        query_lower = query.lower()
        
        # Score each case based on keyword overlap
        filtered_data = filtered_data.copy()
        filtered_data['relevance_score'] = filtered_data['query'].apply(
            lambda x: self._calculate_relevance(query_lower, str(x).lower())
        )
        
        # Sort by relevance and return top_k
        top_cases = filtered_data.nlargest(top_k, 'relevance_score')
        
        # Convert to list of dicts
        results = []
        for _, row in top_cases.iterrows():
            results.append({
                'id': row.get('id', 'N/A'),
                'category': row['category'],
                'urgency': row['urgency'],
                'manuscript_id': row.get('manuscript_id', 'N/A'),
                'query': row['query'],
                'resolution': row['resolution'],
                'tags': row.get('tags', ''),
                'relevance_score': row['relevance_score']
            })
        
        return results
    
    def _calculate_relevance(self, query, case_query):
        """
        Calculate simple keyword-based relevance score
        
        Args:
            query: User's query (lowercase)
            case_query: Historical case query (lowercase)
        
        Returns:
            Float relevance score
        """
        # Split into words
        query_words = set(query.split())
        case_words = set(case_query.split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                     'i', 'my', 'me', 'you', 'your', 'it', 'its', 'this', 'that'}
        
        query_words = query_words - stop_words
        case_words = case_words - stop_words
        
        if not query_words or not case_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words & case_words)
        union = len(query_words | case_words)
        
        return intersection / union if union > 0 else 0.0
    
    def get_case_by_id(self, case_id):
        """
        Retrieve specific case by ID
        
        Args:
            case_id: Case identifier
        
        Returns:
            Case dict or None
        """
        if self.data.empty:
            return None
        
        case = self.data[self.data['id'] == case_id]
        if case.empty:
            return None
        
        return case.iloc[0].to_dict()
    
    def get_stats(self):
        """
        Get knowledge base statistics
        
        Returns:
            Dict with stats
        """
        if self.data.empty:
            return {"total_cases": 0, "categories": {}}
        
        return {
            "total_cases": len(self.data),
            "categories": self.data['category'].value_counts().to_dict(),
            "urgency_distribution": self.data['urgency'].value_counts().to_dict()
        }


# Test the agent if run directly
if __name__ == "__main__":
    agent = KnowledgeBaseAgent()
    
    print("\nKnowledge Base Statistics:")
    stats = agent.get_stats()
    print(f"  Total Cases: {stats['total_cases']}")
    print(f"  Categories: {stats['categories']}")
    
    # Test search
    test_query = "My manuscript has been in review for 8 weeks"
    category = "review_delay"
    
    print(f"\nSearching for: '{test_query}'")
    print(f"Category filter: {category}\n")
    
    results = agent.search(test_query, category=category, top_k=2)
    
    print(f"Found {len(results)} similar cases:\n")
    for idx, case in enumerate(results, 1):
        print(f"{idx}. {case['id']} (relevance: {case['relevance_score']:.2f})")
        print(f"   Query: {case['query'][:80]}...")
        print(f"   Resolution: {case['resolution'][:100]}...\n")
