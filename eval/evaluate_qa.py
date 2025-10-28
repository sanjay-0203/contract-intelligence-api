"""Q&A Evaluation Script

Tests the Q&A system against a curated dataset of questions and expected answers.

Usage:
    python evaluate_qa.py

Environment variables:
    - OPENAI_API_KEY: Required for LLM operations
    - DATABASE_URL: Database connection string
"""

import os
import sys
import json
import time
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.llm_service import LLMService
from src.services.vector_search import VectorSearchService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def load_eval_dataset(filepath: str = "qa_eval_dataset.json") -> List[Dict[str, Any]]:
    """Load evaluation dataset."""
    dataset_path = Path(__file__).parent / filepath
    with open(dataset_path, 'r') as f:
        return json.load(f)


def evaluate_answer(answer: str, expected_contains: List[str]) -> Dict[str, Any]:
    """
    Evaluate if answer contains expected information.
    
    Returns:
        - score: 0.0 to 1.0 based on how many expected phrases are present
        - matched: List of matched phrases
        - missing: List of missing phrases
    """
    answer_lower = answer.lower()
    matched = []
    missing = []
    
    for phrase in expected_contains:
        if phrase.lower() in answer_lower:
            matched.append(phrase)
        else:
            missing.append(phrase)
    
    score = len(matched) / len(expected_contains) if expected_contains else 1.0
    
    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "answer_length": len(answer)
    }


def run_evaluation(
    dataset: List[Dict[str, Any]],
    document_ids: Dict[str, str]
) -> Dict[str, Any]:
    """
    Run evaluation on all questions.
    
    Args:
        dataset: List of evaluation questions
        document_ids: Mapping of document names to IDs
        
    Returns:
        Evaluation results with metrics
    """
    # Initialize services
    llm = LLMService()
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/contract_intelligence")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    vector_search = VectorSearchService(db)
    
    results = []
    total_score = 0.0
    total_response_time = 0.0
    
    print(f"\nRunning evaluation on {len(dataset)} questions...\n")
    print("=" * 80)
    
    for i, item in enumerate(dataset, 1):
        question = item["question"]
        doc_name = item.get("document_name", "service_agreement.pdf")
        expected = item["expected_answer_contains"]
        
        # Get document ID
        doc_id = document_ids.get(doc_name)
        if not doc_id:
            print(f"⚠️  Q{i}: Skipping - document {doc_name} not found")
            continue
        
        print(f"\nQ{i}/{len(dataset)}: {question}")
        print(f"Document: {doc_name}")
        
        # Generate answer
        start_time = time.time()
        
        try:
            # Get embedding
            question_embedding = llm.create_embedding(question)
            
            # Search for relevant chunks
            chunks = vector_search.search_similar_chunks(
                query_embedding=question_embedding,
                document_ids=[doc_id],
                top_k=5
            )
            
            if not chunks:
                print(f"❌ No relevant chunks found")
                results.append({
                    "question_id": item["id"],
                    "question": question,
                    "score": 0.0,
                    "error": "No relevant chunks found"
                })
                continue
            
            # Generate answer
            context_texts = [c["text"] for c in chunks]
            answer = llm.answer_question(question, context_texts)
            
            response_time = time.time() - start_time
            
            # Evaluate answer
            eval_result = evaluate_answer(answer, expected)
            
            # Store result
            result = {
                "question_id": item["id"],
                "question": question,
                "answer": answer,
                "expected": expected,
                "score": eval_result["score"],
                "matched": eval_result["matched"],
                "missing": eval_result["missing"],
                "response_time_ms": int(response_time * 1000),
                "num_chunks": len(chunks)
            }
            results.append(result)
            
            total_score += eval_result["score"]
            total_response_time += response_time
            
            # Print result
            score_display = "✓" if eval_result["score"] >= 0.5 else "✗"
            print(f"{score_display} Score: {eval_result['score']:.2f} ({response_time*1000:.0f}ms)")
            print(f"Answer: {answer[:150]}...")
            if eval_result["missing"]:
                print(f"Missing: {', '.join(eval_result['missing'])}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "question_id": item["id"],
                "question": question,
                "score": 0.0,
                "error": str(e)
            })
    
    db.close()
    
    # Calculate metrics
    valid_results = [r for r in results if "error" not in r]
    avg_score = total_score / len(valid_results) if valid_results else 0.0
    avg_response_time = total_response_time / len(valid_results) if valid_results else 0.0
    
    high_quality = len([r for r in valid_results if r["score"] >= 0.8])
    medium_quality = len([r for r in valid_results if 0.5 <= r["score"] < 0.8])
    low_quality = len([r for r in valid_results if r["score"] < 0.5])
    
    print("\n" + "=" * 80)
    print("\n📊 EVALUATION SUMMARY")
    print(f"\nOverall Score: {avg_score:.2%}")
    print(f"Average Response Time: {avg_response_time*1000:.0f}ms")
    print(f"\nQuality Distribution:")
    print(f"  High (≥80%): {high_quality}/{len(valid_results)}")
    print(f"  Medium (50-79%): {medium_quality}/{len(valid_results)}")
    print(f"  Low (<50%): {low_quality}/{len(valid_results)}")
    
    if len(results) != len(dataset):
        print(f"\n⚠️  {len(dataset) - len(results)} questions had errors")
    
    return {
        "overall_score": avg_score,
        "avg_response_time_ms": int(avg_response_time * 1000),
        "total_questions": len(dataset),
        "successful_questions": len(valid_results),
        "high_quality_count": high_quality,
        "medium_quality_count": medium_quality,
        "low_quality_count": low_quality,
        "results": results
    }


def main():
    """Main evaluation function."""
    print("Contract Intelligence API - Q&A Evaluation")
    print("=" * 80)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Load dataset
    try:
        dataset = load_eval_dataset()
        print(f"✓ Loaded {len(dataset)} evaluation questions")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        sys.exit(1)
    
    # Note: In a real evaluation, you would:
    # 1. Ingest the test documents first
    # 2. Get their document IDs
    # 3. Pass those IDs to run_evaluation
    
    print("\n⚠️  NOTE: This evaluation requires test documents to be ingested first.")
    print("Please run the following steps:")
    print("1. Start the API: docker-compose up")
    print("2. Ingest test contracts: POST /ingest with example_contracts/*.pdf")
    print("3. Update document_ids mapping in this script")
    print("4. Run evaluation again")
    
    # Placeholder for document IDs (would come from ingestion)
    document_ids = {
        "service_agreement.pdf": "REPLACE_WITH_ACTUAL_DOCUMENT_ID",
        "nda.pdf": "REPLACE_WITH_ACTUAL_DOCUMENT_ID"
    }
    
    print(f"\n💡 Once documents are ingested, update document_ids and re-run.")
    
    # Uncomment to run evaluation with real document IDs
    # evaluation_results = run_evaluation(dataset, document_ids)
    # 
    # # Save results
    # output_path = Path(__file__).parent / "evaluation_results.json"
    # with open(output_path, 'w') as f:
    #     json.dump(evaluation_results, f, indent=2)
    # print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    main()
