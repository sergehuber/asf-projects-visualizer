from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from openai import OpenAI
import re
import networkx as nx
from fuzzywuzzy import process

app = Flask(__name__, static_folder='../static')
CORS(app, resources={r"/*": {"origins": "*"}})

# Load Apache project data
with open('apache_projects.json', 'r') as f:
    apache_projects = json.load(f)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/projects')
def get_projects():
    # Group projects by category
    projects_by_category = {}
    for project in apache_projects:
        category = project.get('category', 'Uncategorized')
        if category not in projects_by_category:
            projects_by_category[category] = []
        
        # Simplify similar_projects to only include names
        project_copy = project.copy()
        project_copy['similar_projects'] = [sp['name'] for sp in project.get('similar_projects', [])]
        project_copy['features'] = project.get('features', project.get('extracted_features', []))
        
        projects_by_category[category].append(project_copy)
    
    # Sort categories and projects within categories
    result = []
    for category, projects in sorted(projects_by_category.items()):
        result.append({
            'name': category,
            'projects': sorted(projects, key=lambda x: x['name'])
        })
    
    # Sort categories by number of projects (descending)
    result.sort(key=lambda x: len(x['projects']), reverse=True)

    # Calculate total number of projects
    total_projects = sum(len(category['projects']) for category in result)

    return jsonify({"categories": result, "total_projects": total_projects})

class CustomJSONDecoder(json.JSONDecoder):
    def decode(self, s):
        # Remove invalid control characters
        s = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', s)
        return super().decode(s)

@app.route('/api/filter')
def filter_projects():
    query = request.args.get('query', '')
    
    # Prepare project metadata
    project_metadata = "\n".join([f"{p['name']}: {p['shortdesc']}" for p in apache_projects])
    
    # Use OpenAI to interpret the query and find relevant projects
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": (
                "You are an expert on Apache projects. Your task is to "
                "interpret user queries about Apache projects and return "
                "a list of relevant Apache project names along with brief "
                "explanations for why each project is relevant. Also, "
                "describe relationships between the projects and suggest "
                "multiple possible stacks of projects. Consider all Apache projects, "
                "including those for big data solutions like Apache Iceberg and Polaris. "
                "Provide your response in JSON format with the following structure: "
                "{\"projects\": {\"project_name\": {\"explanation\": \"...\", \"role\": \"...\", \"features\": [\"feature1\", \"feature2\", ...]}}, "
                "\"relationships\": [{\"source\": \"project1\", \"target\": \"project2\", "
                "\"description\": \"relationship_description\"}], "
                "\"stacks\": [{\"name\": \"stack_name\", \"projects\": [\"project1\", \"project2\", ...], \"description\": \"stack_description\"}]}"
                "Do not include any text before or after the JSON content.\n\n"
                f"Here's a list of Apache projects with short descriptions:\n{project_metadata}"
            )},
            {"role": "user", "content": (
                f"Given the query: '{query}', what Apache projects would "
                "be most relevant, how are they related to each other, and "
                "what would be possible stacks of these projects? Please provide "
                "the project names, brief explanations for why each project is relevant, "
                "its role in the stack, key features, relationships between the projects, and multiple suggested stacks."
            )}
        ]
    )
    
    try:
        # Extract JSON content from the response
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_content = json_match.group(0)
            ai_response = json.loads(json_content, cls=CustomJSONDecoder)
        else:
            raise ValueError("No JSON content found in the response")

        relevant_projects = ai_response.get('projects', {})
        relationships = ai_response.get('relationships', [])
        stacks = ai_response.get('stacks', [])
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing JSON from OpenAI response: {str(e)}")
        print("Raw response:")
        print(content)
        relevant_projects = {}
        relationships = []
        stacks = []

    # Filter and explain projects based on AI response
    filtered_projects = []
    for project_name, project_info in relevant_projects.items():
        # Use fuzzy matching to find the closest project name
        closest_match, score = process.extractOne(project_name, [p['name'] for p in apache_projects])
        if score >= 80:  # You can adjust this threshold as needed
            project = next((p for p in apache_projects if p['name'] == closest_match), None)
            if project:
                project_copy = project.copy()
                project_copy['filter_explanation'] = project_info['explanation']
                project_copy['role'] = project_info['role']
                project_copy['features'] = project_info.get('features', [])
                project_copy['matched_name'] = project_name  # Store the original AI-provided name
                project_copy['similar_projects'] = [sp['name'] for sp in project_copy.get('similar_projects', [])]
                filtered_projects.append(project_copy)

    # Create a graph of project relationships
    G = nx.Graph()
    for project in filtered_projects:
        G.add_node(project['name'])
    for rel in relationships:
        G.add_edge(rel['source'], rel['target'], description=rel['description'])

    # Convert the graph to a format suitable for D3.js
    graph_data = {
        "nodes": [{"id": node, "group": 1} for node in G.nodes()],
        "links": [{"source": u, "target": v, "value": 1, "description": G[u][v]['description']} for u, v in G.edges()]
    }

    return jsonify({
        'projects': filtered_projects,
        'graph': graph_data,
        'stacks': stacks,
        'total_projects': len(filtered_projects)
    })

@app.route('/api/project_names')
def get_project_names():
    query = request.args.get('query', '').lower()
    project_names = [p['name'] for p in apache_projects if query in p['name'].lower()]
    return jsonify(project_names)

@app.route('/api/compare')
def compare_projects():
    project_names = request.args.getlist('projects')
    
    if len(project_names) < 2 or len(project_names) > 4:
        return jsonify({"error": "Please specify between 2 and 4 projects for comparison"}), 400

    projects = []
    for name in project_names:
        project = next((p for p in apache_projects if p['name'] == name), None)
        if not project:
            return jsonify({"error": f"Project '{name}' not found"}), 404
        projects.append(project)

    comparison = {
        "projects": [
            {
                "name": p['name'],
                "shortdesc": p['shortdesc'],
                "category": p.get('category', 'Unknown'),
                "features": p.get('features', p.get('extracted_features', []))
            } for p in projects
        ]
    }

    return jsonify(comparison)

if __name__ == '__main__':
    app.run(debug=True)