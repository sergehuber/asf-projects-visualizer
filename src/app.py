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
        projects_by_category[category].append(project)
    
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

@app.route('/api/filter')
def filter_projects():
    query = request.args.get('query', '')
    
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
                "a possible stack of projects. Provide your response in JSON format "
                "with the following structure: "
                "{\"projects\": {\"project_name\": {\"explanation\": \"...\", \"role\": \"...\"}}, "
                "\"relationships\": [{\"source\": \"project1\", \"target\": \"project2\", "
                "\"description\": \"relationship_description\"}], "
                "\"stack\": [\"project1\", \"project2\", ...]}"
                "Do not include any text before or after the JSON content."
            )},
            {"role": "user", "content": (
                f"Given the query: '{query}', what Apache projects would "
                "be most relevant, how are they related to each other, and "
                "what would be a possible stack of these projects? Please provide "
                "the project names, brief explanations for why each project is relevant, "
                "its role in the stack, relationships between the projects, and a suggested stack."
            )}
        ]
    )
    
    try:
        # Extract JSON content from the response
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_content = json_match.group(0)
            ai_response = json.loads(json_content)
        else:
            raise ValueError("No JSON content found in the response")

        relevant_projects = ai_response.get('projects', {})
        relationships = ai_response.get('relationships', [])
        stack = ai_response.get('stack', [])
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing JSON from OpenAI response: {str(e)}")
        print("Raw response:")
        print(content)
        relevant_projects = {}
        relationships = []
        stack = []

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
                project_copy['matched_name'] = project_name  # Store the original AI-provided name
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
        'stack': stack,
        'total_projects': len(filtered_projects)
    })

if __name__ == '__main__':
    app.run(debug=True)