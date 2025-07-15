import pandas as pd
import numpy as np
from app.core import get_response_for_evaluation
from app.models import load_llm
import os
from dotenv import load_dotenv
import time
import re

# Load environment variables
load_dotenv()

# Load Gemini LLM
llm = load_llm()

def call_gemini(prompt):
    """
    Call Gemini with a prompt and return the response.
    """
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "Error"

def extract_score_from_response(response):
    """
    Extract numerical score from Gemini response.
    Looks for patterns like 'Skor: 8/10' or '8/10' or '8'.
    """
    # Look for patterns like "Skor: 8/10", "8/10", "8", etc.
    patterns = [
        r'Skor:\s*(\d+)/10',
        r'(\d+)/10',
        r'Skor:\s*(\d+)',
        r'(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            score = int(match.group(1))
            # Ensure score is between 0 and 10
            return max(0, min(10, score))
    
    # If no score found, try to infer from text
    if 'sangat baik' in response.lower() or 'excellent' in response.lower():
        return 9
    elif 'baik' in response.lower() or 'good' in response.lower():
        return 7
    elif 'cukup' in response.lower() or 'fair' in response.lower():
        return 5
    elif 'kurang' in response.lower() or 'poor' in response.lower():
        return 3
    else:
        return 5  # Default score

def evaluate_faithfulness(context, answer):
    """
    Evaluate if the answer faithfully reflects the information in the context.
    """
    prompt = f"""
    Tugas: Evaluasi kesetiaan jawaban terhadap konteks yang diberikan.
    
    Konteks:
    {context}
    
    Jawaban:
    {answer}
    
    Pertanyaan: Apakah jawaban tersebut setia dan akurat mencerminkan informasi yang ada dalam konteks? 
    
    Berikan penilaian dengan skala 1-10, di mana:
    10 = Sangat setia, semua informasi akurat
    5 = Cukup setia, sebagian besar informasi akurat
    1 = Tidak setia, banyak informasi tidak akurat atau tidak ada dalam konteks
    
    Berikan juga penjelasan singkat mengapa Anda memberikan skor tersebut.
    
    Format jawaban:
    Penjelasan: [penjelasan Anda]
    Skor: [angka]/10
    """
    
    response = call_gemini(prompt)
    score = extract_score_from_response(response)
    
    return {
        'score': score,
        'explanation': response,
        'metric': 'faithfulness'
    }

def evaluate_answer_relevancy(question, answer):
    """
    Evaluate if the answer is relevant and directly addresses the question.
    """
    prompt = f"""
    Tugas: Evaluasi relevansi jawaban terhadap pertanyaan.
    
    Pertanyaan: {question}
    Jawaban: {answer}
    
    Pertanyaan: Apakah jawaban tersebut relevan dan langsung menjawab pertanyaan yang diajukan?
    
    Berikan penilaian dengan skala 1-10, di mana:
    10 = Sangat relevan, langsung menjawab pertanyaan
    5 = Cukup relevan, sebagian menjawab pertanyaan
    1 = Tidak relevan, tidak menjawab pertanyaan
    
    Berikan juga penjelasan singkat mengapa Anda memberikan skor tersebut.
    
    Format jawaban:
    Penjelasan: [penjelasan Anda]
    Skor: [angka]/10
    """
    
    response = call_gemini(prompt)
    score = extract_score_from_response(response)
    
    return {
        'score': score,
        'explanation': response,
        'metric': 'answer_relevancy'
    }

def evaluate_context_precision(question, contexts):
    """
    Evaluate if the retrieved contexts are relevant to the question.
    """
    context_text = "\n\n".join(contexts) if contexts else "Tidak ada konteks"
    
    prompt = f"""
    Tugas: Evaluasi presisi konteks yang diambil untuk pertanyaan.
    
    Pertanyaan: {question}
    
    Konteks yang diambil:
    {context_text}
    
    Pertanyaan: Apakah konteks yang diambil relevan dan tepat untuk menjawab pertanyaan tersebut?
    
    Berikan penilaian dengan skala 1-10, di mana:
    10 = Sangat presisi, semua konteks sangat relevan
    5 = Cukup presisi, sebagian besar konteks relevan
    1 = Tidak presisi, sebagian besar konteks tidak relevan
    
    Berikan juga penjelasan singkat mengapa Anda memberikan skor tersebut.
    
    Format jawaban:
    Penjelasan: [penjelasan Anda]
    Skor: [angka]/10
    """
    
    response = call_gemini(prompt)
    score = extract_score_from_response(response)
    
    return {
        'score': score,
        'explanation': response,
        'metric': 'context_precision'
    }

def evaluate_context_recall(question, ground_truth, contexts):
    """
    Evaluate if the retrieved contexts contain the necessary information to answer the question.
    """
    context_text = "\n\n".join(contexts) if contexts else "Tidak ada konteks"
    
    prompt = f"""
    Tugas: Evaluasi recall konteks - apakah konteks yang diambil mengandung informasi yang diperlukan.
    
    Pertanyaan: {question}
    
    Jawaban yang diharapkan (ground truth):
    {ground_truth}
    
    Konteks yang diambil:
    {context_text}
    
    Pertanyaan: Apakah konteks yang diambil mengandung informasi yang diperlukan untuk memberikan jawaban yang diharapkan?
    
    Berikan penilaian dengan skala 1-10, di mana:
    10 = Sangat lengkap, semua informasi yang diperlukan ada
    5 = Cukup lengkap, sebagian besar informasi ada
    1 = Tidak lengkap, banyak informasi yang diperlukan tidak ada
    
    Berikan juga penjelasan singkat mengapa Anda memberikan skor tersebut.
    
    Format jawaban:
    Penjelasan: [penjelasan Anda]
    Skor: [angka]/10
    """
    
    response = call_gemini(prompt)
    score = extract_score_from_response(response)
    
    return {
        'score': score,
        'explanation': response,
        'metric': 'context_recall'
    }

def run_gemini_evaluation(csv_path="evaluation/eval_dataset_PPB.csv", sample_size=5):
    """
    Run the complete Gemini-based evaluation.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return None
    
    # Load dataset
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} questions from {csv_path}")
    
    # Take a sample
    sample_df = df.head(sample_size)
    print(f"Evaluating {len(sample_df)} questions...")
    
    results = []
    
    for idx, row in sample_df.iterrows():
        question = row['question']
        ground_truth = row['ground_truth']
        
        print(f"\n--- Processing Question {idx + 1}/{len(sample_df)} ---")
        print(f"Question: {question}")
        
        # Get RAG response
        print("Getting RAG response...")
        rag_result = get_response_for_evaluation(question)
        answer = rag_result['answer']
        contexts = rag_result['contexts']
        
        print(f"Answer: {answer[:100]}...")
        print(f"Number of contexts: {len(contexts)}")
        
        # Evaluate each metric
        print("Evaluating faithfulness...")
        faithfulness_result = evaluate_faithfulness("\n\n".join(contexts), answer)
        
        print("Evaluating answer relevancy...")
        relevancy_result = evaluate_answer_relevancy(question, answer)
        
        print("Evaluating context precision...")
        precision_result = evaluate_context_precision(question, contexts)
        
        print("Evaluating context recall...")
        recall_result = evaluate_context_recall(question, ground_truth, contexts)
        
        # Store results
        result = {
            'question': question,
            'ground_truth': ground_truth,
            'answer': answer,
            'contexts_count': len(contexts),
            'faithfulness_score': faithfulness_result['score'],
            'faithfulness_explanation': faithfulness_result['explanation'],
            'relevancy_score': relevancy_result['score'],
            'relevancy_explanation': relevancy_result['explanation'],
            'precision_score': precision_result['score'],
            'precision_explanation': precision_result['explanation'],
            'recall_score': recall_result['score'],
            'recall_explanation': recall_result['explanation']
        }
        
        results.append(result)
        
        # Add delay to avoid rate limiting
        time.sleep(2)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Calculate average scores
    avg_scores = {
        'faithfulness': results_df['faithfulness_score'].mean(),
        'answer_relevancy': results_df['relevancy_score'].mean(),
        'context_precision': results_df['precision_score'].mean(),
        'context_recall': results_df['recall_score'].mean()
    }
    
    # Save detailed results
    results_df.to_csv('gemini_evaluation_results.csv', index=False)
    
    # Save summary
    summary_df = pd.DataFrame([avg_scores])
    summary_df.to_csv('gemini_evaluation_summary.csv', index=False)
    
    return results_df, avg_scores

def print_summary(avg_scores):
    """
    Print a formatted summary of the evaluation results.
    """
    print("\n" + "="*60)
    print("GEMINI RAG EVALUATION SUMMARY")
    print("="*60)
    
    for metric, score in avg_scores.items():
        print(f"{metric.replace('_', ' ').title()}: {score:.2f}/10")
    
    print("\n" + "="*60)
    print("INTERPRETATION:")
    print("="*60)
    print("9-10: Excellent")
    print("7-8:  Good")
    print("5-6:  Fair")
    print("3-4:  Poor")
    print("1-2:  Very Poor")
    print("="*60)

if __name__ == "__main__":
    print("Starting Gemini-based RAG Evaluation...")
    print("This will evaluate your RAG system using Gemini with Indonesian prompts.")
    
    # Run evaluation
    results, avg_scores = run_gemini_evaluation(sample_size=5)
    
    if results is not None:
        # Print summary
        print_summary(avg_scores)
        
        print(f"\nDetailed results saved to: gemini_evaluation_results.csv")
        print(f"Summary saved to: gemini_evaluation_summary.csv")
        
        # Show first few results
        print(f"\nFirst 3 results preview:")
        print(results[['question', 'faithfulness_score', 'relevancy_score', 'precision_score', 'recall_score']].head(3))
    else:
        print("Evaluation failed. Please check the error messages above.") 