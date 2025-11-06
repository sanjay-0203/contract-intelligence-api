#!/usr/bin/env python3
"""
Evaluation script for Contract Intelligence API Q&A system.

Usage:
    python eval/evaluate_qa.py --api-url http://localhost:8000 --document-id 1
"""

import json
import requests
import argparse
from typing import List, Dict, Any

def load_qa_dataset(filepath: str) -> List[Dict[str, Any]]:
    """Load Q&A dataset from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data["qa_pairs"]

def evaluate_answer(answer: str, expected_keywords: List[str]) -> float:
    """
    Evaluate answer quality by checking for expected keywords.
    
    Returns: Score between 0.0 and 1.0
    """
    answer_lower = answer.lower()
    found_keywords = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    score = found_keywords / len(expected_keywords) if expected_keywords else 0.0
    return min(1.0, score)

def run_evaluation(api_url: str, document_id: int, dataset_path: str = "eval/qa_dataset.json"):
    """Run Q&A evaluation against the API."""
    qa_pairs = load_qa_dataset(dataset_path)
    
    results = {
        "total_questions": len(qa_pairs),
        "scores": [],
        "by_difficulty": {"easy": [], "medium": [], "hard": []},
        "api_url": api_url,
        "document_id": document_id
    }
    
    print(f"Running evaluation on {len(qa_pairs)} Q&A pairs...")
    print(f"API URL: {api_url}")
    print(f"Document ID: {document_id}\n")
    
    for qa in qa_pairs:
        question = qa["question"]
        expected_keywords = qa["expected_keywords"]
        difficulty = qa["difficulty"]
        
        try:
            # Call the API
            response = requests.post(
                f"{api_url}/ask",
                params={
                    "question": question,
                    "document_id": document_id
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Q{qa['id']}: API error - {response.status_code}")
                score = 0.0
            else:
                data = response.json()
                answer = data.get("answer", "")
                confidence = data.get("confidence", 0.0)
                
                # Evaluate answer
                keyword_score = evaluate_answer(answer, expected_keywords)
                combined_score = (keyword_score + confidence) / 2
                
                print(f"✓ Q{qa['id']} ({difficulty}): {question}")
                print(f"  Answer: {answer[:100]}...")
                print(f"  Score: {combined_score:.2f} (keywords: {keyword_score:.2f}, confidence: {confidence:.2f})\n")
                
                score = combined_score
        except Exception as e:
            print(f"❌ Q{qa['id']}: Error - {str(e)}")
            score = 0.0
        
        results["scores"].append({
            "question_id": qa["id"],
            "question": question,
            "score": score,
            "difficulty": difficulty
        })
        results["by_difficulty"][difficulty].append(score)
    
    # Calculate statistics
    all_scores = [r["score"] for r in results["scores"]]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Overall Average Score: {avg_score:.2f}/1.0")
    
    for difficulty in ["easy", "medium", "hard"]:
        scores = results["by_difficulty"][difficulty]
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  {difficulty.capitalize()}: {avg:.2f}/1.0 ({len(scores)} questions)")
    
    print(f"\nTotal Questions Evaluated: {len(all_scores)}")
    print(f"Passed (>0.5): {sum(1 for s in all_scores if s > 0.5)}/{len(all_scores)}")
    
    # Save results
    results["average_score"] = avg_score
    with open("eval/results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: eval/results.json")
    return avg_score

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Contract Intelligence API Q&A system")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--document-id", type=int, default=1, help="Document ID to evaluate")
    parser.add_argument("--dataset", default="eval/qa_dataset.json", help="Q&A dataset path")
    
    args = parser.parse_args()
    
    try:
        score = run_evaluation(args.api_url, args.document_id, args.dataset)
        exit(0 if score > 0.5 else 1)
    except Exception as e:
        print(f"Evaluation failed: {str(e)}")
        exit(1)
