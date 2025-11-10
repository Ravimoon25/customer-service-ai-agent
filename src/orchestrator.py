import sys
sys.path.append('..')

from src.agents.triage_agent import TriageAgent
from src.agents.kb_agent import KnowledgeBaseAgent
from src.agents.response_agent import ResponseAgent
from config.config import Config
import time


class CustomerServiceOrchestrator:
    """
    Orchestrator: Coordinates all agents to process customer queries
    """
    
    def __init__(self):
        """Initialize all agents"""
        print("Initializing Customer Service Agent System...")
        self.triage_agent = TriageAgent()
        self.kb_agent = KnowledgeBaseAgent()
        self.response_agent = ResponseAgent()
        print("✓ All agents initialized\n")
    
    def process_query(self, customer_query, verbose=True):
        """
        Process a customer query through the complete pipeline
        
        Args:
            customer_query: Customer's question/complaint
            verbose: Print step-by-step progress
        
        Returns:
            Dict with complete results
        """
        start_time = time.time()
        
        if verbose:
            print("=" * 70)
            print("PROCESSING CUSTOMER QUERY")
            print("=" * 70)
            print(f"Query: {customer_query}\n")
        
        # Step 1: Triage and Classification
        if verbose:
            print("STEP 1: Triage Agent - Classifying query...")
        
        triage_result = self.triage_agent.classify(customer_query)
        
        if verbose:
            print(f"  ✓ Category: {triage_result['category']}")
            print(f"  ✓ Urgency: {triage_result['urgency']}")
            print(f"  ✓ Manuscript ID: {triage_result.get('manuscript_id', 'N/A')}")
            print(f"  ✓ Summary: {triage_result['issue_summary']}\n")
        
        # Step 2: Knowledge Base Search
        if verbose:
            print("STEP 2: Knowledge Base Agent - Searching similar cases...")
        
        kb_results = self.kb_agent.search(
            customer_query,
            category=triage_result['category'],
            top_k=3
        )
        
        if verbose:
            print(f"  ✓ Found {len(kb_results)} similar cases")
            if kb_results:
                for idx, case in enumerate(kb_results, 1):
                    print(f"    {idx}. {case['id']} (relevance: {case['relevance_score']:.2f})")
            print()
        
        # Step 3: Generate Response
        if verbose:
            print("STEP 3: Response Agent - Generating personalized response...")
        
        response, confidence, should_escalate = self.response_agent.generate_with_confidence(
            customer_query,
            triage_result,
            kb_results
        )
        
        if verbose:
            print(f"  ✓ Response generated")
            print(f"  ✓ Confidence: {confidence:.2f}")
            print(f"  ✓ Escalation needed: {should_escalate}\n")
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        # Compile complete result
        result = {
            "query": customer_query,
            "triage": triage_result,
            "similar_cases": kb_results,
            "response": response,
            "confidence_score": confidence,
            "should_escalate": should_escalate,
            "processing_time_seconds": round(processing_time, 2)
        }
        
        if verbose:
            print("=" * 70)
            print("GENERATED RESPONSE")
            print("=" * 70)
            print(response)
            print("=" * 70)
            print(f"\n⏱️  Total processing time: {processing_time:.2f} seconds")
            if should_escalate:
                print("⚠️  RECOMMENDATION: Escalate to human agent")
            print()
        
        return result
    
    def batch_process(self, queries):
        """
        Process multiple queries
        
        Args:
            queries: List of customer queries
        
        Returns:
            List of result dicts
        """
        results = []
        
        print(f"\nProcessing {len(queries)} queries...\n")
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{'='*70}")
            print(f"Query {idx}/{len(queries)}")
            print(f"{'='*70}")
            
            result = self.process_query(query, verbose=True)
            results.append(result)
        
        # Summary statistics
        print("\n" + "="*70)
        print("BATCH PROCESSING SUMMARY")
        print("="*70)
        print(f"Total queries processed: {len(results)}")
        print(f"Average confidence: {sum(r['confidence_score'] for r in results)/len(results):.2f}")
        print(f"Escalations needed: {sum(1 for r in results if r['should_escalate'])}")
        print(f"Total time: {sum(r['processing_time_seconds'] for r in results):.2f}s")
        
        return results
    
    def get_system_stats(self):
        """
        Get statistics about the system
        
        Returns:
            Dict with system stats
        """
        kb_stats = self.kb_agent.get_stats()
        
        return {
            "knowledge_base": kb_stats,
            "categories": Config.CATEGORIES,
            "urgency_levels": Config.URGENCY_LEVELS,
            "model": Config.CLAUDE_MODEL
        }


# Test the orchestrator if run directly
if __name__ == "__main__":
    orchestrator = CustomerServiceOrchestrator()
    
    # Test single query
    test_query = "I submitted my manuscript MS-2024-1234 three weeks ago. Can you tell me the status?"
    
    result = orchestrator.process_query(test_query)
    
    print("\n" + "="*70)
    print("RESULT SUMMARY")
    print("="*70)
    print(f"Category: {result['triage']['category']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Escalate: {result['should_escalate']}")
