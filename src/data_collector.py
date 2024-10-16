# Copyright 2024 The Apache Software Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import requests
import xml.etree.ElementTree as ET
import json
import re
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from collections import Counter
from llms import query_llm

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('maxent_ne_chunker')
nltk.download('maxent_ne_chunker_tab')
nltk.download('words')

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

    latest_release = extract_latest_release(project, ns)

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
        'latest_release': latest_release
    }

def extract_latest_release(project, ns):
    releases = project.findall('doap:release', ns)
    if not releases:
        return None

    latest_release = max(releases, key=lambda r: r.find('doap:revision', ns).text if r.find('doap:revision', ns) is not None else '')
    
    version = latest_release.find('doap:revision', ns)
    date = latest_release.find('doap:created', ns)
    download_url = latest_release.find('doap:file-release', ns)

    return {
        'version': version.text if version is not None else 'Unknown',
        'date': date.text if date is not None else 'Unknown',
        'download_url': clean_url(download_url.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')) if download_url is not None else None
    }

def find_logo(soup, base_url, project_name):
    # Common images to exclude
    exclude_list = [
        'maven-feather.png',
        'asf_logo.png',
        'apache_logo.png',
        'feather.png',
        'apache-logo.png',
        'apache_logo_wide.png',
        'slack-logo.svg',
        'twitter_32_26_white.png'
    ]

    def is_valid_logo(url):
        return not any(exclude_img in url.lower() for exclude_img in exclude_list)

    def similarity_score(s1, s2):
        return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

    # Priority order for logo search
    logo_selectors = [
        ('img.logo', 'src'),
        ('.logo img', 'src'),
        ('a.logo img', 'src'),
        ('#logo img', 'src'),
        ('img[alt*="logo"]', 'src'),
        ('img[src*="logo"]', 'src'),
    ]

    candidate_logos = []

    for selector, attr in logo_selectors:
        logos = soup.select(selector)
        for logo in logos:
            if logo and logo.get(attr):
                logo_url = urljoin(base_url, logo[attr])
                if is_valid_logo(logo_url):
                    candidate_logos.append(logo_url)

    # If no logo found with above selectors, try a more general approach
    if not candidate_logos:
        all_images = soup.find_all('img')
        for img in all_images:
            src = img.get('src')
            alt = img.get('alt', '').lower()
            if src and ('logo' in src.lower() or 'logo' in alt):
                logo_url = urljoin(base_url, src)
                if is_valid_logo(logo_url):
                    candidate_logos.append(logo_url)

    # Score candidate logos based on filename similarity to project name
    if candidate_logos:
        scored_logos = []
        for logo_url in candidate_logos:
            filename = urlparse(logo_url).path.split('/')[-1]
            score = similarity_score(project_name, filename)
            scored_logos.append((logo_url, score))
        
        # Sort by score descending and return the best match
        scored_logos.sort(key=lambda x: x[1], reverse=True)
        return scored_logos[0][0]

    return None

def scrape_metadata(url, project_name):
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
        
        metadata['logo'] = find_logo(soup, url, project_name)
        
        return metadata
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def extract_features_from_text(text):
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # Tokenize words, remove stopwords, and perform POS tagging
    stop_words = set(stopwords.words('english'))
    words = [word.lower() for sentence in sentences for word in word_tokenize(sentence) if word.isalnum()]
    words = [word for word in words if word not in stop_words]
    pos_tags = pos_tag(words)
    
    # Extract noun phrases
    def extract_noun_phrases(pos_tags):
        grammar = r"""
            NP: {<JJ.*>*<NN.*>+}  # Adjective(s) followed by Noun(s)
               {<NN.*>+}          # One or more Nouns
        """
        chunk_parser = nltk.RegexpParser(grammar)
        tree = chunk_parser.parse(pos_tags)
        for subtree in tree.subtrees():
            if subtree.label() == 'NP':
                yield ' '.join(word for word, tag in subtree.leaves())
    
    noun_phrases = list(extract_noun_phrases(pos_tags))
    
    # Extract named entities
    named_entities = []
    for sentence in sentences:
        chunks = ne_chunk(pos_tag(word_tokenize(sentence)))
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                named_entities.append(' '.join(c[0] for c in chunk))
    
    # Combine noun phrases and named entities
    features = noun_phrases + named_entities
    
    # Count feature frequencies
    feature_freq = Counter(features)
    
    # Extract top 10 most common features
    top_features = [feature for feature, _ in feature_freq.most_common(10)]
    
    return top_features

def scrape_additional_info(url):
    try:
        response = requests.get(clean_url(url), timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all text from paragraphs
        paragraphs = soup.find_all('p')
        full_text = ' '.join([p.get_text() for p in paragraphs])
        
        # Extract additional description (first 3 sentences)
        sentences = sent_tokenize(full_text)
        additional_description = ' '.join(sentences[:3])
        
        # Extract features using NLP
        features = extract_features_from_text(full_text)
        
        return {
            'additional_description': additional_description,
            'extracted_features': features
        }
    except Exception as e:
        print(f"Error scraping additional info from {url}: {str(e)}")
        return None

def fetch_additional_pages(base_url, max_pages=5):
    visited = set()
    to_visit = [base_url]
    additional_content = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract text content
                text_content = soup.get_text(separator=' ', strip=True)
                # Compact all whitespace
                compacted_content = re.sub(r'\s+', ' ', text_content).strip()
                additional_content.append(compacted_content)
                visited.add(url)

                # Find more links on the same domain
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(url, link['href'])
                    if urlparse(next_url).netloc == urlparse(base_url).netloc and next_url not in visited:
                        to_visit.append(next_url)
            else:
                print(f"Failed to fetch {url}: Status code {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")

    return ' '.join(additional_content)

def fetch_and_parse_doap(location):
    try:
        response = requests.get(clean_url(location))
        if response.status_code == 200:
            project_data = parse_doap_rdf(response.content)
            if project_data:
                # Scrape additional metadata from homepage
                if project_data['homepage']:
                    homepage_metadata = scrape_metadata(project_data['homepage'], project_data['name'])
                    if homepage_metadata:
                        project_data['homepage_metadata'] = homepage_metadata
                        if homepage_metadata['logo']:
                            project_data['logo'] = homepage_metadata['logo']
                    
                    # Scrape additional info
                    additional_info = scrape_additional_info(project_data['homepage'])
                    if additional_info:
                        if not project_data['description']:
                            project_data['description'] = additional_info['additional_description']
                        project_data['extracted_features'] = additional_info['extracted_features']
                
                # Scrape additional metadata from download page
                if project_data['download_page']:
                    download_metadata = scrape_metadata(project_data['download_page'], project_data['name'])
                    if download_metadata:
                        project_data['download_metadata'] = download_metadata
                        if not project_data.get('logo') and download_metadata['logo']:
                            project_data['logo'] = download_metadata['logo']
                
                # Fetch additional pages
                if project_data.get('homepage'):
                    additional_content = fetch_additional_pages(project_data['homepage'])
                    project_data['additional_content'] = additional_content
                return project_data
    except Exception as e:
        print(f"Error fetching or parsing DOAP from {location}: {str(e)}")
    return None

def compute_similarities(projects, top_n=5):
    project_descriptions = [f"{p['name']} {p['shortdesc']} {p.get('description', '')}" for p in projects]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(project_descriptions)
    
    similarities = cosine_similarity(tfidf_matrix)
    
    for i, project in enumerate(projects):
        similar_indices = similarities[i].argsort()[-top_n-1:-1][::-1]
        project['similar_projects'] = [
            {
                'name': projects[j]['name'],
                'score': similarities[i][j]
            }
            for j in similar_indices if i != j
        ]

def enhance_project_data(project):
    prompt = f"""
    You are an expert about Apache projects.
    Provide additional the information about this Apache project: {project['name']}
    And here is some basic information about it:
    Short description: {project['shortdesc']}
    Category: {project['category']}

    Please provide the following information in a structured format using JSON only for this
    specific project :
    1. An enhanced description (2-3 sentences)
    2. A list of 3-5 key features
    3. Suggested related Apache projects (2-3)
    4. A refined category (if applicable)
    5. Any additional insights gained from the extra content

    Format the response as JSON and never put any text or even quotes before or after the JSON:
    {{
        "enhanced_description": "...",
        "key_features": ["feature1", "feature2", ...],
        "related_projects": ["project1", "project2", ...],
        "refined_category": "...",
        "additional_insights": "..."
    }}
    """
        
    response = query_llm(prompt)
    try:
        # Remove any leading/trailing whitespace
        response = response.strip()
        # Remove triple backticks and "json" if present
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        # Remove any remaining leading/trailing whitespace
        response = response.strip()

        enhanced_data = json.loads(response)
        project.update(enhanced_data)
    except json.JSONDecodeError:
        print(f"Error parsing LLM response for project {project['name']} : {response}")
    return project

def fetch_apache_projects(use_llm=False):
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

    if use_llm:
        from llms import LocalLLM
        llm = LocalLLM()
        # Enhance project data using LLM
        with ThreadPoolExecutor(max_workers=5) as executor:
            enhanced_projects = list(tqdm(executor.map(lambda p: enhance_project_data(p, llm), projects), total=len(projects), desc="Enhancing project data"))
        projects = enhanced_projects

    # Compute similarities after all projects are fetched and optionally enhanced
    compute_similarities(projects)

    return projects

def main():
    parser = argparse.ArgumentParser(description="Collect and enhance Apache project data")
    parser.add_argument("--collect", action="store_true", help="Collect initial data from Apache")
    parser.add_argument("--enhance", action="store_true", help="Enhance data using LLM")
    args = parser.parse_args()

    if args.collect:
        apache_projects = fetch_apache_projects()
        with open('apache_projects_raw.json', 'w') as f:
            json.dump(apache_projects, f, indent=2)
        print(f"Collected data for {len(apache_projects)} projects. Saved to apache_projects_raw.json")

    if args.enhance:
        if not os.path.exists('apache_projects_raw.json'):
            print("Raw data file not found. Please run with --collect first.")
            return

        with open('apache_projects_raw.json', 'r') as f:
            apache_projects = json.load(f)

        enhanced_projects = []
        for project in tqdm(apache_projects, desc="Enhancing project data"):
            enhanced_project = enhance_project_data(project)
            enhanced_projects.append(enhanced_project)

        with open('apache_projects_enhanced.json', 'w') as f:
            json.dump(enhanced_projects, f, indent=2)
        print(f"Enhanced data for {len(enhanced_projects)} projects. Saved to apache_projects_enhanced.json")

if __name__ == "__main__":
    main()