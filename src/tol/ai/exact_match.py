
import json
import pandas as pd
from transformers import pipeline
from typing import List, Dict
from transformers import T5ForConditionalGeneration, T5Tokenizer, BartForConditionalGeneration, BartTokenizer

def load_test_data(file_path: str) -> List[Dict[str, str]]:
    """
    Load test data from file
    """
    
    # Example for CSV file
    df = pd.read_csv(file_path)
    return df.to_dict('records')

def normalize_json(json_str: str) -> str:
    """Normalize JSON string for comparison"""
    try:
        parsed = json.loads(json_str.strip())
        return json.dumps(parsed, sort_keys=True, separators=(',', ':'))
    except json.JSONDecodeError:
        return json_str.strip()

def evaluate_exact_match(test_data: List[Dict[str, str]]):
    """
    Simple exact match evaluation using pipelines
    
    Args:
        t5_model_path: Path to your fine-tuned T5 model
        bart_model_path: Path to your fine-tuned BART model  
        test_data: List of dicts with 'input' and 'expected_output' keys
    """
    
    # Initialize pipelines
    print("Loading models...")
    # t5_model = T5ForConditionalGeneration.from_pretrained("src/tol/ai/t5-jsongen-finetuned/checkpoint-20000")
    # t5_tokenizer = T5Tokenizer.from_pretrained("src/tol/ai/t5-jsongen-finetuned/checkpoint-20000", local_files_only=True)
    # t5_pipeline = pipeline("text2text-generation", model=t5_model, tokenizer=t5_tokenizer)
    bart_model = BartForConditionalGeneration.from_pretrained("src/tol/ai/bart-jsongen-finetuned/checkpoint-20000")
    bart_tokenizer = BartTokenizer.from_pretrained("src/tol/ai/bart-jsongen-finetuned/checkpoint-20000", local_files_only=True)
    bart_pipeline = pipeline("text2text-generation", model=bart_model, tokenizer=bart_tokenizer)
    
    # Initialize counters
    t5_exact_matches = 0
    bart_exact_matches = 0
    total_samples = len(test_data)
    
    results = []
    
    print(f"Evaluating {total_samples} samples...")
    
    for i, sample in enumerate(test_data):
        input_text = sample['input_text']
        expected_output = sample['target_text']
        
        # Generate predictions
        # t5_pred = t5_pipeline(input_text, max_length=512, do_sample=False)[0]['generated_text']
        bart_pred = bart_pipeline(input_text, max_length=512, do_sample=False)[0]['generated_text']
        
        # Normalize for comparison
        expected_norm = normalize_json(expected_output)
        # t5_norm = normalize_json(t5_pred)
        bart_norm = normalize_json(bart_pred)
        
        # Check exact matches
        # t5_match = (expected_norm == t5_norm)
        bart_match = (expected_norm == bart_norm)
        
        # if t5_match:
        #     t5_exact_matches += 1
        if bart_match:
            bart_exact_matches += 1
        
        # Store results for analysis
        results.append({
            'input': input_text,
            'expected': expected_output,
            # 't5_prediction': t5_pred,
            'bart_prediction': bart_pred,
            # 't5_exact_match': t5_match,
            'bart_exact_match': bart_match
        })
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{total_samples} samples")
    
    # Calculate final accuracies
    # t5_accuracy = t5_exact_matches / total_samples
    bart_accuracy = bart_exact_matches / total_samples
    
    # Print results
    print("\n" + "="*50)
    print("EXACT MATCH RESULTS")
    print("="*50)
    # print(f"T5 Exact Match Accuracy:   {t5_accuracy:.3f} ({t5_exact_matches}/{total_samples})")
    print(f"BART Exact Match Accuracy: {bart_accuracy:.3f} ({bart_exact_matches}/{total_samples})")
    # print(f"Difference (T5 - BART):    {t5_accuracy - bart_accuracy:.3f}")
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_df.to_csv('model_comparison_results.csv', index=False)
    print(f"\nDetailed results saved to 'model_comparison_results.csv'")
    
    return {
        # 't5_accuracy': t5_accuracy,
        'bart_accuracy': bart_accuracy,
        'detailed_results': results_df
    }
    
if __name__ == "__main__":
    # Update these paths to your models and data
    TEST_DATA_PATH = "src/tol/ai/exact_match_test_data.csv"
    
    # Load test data
    test_data = load_test_data(TEST_DATA_PATH)
    
    # Run evaluation
    results = evaluate_exact_match(test_data)
    
    # Optional: Look at some examples where models disagreed
    # detailed_results = results['detailed_results']
    # disagreements = detailed_results[
    #     detailed_results['t5_exact_match'] != detailed_results['bart_exact_match']
    # ]
    
    # print(f"\nFound {len(disagreements)} cases where models disagreed")
    # if len(disagreements) > 0:
    #     print("\nFirst few disagreement examples:")
    #     for i, row in disagreements.head(3).iterrows():
    #         print(f"\nInput: {row['input']}")
    #         print(f"Expected: {row['expected']}")
    #         print(f"T5: {row['t5_prediction']} (Match: {row['t5_exact_match']})")
    #         print(f"BART: {row['bart_prediction']} (Match: {row['bart_exact_match']})")