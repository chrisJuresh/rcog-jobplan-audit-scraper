import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import shutil

# Create a session to maintain cookies
session = requests.Session()

def fetch_jobs(url):
    try:
        response = session.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve content from {url}: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def parse_jobs(html_content, start_id):
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    job_cards = soup.find_all('li', class_='nhsuk-list-panel')
    for job in job_cards:
        job_id = start_id
        start_id += 1
        job_title_tag = job.find('a', {'data-test': 'search-result-job-title'})
        if job_title_tag:
            job_title = job_title_tag.text.strip()
            job_link = 'https://www.jobs.nhs.uk' + job_title_tag['href']
        else:
            job_title = None
            job_link = None
        
        employer_tag = job.find('h3', class_='nhsuk-u-font-weight-bold')
        if employer_tag:
            employer = employer_tag.contents[0].strip()
        else:
            employer = None
        
        salary_tag = job.find('li', {'data-test': 'search-result-salary'})
        salary = salary_tag.find('strong').text.strip() if salary_tag else None

        closing_date_tag = job.find('li', {'data-test': 'search-result-closingDate'})
        closing_date = closing_date_tag.find('strong').text.strip() if closing_date_tag else None
        
        jobs.append({
            'ID': job_id,
            'Title': job_title,
            'Employer': employer,
            'Closing Date': closing_date,
            'Salary': salary,
            'Link': job_link
        })
    return jobs, start_id

def get_contact_details(job_link):
    print(f"Fetching details from {job_link}")
    html_content = fetch_jobs(job_link)
    if not html_content:
        return None, None, None, None, []

    soup = BeautifulSoup(html_content, 'html.parser')
    contact_div = soup.find('div', id='contact_details')

    job_title = contact_name = contact_email = contact_number = None
    if contact_div:
        job_title = contact_div.find('p', id='contact_details_job_title').text.strip() if contact_div.find('p', id='contact_details_job_title') else None
        contact_name = contact_div.find('p', id='contact_details_name').text.strip() if contact_div.find('p', id='contact_details_name') else None
        contact_email = contact_div.find('a', href=True).text.strip() if contact_div.find('a', href=True) else None
        contact_number = contact_div.find('p', id='contact_details_number').text.strip() if contact_div.find('p', id='contact_details_number') else None
        print(f"Extracted contact details: {job_title}, {contact_name}, {contact_email}, {contact_number}")

    supporting_documents = []
    document_forms = soup.find_all('form', method='post')
    for form in document_forms:
        document_input = form.find('input', {'name': 'document'})
        if document_input:
            document_id = document_input['value']
            document_name = form.find('input', class_='nhsuk-button--link')['value']
            supporting_documents.append((document_id, document_name))

    return job_title, contact_name, contact_email, contact_number, supporting_documents

def download_document(document_id, document_name, folder_path):
    url = 'https://www.jobs.nhs.uk/candidate/jobadvert/C9318-24-0587/getfile'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.jobs.nhs.uk/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    data = {
        'document': document_id,
        '_csrf': session.cookies.get('XSRF-TOKEN', '')  # Get CSRF token from cookies
    }
    try:
        response = session.post(url, headers=headers, data=data, allow_redirects=True)
        if response.status_code == 200:
            file_path = os.path.join(folder_path, document_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {document_name}")
        else:
            print(f"Failed to download {document_name}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {document_name}: {e}")

def get_total_pages(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination = soup.find('a', class_='nhsuk-pagination__link nhsuk-pagination__link--next')
    if pagination:
        page_info = pagination.find('span', class_='nhsuk-pagination__page').text
        total_pages = int(page_info.split()[-1])
        return total_pages
    return 1

def clean_url(url):
    return url.split('?')[0]

def contains_keyword(title):
    keywords = ["Obs", "Gyn", "O&G"]
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in keywords)

def save_to_csv(jobs, filename, folder_paths):
    df = pd.DataFrame(jobs)
    df = df[df['Title'].apply(contains_keyword)]  # Filter jobs based on keywords
    df['Cleaned Link'] = df['Link'].apply(clean_url)
    initial_count = len(df)
    df.drop_duplicates(subset=['Cleaned Link'], keep='first', inplace=True)  # Remove duplicates based on 'Cleaned Link' column
    duplicate_count = initial_count - len(df)
    
    if duplicate_count > 0:
        duplicate_links = set(jobs[i]['Link'] for i in range(len(jobs))) - set(df['Link'])
        duplicate_folders = [folder_paths[i] for i in range(len(jobs)) if jobs[i]['Link'] in duplicate_links]
        for folder in duplicate_folders:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                print(f"Deleted folder: {folder}")

    df.drop(columns=['Cleaned Link'], inplace=True)  # Remove the temporary column
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} jobs to {filename}")

def scrape_jobs(urls):
    all_jobs = []
    folder_paths = []
    start_id = 1  # Initialize the start_id
    for base_url in urls:
        first_page_content = fetch_jobs(base_url)
        if not first_page_content:
            continue

        total_pages = get_total_pages(first_page_content)
        print(f"Total pages to scrape for {base_url}: {total_pages}")

        for page in range(1, total_pages + 1):
            url = f"{base_url}&page={page}"
            print(f"Scraping page {page} of {total_pages} for {base_url}")

            html_content = fetch_jobs(url)
            if html_content:
                jobs, start_id = parse_jobs(html_content, start_id)
                for job in jobs:
                    job_title, contact_name, contact_email, contact_number, supporting_documents = get_contact_details(job['Link'])
                    job.update({
                        'Contact Job Title': job_title,
                        'Contact Name': contact_name,
                        'Contact Email': contact_email,
                        'Contact Number': contact_number
                    })

                    # Create a folder for each job using only the ID
                    folder_name = f"{job['ID']}"
                    folder_path = os.path.join('job_documents', folder_name)
                    os.makedirs(folder_path, exist_ok=True)
                    folder_paths.append(folder_path)

                    # Download supporting documents
                    for doc_id, doc_name in supporting_documents:
                        download_document(doc_id, doc_name, folder_path)

                all_jobs.extend(jobs)

            time.sleep(1)

    save_to_csv(all_jobs, 'nhs_jobs.csv', folder_paths)

def start_scraping():
    url_text = url_textbox.get("1.0", tk.END).strip()
    urls = [url.strip() for url in url_text.split('\n') if url.strip()]
    if not urls:
        messagebox.showerror("Error", "Please enter at least one URL")
        return
    
    scrape_jobs(urls)
    messagebox.showinfo("Success", "Scraping completed and data saved to nhs_jobs.csv")

# GUI setup
root = tk.Tk()
root.title("Job Scraper")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

url_label = tk.Label(frame, text="Enter NHS job URLs (one per line):")
url_label.pack()

url_textbox = scrolledtext.ScrolledText(frame, width=60, height=10)
url_textbox.pack(pady=5)

start_button = tk.Button(frame, text="Start Scraping", command=start_scraping)
start_button.pack(pady=5)

root.mainloop()