import requests
import xml.etree.ElementTree as ET
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

def clean_url(url):
    """Clean and correct minor errors in URLs."""
    if url is None:
        return None
    
    # Remove leading/trailing whitespace
    url = url.strip()
    
    # Correct 'ihttp' to 'http'
    if url.startswith('ihttp'):
        url = 'http' + url[5:]
    
    # Handle cases where the URL already starts with a protocol
    if url.startswith(('http://', 'https://')):
        return url

    if url.startswith('https//'):
        url = 'https://' + url[7:]

    return url

def fetch_xml(url):
    response = requests.get(clean_url(url))
    return ET.fromstring(response.content)

def parse_doap_rdf(rdf_content):
    root = ET.fromstring(rdf_content)
    ns = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'doap': 'http://usefulinc.com/ns/doap#',
        'asfext': 'http://projects.apache.org/ns/asfext#'
    }

    project = root.find('.//doap:Project', ns)
    if project is None:
        return None

    name = project.find('doap:name', ns)
    shortdesc = project.find('doap:shortdesc', ns)
    description = project.find('doap:description', ns)
    category = project.find('doap:category', ns)
    programming_language = project.find('doap:programming-language', ns)
    homepage = project.find('doap:homepage', ns)
    download_page = project.find('doap:download-page', ns)
    bug_database = project.find('doap:bug-database', ns)
    mailing_list = project.find('doap:mailing-list', ns)

    return {
        'name': name.text if name is not None else 'Unknown',
        'shortdesc': shortdesc.text if shortdesc is not None else '',
        'description': description.text if description is not None else '',
        'category': category.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '').split('/')[-1] if category is not None else 'Unknown',
        'programming_language': programming_language.text if programming_language is not None else 'Unknown',
        'homepage': clean_url(homepage.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')) if homepage is not None else None,
        'download_page': clean_url(download_page.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')) if download_page is not None else None,
        'bug_database': clean_url(bug_database.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')) if bug_database is not None else None,
        'mailing_list': clean_url(mailing_list.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')) if mailing_list is not None else None,
    }

def find_logo(soup, base_url):
    # Common images to exclude
    exclude_list = [
        'maven-feather.png',
        'asf_logo.png',
        'apache_logo.png',
        'feather.png',
        'apache-logo.png',
        'apache_logo_wide.png'
    ]

    # Look for common logo patterns
    logo_patterns = [
        ('img[src*="logo"]', 'src'),
        ('img[alt*="logo"]', 'src'),
        ('img[class*="logo"]', 'src'),
        ('img[id*="logo"]', 'src'),
        ('a[class*="logo"] img', 'src'),
        ('.logo img', 'src'),
        ('#logo img', 'src'),
    ]

    for pattern, attr in logo_patterns:
        for logo in soup.select(pattern):
            if logo and logo.get(attr):
                logo_url = urljoin(base_url, logo[attr])
                if not any(exclude_img in logo_url.lower() for exclude_img in exclude_list):
                    return logo_url

    return None

def scrape_metadata(url):
    try:
        response = requests.get(clean_url(url), timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        metadata = {
            'title': soup.title.string if soup.title else None,
            'meta_description': None,
            'h1_headers': [],
            'links': [],
            'logo': None,
        }
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['meta_description'] = meta_desc.get('content')
        
        for h1 in soup.find_all('h1'):
            metadata['h1_headers'].append(h1.text.strip())
        
        for link in soup.find_all('a', href=True):
            href = clean_url(link['href'])
            if href and href.startswith('http'):
                metadata['links'].append(href)
        
        metadata['logo'] = find_logo(soup, url)
        
        return metadata
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def fetch_and_parse_doap(location):
    try:
        response = requests.get(clean_url(location))
        if response.status_code == 200:
            project_data = parse_doap_rdf(response.content)
            if project_data:
                # Scrape additional metadata from homepage
                if project_data['homepage']:
                    homepage_metadata = scrape_metadata(project_data['homepage'])
                    if homepage_metadata:
                        project_data['homepage_metadata'] = homepage_metadata
                        if homepage_metadata['logo']:
                            project_data['logo'] = homepage_metadata['logo']
                
                # Scrape additional metadata from download page
                if project_data['download_page']:
                    download_metadata = scrape_metadata(project_data['download_page'])
                    if download_metadata:
                        project_data['download_metadata'] = download_metadata
                        if not project_data.get('logo') and download_metadata['logo']:
                            project_data['logo'] = download_metadata['logo']
                
                return project_data
    except Exception as e:
        print(f"Error fetching or parsing DOAP from {location}: {str(e)}")
    return None

def fetch_apache_projects():
    projects_xml_url = "https://svn.apache.org/repos/asf/comdev/projects.apache.org/trunk/data/projects.xml"
    root = fetch_xml(projects_xml_url)

    locations = [location.text for location in root.findall('.//location')]

    projects = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_location = {executor.submit(fetch_and_parse_doap, location): location for location in locations}
        
        with tqdm(total=len(locations), desc="Processing projects") as pbar:
            for future in as_completed(future_to_location):
                location = future_to_location[future]
                try:
                    project_data = future.result()
                    if project_data:
                        projects.append(project_data)
                except Exception as e:
                    print(f"Error processing {location}: {str(e)}")
                pbar.update(1)

    return projects

def main():
    apache_projects = fetch_apache_projects()
    with open('apache_projects.json', 'w') as f:
        json.dump(apache_projects, f, indent=2)
    print(f"Saved {len(apache_projects)} Apache projects to apache_projects.json")

if __name__ == '__main__':
    main()