import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
import os
from app.core import get_response_for_evaluation
import asyncio
from dotenv import load_dotenv

# Load environment variables for Langsmith
load_dotenv()

# --- 1. Evaluation Dataset Creation ---
def create_evaluation_dataset(csv_path="evaluation/eval_dataset_PPB.csv"):
    """
    Reads a CSV file and generates an evaluation dataset with
    'question' and 'ground_truth' columns.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    # Optionally, save a copy for reference
    df.to_csv("ragas_evaluation_dataset.csv", index=False)
    print(f"Evaluation dataset loaded from {csv_path} and saved to ragas_evaluation_dataset.csv")
    return Dataset.from_pandas(df)

# --- 2. RAG Pipeline Execution ---
async def run_rag_pipeline(dataset: Dataset):
    """
    Runs the RAG pipeline for each question in the dataset and
    collects the results.
    """
    results = []
    for entry in dataset:
        question = entry['question']
        print(f"Processing question: {question}")
        # Call the evaluation function from core.py
        rag_output = get_response_for_evaluation(question)
        results.append({
            "question": question,
            "answer": rag_output['answer'],
            "contexts": rag_output['contexts'],
            "ground_truth": entry['ground_truth']
        })

    return Dataset.from_list(results)

# --- 3. RAGAS Evaluation ---
def evaluate_with_ragas(results_dataset: Dataset):
    """
    Evaluates the RAG pipeline results using RAGAS metrics.
    """
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]

    print("Starting evaluation with RAGAS...")
    result = evaluate(
        dataset=results_dataset,
        metrics=metrics,
        raise_exceptions=False # Prevents stopping on a single failure
    )

    print("Evaluation complete.")
    return result

# --- Main Execution ---
if __name__ == "__main__":
    # Step 1: Create the dataset from the CSV file
    evaluation_dataset = create_evaluation_dataset()

    if evaluation_dataset:
        # For a quick test, let's use a small sample (e.g., the first 5 entries)
        sample_size = min(5, len(evaluation_dataset))
        sample_dataset = evaluation_dataset.select(range(sample_size))

        # Step 2: Run the RAG pipeline on the sample
        results_with_context = asyncio.run(run_rag_pipeline(sample_dataset))

        # Step 3: Evaluate the results with RAGAS
        evaluation_scores = evaluate_with_ragas(results_with_context)

        # Display the results
        print("\n--- RAGAS Evaluation Scores ---")
        print(evaluation_scores)

        # Display as a pandas DataFrame for better readability
        df_results = evaluation_scores.to_pandas()
        print("\n--- Results in DataFrame ---")
        print(df_results.head()) 