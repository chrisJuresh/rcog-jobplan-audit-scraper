import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox

def fetch_jobs(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve content from {url}: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def parse_jobs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    job_cards = soup.find_all('li', class_='nhsuk-list-panel')
    for job in job_cards:
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
            'Title': job_title,
            'Employer': employer,
            'Closing Date': closing_date,
            'Salary': salary,
            'Link': job_link
        })
    return jobs

def get_contact_details(job_link):
    print(f"Fetching details from {job_link}")
    html_content = fetch_jobs(job_link)
    if not html_content:
        return None, None, None, None

    soup = BeautifulSoup(html_content, 'html.parser')
    contact_div = soup.find('div', id='contact_details')

    if contact_div:
        job_title = contact_div.find('p', id='contact_details_job_title').text.strip() if contact_div.find('p', id='contact_details_job_title') else None
        contact_name = contact_div.find('p', id='contact_details_name').text.strip() if contact_div.find('p', id='contact_details_name') else None
        contact_email = contact_div.find('a', href=True).text.strip() if contact_div.find('a', href=True) else None
        contact_number = contact_div.find('p', id='contact_details_number').text.strip() if contact_div.find('p', id='contact_details_number') else None
        print(f"Extracted contact details: {job_title}, {contact_name}, {contact_email}, {contact_number}")
        return job_title, contact_name, contact_email, contact_number
    else:
        print(f"No contact details found in {job_link}")
    return None, None, None, None

def get_total_pages(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination = soup.find('a', class_='nhsuk-pagination__link nhsuk-pagination__link--next')
    if pagination:
        page_info = pagination.find('span', class_='nhsuk-pagination__page').text
        total_pages = int(page_info.split()[-1])
        return total_pages
    return 1

def save_to_csv(jobs, filename):
    df = pd.DataFrame(jobs)
    df.to_csv(filename, index=False)
    print(f"Saved {len(jobs)} jobs to {filename}")

def scrape_jobs(urls):
    all_jobs = []
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
                jobs = parse_jobs(html_content)
                for job in jobs:
                    job_title, contact_name, contact_email, contact_number = get_contact_details(job['Link'])
                    job.update({
                        'Contact Job Title': job_title,
                        'Contact Name': contact_name,
                        'Contact Email': contact_email,
                        'Contact Number': contact_number
                    })
                all_jobs.extend(jobs)

            time.sleep(1) 

    save_to_csv(all_jobs, 'nhs_jobs.csv')

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

tk.Label(root, text="Enter URLs (one per line):").pack()

url_textbox = scrolledtext.ScrolledText(root, width=60, height=20)
url_textbox.pack()

start_button = tk.Button(root, text="Start Scraping", command=start_scraping)
start_button.pack()

root.mainloop()