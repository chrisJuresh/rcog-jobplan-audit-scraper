import os
import csv
from collections import defaultdict

def clean_data(input_file, output_file):
    # Read the input CSV file
    with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        data = list(reader)

    # Group the data by file1 folder
    grouped_data = defaultdict(list)
    for row in data:
        file1, file2, similarity = row
        folder1 = os.path.dirname(file1)
        grouped_data[folder1].append((file1, file2, float(similarity)))

    # Find the highest similarity entry for each folder
    results = []
    for folder, entries in grouped_data.items():
        highest_similarity_entry = max(entries, key=lambda x: x[2])
        results.append((folder, highest_similarity_entry[1], highest_similarity_entry[2]))

    # Sort results by similarity (descending order)
    results.sort(key=lambda x: x[2], reverse=True)

    # Write the results to the output CSV file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['File 1 Folder', 'File 2', 'Similarity (%)'])
        for folder, file2, similarity in results:
            writer.writerow([folder, file2, f"{similarity:.2f}"])

    print(f"Cleaned data saved to {output_file}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find the most recent similarity results file
    similarity_files = [f for f in os.listdir(script_dir) if f.startswith("similarity_results_") and f.endswith(".csv")]
    if not similarity_files:
        print("No similarity results file found.")
        exit(1)
    
    input_file = max(similarity_files, key=lambda f: os.path.getctime(os.path.join(script_dir, f)))
    input_file = os.path.join(script_dir, input_file)
    
    output_file = os.path.join(script_dir, "cleaned_similarity_results.csv")
    
    clean_data(input_file, output_file)
