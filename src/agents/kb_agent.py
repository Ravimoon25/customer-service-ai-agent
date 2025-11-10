import sys
sys.path.append('../..')

import pandas as pd
import numpy as np
from openai import OpenAI
from config.config import Config
import pickle
import os


class KnowledgeBaseAgent:
    """
    Knowledge Base Agent: Searches for similar past cases using OpenAI embeddings
    """
    
    def __init__(self, data_path=None):
        """
        Initialize with synthetic data and embeddings
        
        Args:
            data_path: Path to CSV file with historical cases
        """
        if data_path is None:
            data_path = Config.SYNTHETIC_DATA_PATH
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        try:
            self.data = pd.read_csv(data_path)
            print(f"✓ Loaded {len(self.data)} cases from knowledge base")
            
            # Check if embeddings exist, otherwise create them
            self.embeddings_path = data_path.replace('.csv', '_embeddings.pkl')
            if os.path.exists(self.embeddings_path):
                self._load_embeddings()
            else:
                print("  Creating embeddings... (this may take a moment)")
                self._create_embeddings()
                
        except FileNotFoundError:
            print(f"⚠ Warning: Data file not found at {data_path}")
            self.data = pd.DataFrame()
            self.embeddings = None
    
    def _create_embeddings(self):
        """Generate embeddings for all cases using OpenAI"""
        queries = self.data['query'].tolist()
        
        # Generate embeddings in batch
        self.embeddings = []
        batch_size = 100  # Process 100 at a time
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            response = self.client.embeddings.create(
                model=Config.EMBEDDING_MODEL,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            self.embeddings.extend(batch_embeddings)
        
        self.embeddings = np.array(self.embeddings)
        
        # Save embeddings for future use
        with open(self.embeddings_path, 'wb') as f:
            pickle.dump(self.embeddings, f)
        
        print(f"  ✓ Created and saved embeddings ({self.embeddings.shape})")
    
    def _load_embeddings(self):
        """Load pre-computed embeddings"""
        with open(self.embeddings_path, 'rb') as f:
            self.embeddings = pickle.load(f)
        print(f"  ✓ Loaded pre-computed embeddings ({self.embeddings.shape})")
    
    def search(self, query, category=None, top_k=3):
        """
        Search for similar cases using semantic similarity
        
        Args:
            query: Customer query text
            category: Category from triage (optional filter)
            top_k: Number of results to return
        
        Returns:
            List of similar cases (dicts)
        """
        if self.data.empty or self.embeddings is None:
            return []
        
        # Generate embedding for query
        query_response = self.client.embeddings.create(
            model=Config.EMBEDDING_MODEL,
            input=[query]
        )
        query_embedding = np.array(query_response.data[0].embedding)
        
        # Filter by category if provided
        if category and category in Config.CATEGORIES:
            mask = self.data['category'] == category
            filtered_indices = self.data[mask].index.tolist()
            
            if not filtered_indices:
                # No cases in this category, search all
                filtered_indices = list(range(len(self.data)))
                filtered_embeddings = self.embeddings
            else:
                filtered_embeddings = self.embeddings[filtered_indices]
        else:
            filtered_indices = list(range(len(self.data)))
            filtered_embeddings = self.embeddings
        
        # Calculate cosine similarity
        similarities = self._cosine_similarity(query_embedding, filtered_embeddings)
        
        # Get top_k most similar
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Map back to original indices
        original_indices = [filtered_indices[i] for i in top_indices]
        
        # Convert to list of dicts
        results = []
        for idx, sim_score in zip(original_indices, similarities[top_indices]):
            row = self.data.iloc[idx]
            results.append({
                'id': row.get('id', 'N/A'),
                'category': row['category'],
                'urgency': row['urgency'],
                'manuscript_id': row.get('manuscript_id', 'N/A'),
                'query': row['query'],
                'resolution': row['resolution'],
                'tags': row.get('tags', ''),
                'relevance_score': float(sim_score)
            })
        
        return results
    
    def _cosine_similarity(self, query_embedding, embeddings):
        """
        Calculate cosine similarity between query and all embeddings
        
        Args:
            query_embedding: Single embedding vector
            embeddings: Matrix of embeddings
        
        Returns:
            Array of similarity scores
        """
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Compute cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities
    
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
            "urgency_distribution": self.data['urgency'].value_counts().to_dict(),
            "embeddings_ready": self.embeddings is not None
        }


# Test the agent if run directly
if __name__ == "__main__":
    agent = KnowledgeBaseAgent()
    
    print("\nKnowledge Base Statistics:")
    stats = agent.get_stats()
    print(f"  Total Cases: {stats['total_cases']}")
    print(f"  Embeddings Ready: {stats['embeddings_ready']}")
    print(f"  Categories: {stats['categories']}")
    
    # Test semantic search
    test_query = "My paper has been waiting for reviewers for a very long time"
    category = "review_delay"
    
    print(f"\nSearching for: '{test_query}'")
    print(f"Category filter: {category}\n")
    
    results = agent.search(test_query, category=category, top_k=3)
    
    print(f"Found {len(results)} similar cases:\n")
    for idx, case in enumerate(results, 1):
        print(f"{idx}. {case['id']} (similarity: {case['relevance_score']:.3f})")
        print(f"   Query: {case['query'][:80]}...")
        print(f"   Resolution: {case['resolution'][:100]}...\n")
