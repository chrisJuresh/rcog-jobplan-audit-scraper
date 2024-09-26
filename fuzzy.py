import os
import textract
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from PyPDF2 import PdfReader
import multiprocessing
from functools import partial
import docx
import csv
from datetime import datetime
from tqdm import tqdm

def extract_text(file_path):
    try:
        if file_path.lower().endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf = PdfReader(file)
                return ' '.join(page.extract_text() for page in pdf.pages)
        elif file_path.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            return ' '.join(paragraph.text for paragraph in doc.paragraphs)
        elif file_path.lower().endswith('.doc'):
            return textract.process(file_path).decode('utf-8')
        else:
            return textract.process(file_path).decode('utf-8')
    except Exception as e:
        print(f"Error processing file: {file_path}")
        print(f"Error details: {str(e)}")
        return ""

def get_files_recursive(folder_path):
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.doc', '.docx', '.pdf')) and not file.startswith('~$'):
                file_list.append(os.path.join(root, file))
    return file_list

def compute_similarity(text1, text2):
    if not text1.strip() or not text2.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity * 100  # Convert to percentage
    except ValueError:
        print("Error: Unable to compute similarity. Possibly empty or identical documents.")
        return 0.0

def process_file_pair(file1, files2, folder1, folder2, threshold):
    text1 = extract_text(file1)
    results = []
    for file2 in files2:
        text2 = extract_text(file2)
        similarity = compute_similarity(text1, text2)
        if similarity >= threshold:
            results.append((os.path.relpath(file1, folder1), os.path.relpath(file2, folder2), similarity))
    return results

def find_similar_documents(folder1, folder2, threshold=10, num_cores=None):
    files1 = get_files_recursive(folder1)
    files2 = get_files_recursive(folder2)
    
    if num_cores is None:
        num_cores = multiprocessing.cpu_count()
    
    print(f"Using {num_cores} cores for processing.")
    
    pool = multiprocessing.Pool(processes=num_cores)
    func = partial(process_file_pair, files2=files2, folder1=folder1, folder2=folder2, threshold=threshold)
    
    results = list(tqdm(pool.imap(func, files1), total=len(files1), desc="Processing"))
    
    pool.close()
    pool.join()
    
    # Flatten the results list
    flattened_results = [item for sublist in results for item in sublist]
    
    # Sort results by similarity (descending order)
    flattened_results.sort(key=lambda x: x[2], reverse=True)
    
    return flattened_results

def save_to_csv(results, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['File 1', 'File 2', 'Similarity (%)'])
        for file1, file2, similarity in results:
            csvwriter.writerow([file1, file2, f"{similarity:.2f}"])
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder1 = os.path.join(script_dir, "jobs", "job_documents")
    folder2 = os.path.join(script_dir, "jobs", "rcog-jobs")

    print(f"Comparing documents in:")
    print(f"  {os.path.relpath(folder1, script_dir)}")
    print(f"  {os.path.relpath(folder2, script_dir)}")
    print("---")

    results = find_similar_documents(folder1, folder2, num_cores=16)
    
    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(script_dir, f"similarity_results_{timestamp}.csv")
    
    save_to_csv(results, output_file)
    
    # Print all results to console
    print("\nAll Similar Document Pairs:")
    for file1, file2, similarity in results:
        print(f"Similarity between {file1} and {file2}: {similarity:.2f}%")
    
    print(f"\nTotal similar document pairs found: {len(results)}")
