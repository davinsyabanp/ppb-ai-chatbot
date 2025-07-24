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
from langchain_google_vertexai import ChatVertexAI

# Load environment variables for Langsmith
load_dotenv()

def initialize_llm_as_judge():
    """
    Initialize and return the LLM model from Vertex AI to be used as a judge.
    Ensures that you have authenticated with `gcloud auth application-default login`.
    """
    try:
        # Ensure PROJECT_ID and REGION are set in your environment variables
        project_id = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GCP_REGION", "asia-southeast1") # Default to Jakarta if not set

        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is not set. Please add it to your .env file.")

        print(f"Initializing Vertex AI with Project ID: {project_id} and Location: {location}")

        # Initialize the model from Vertex AI (e.g., gemini-1.0pro)
        llm = ChatVertexAI(
            project_id=project_id,
            location=location,
            model_name="gemini-1.0-pro",
            temperature=0.1,
            max_output_tokens=512
        )
        print("✅ Successfully initialized Vertex AI LLM.")
        return llm
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI LLM: {e}")
        print("Please ensure your Google Cloud credentials are set up correctly:")
        print("1. Run 'gcloud auth application-default login' in your terminal.")
        print("2. Ensure the GCP_PROJECT_ID variable is correct in your .env file.")
        return None

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
def evaluate_with_ragas(results_dataset: Dataset, judge_llm):
    """
    Evaluates the RAG pipeline results using RAGAS metrics with Vertex AI as the judge.
    """
    # Configure each metric to use the Vertex AI LLM
    faithfulness.llm = judge_llm
    answer_relevancy.llm = judge_llm
    context_precision.llm = judge_llm
    context_recall.llm = judge_llm

    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]

    print("Starting evaluation with RAGAS using Vertex AI as the judge...")
    result = evaluate(
        dataset=results_dataset,
        metrics=metrics,
        raise_exceptions=False # Prevents stopping on a single failure
    )

    print("Evaluation complete.")
    return result

# --- Main Execution ---
if __name__ == "__main__":
    # Initialize the judge LLM from Vertex AI
    llm_as_judge = initialize_llm_as_judge()

    if not llm_as_judge:
        print("Evaluation cancelled because the judge LLM (Vertex AI) failed to initialize.")
    else:
        # Step 1: Create the dataset from the CSV file
        evaluation_dataset = create_evaluation_dataset()

        if evaluation_dataset:
            # For a quick test, let's use a small sample (e.g., the first 5 entries)
            sample_size = min(5, len(evaluation_dataset))
            sample_dataset = evaluation_dataset.select(range(sample_size))

            # Step 2: Run the RAG pipeline on the sample
            results_with_context = asyncio.run(run_rag_pipeline(sample_dataset))

            # Step 3: Evaluate the results with RAGAS, passing the judge LLM
            evaluation_scores = evaluate_with_ragas(results_with_context, llm_as_judge)

            # Display the results
            print("\n--- RAGAS Evaluation Scores (Vertex AI Judge) ---")
            print(evaluation_scores)

            # Display as a pandas DataFrame for better readability
            df_results = evaluation_scores.to_pandas()
            print("\n--- Results in DataFrame ---")
            print(df_results.head()) 