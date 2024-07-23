import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def fetch_jobs(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve content: {response.status_code}")
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
        
        location_tag = job.find('div', class_='location')
        location = location_tag.text.strip() if location_tag else None
        
        salary_tag = job.find('div', class_='salary')
        salary = salary_tag.text.strip() if salary_tag else None
        
        jobs.append({
            'Title': job_title,
            'Employer': employer,
            'Location': location,
            'Salary': salary,
            'Link': job_link
        })
    return jobs

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

def main():
    base_url = 'https://www.jobs.nhs.uk/candidate/search/results?keyword=gynaecologist&skipPhraseSuggester=true&payBand=CONSULTANT&language=en'
    all_jobs = []

    first_page_content = fetch_jobs(base_url)
    if not first_page_content:
        return

    total_pages = get_total_pages(first_page_content)
    print(f"Total pages to scrape: {total_pages}")

    for page in range(1, total_pages + 1):
        url = f"{base_url}&page={page}"
        print(f"Scraping page {page} of {total_pages}")
        
        html_content = fetch_jobs(url)
        if html_content:
            jobs = parse_jobs(html_content)
            all_jobs.extend(jobs)
        
        time.sleep(2)  # Add a delay to avoid overwhelming the server

    save_to_csv(all_jobs, 'nhs_jobs.csv')

if __name__ == "__main__":
    main()
