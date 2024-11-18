from flask import Flask, render_template, request, jsonify, send_from_directory, json
from werkzeug.utils import secure_filename
import os
from silly_visualizer import generate_visualization, SourceCodeParser
import ast
import re
import threading
import matplotlib
import matplotlib.pyplot as plt
import traceback
import networkx as nx
import numpy as np
import io
import base64
import graphviz
import plotly.graph_objs as go

matplotlib.use('Agg')  # Use Agg backend to prevent GUI issues

app = Flask(__name__, template_folder='frontend/', static_folder='frontend/')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
ALLOWED_EXTENSIONS = {'py', 'java'}

# Create a thread lock for matplotlib operations
plot_lock = threading.Lock()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_language(code):
    """Detect the programming language based on code content."""
    python_patterns = [
        r'def\s+\w+\s*\([^)]*\)\s*:',
        r'import\s+[\w\s,]+',
        r'class\s+\w+(\s*\([^)]*\))?\s*:',
        r'print\s*\([^)]*\)'
    ]

    java_patterns = [
        r'public\s+class\s+\w+',
        r'private|protected|public\s+\w+\s+\w+\s*\([^)]*\)',
        r'import\s+[\w.]+;',
        r'System\.out\.println'
    ]

    python_score = sum(1 for pattern in python_patterns if re.search(pattern, code))
    java_score = sum(1 for pattern in java_patterns if re.search(pattern, code))

    return 'python' if python_score >= java_score else 'java'


"""
Route for the home page.

This function handles the route for the root URL ('/'). It renders and returns
the 'index.html' template when the home page is accessed.

Returns:
    Response: The rendered 'index.html' template.
"""
@app.route('/')
def home():
    return render_template('index.html')


"""
Handle the visualization request from the client.
This endpoint accepts either a file upload or raw code input, processes the code,
generates a visualization, and returns the visualization along with code analysis.
Request Methods:
    POST
Request Parameters:
    file (optional): A file object containing the code to be visualized. Only .py and .java files are allowed.
    code (optional): A string containing the code to be visualized. This is used if no file is uploaded.
    language (optional): The programming language of the code. If 'auto', the language will be detected automatically.
    diagram_type (optional): The type of diagram to generate. Defaults to 'ast'.
Returns:
    JSON: A JSON object containing the following keys:
        - graph_data: The generated visualization graph data.
        - title: The title of the visualization.
        - language_used: The detected or specified programming language.
        - uploaded_file (optional): The name of the uploaded file, if a file was uploaded.
        - error (optional): An error message if an error occurred during processing.
Raises:
    Exception: If an error occurs during file handling, code processing, or visualization generation.
"""
@app.route('/visualize', methods=['POST'])
def visualize_code():
    try:
        # Parse request data
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'code': request.form.get('code', ''),
                'language': request.form.get('language', ''),
                'diagram_type': request.form.get('diagram_type', 'ast')
            }
        
        # Validate input
        code = data.get('code', '').strip()
        language = data.get('language', '').lower()
        diagram_type = data.get('diagram_type', 'ast').lower()
        
        if not code:
            return jsonify({
                'error': 'Missing code',
                'details': 'Source code is required for visualization'
            }), 400
        
        if language not in ['python', 'java']:
            language = 'python' if 'def ' in code or 'import ' in code else 'java'
        
        if diagram_type not in ['ast', 'cfg', 'ddg']:
            diagram_type = 'ast'
        
        # Generate visualization
        try:
            # Create a NetworkX graph from the code
            parser = SourceCodeParser()
            G, metadata = parser.parse(code, language)
            
            # Convert NetworkX graph to D3.js format
            nodes = []
            links = []
            
            # Process nodes
            for node in G.nodes():
                node_data = G.nodes[node]
                nodes.append({
                    'id': str(node),
                    'label': str(node),
                    'type': node_data.get('type', 'default'),
                    'color': _get_node_color(node_data.get('type', 'default')),
                    'value': node_data.get('value', '')
                })
            
            # Process edges
            for source, target in G.edges():
                links.append({
                    'source': str(source),
                    'target': str(target)
                })
            
            # Generate title based on diagram type
            title_map = {
                'ast': 'Abstract Syntax Tree',
                'cfg': 'Control Flow Graph',
                'ddg': 'Data Dependency Graph'
            }
            title = title_map.get(diagram_type, 'Code Visualization')
            
            return jsonify({
                'graph_data': {
                    'nodes': nodes,
                    'links': links
                },
                'title': title,
                'language': language,
                'diagram_type': diagram_type,
                'parsing_metadata': metadata
            })
        except Exception as viz_error:
            app.logger.error(f"Visualization generation error: {str(viz_error)}")
            return jsonify({
                'error': 'Visualization generation failed',
                'details': str(viz_error)
            }), 500
    
    except Exception as e:
        app.logger.error(f"Request processing error: {str(e)}")
        return jsonify({
            'error': 'Request processing failed',
            'details': str(e)
        }), 400

def _get_node_color(node_type: str) -> str:
    """
    Generate a color based on the node type for more granular visualization.
    
    Args:
        node_type (str): Type of the AST node
    
    Returns:
        str: Hex color code for the node
    """
    # Comprehensive color mapping for different node types
    color_map = {
        # Python-specific node types
        'Module': '#2C3E50',           # Dark blue-gray for module/file level
        'ClassDef': '#3498DB',         # Bright blue for class definitions
        'FunctionDef': '#2ECC71',      # Green for function definitions
        'AsyncFunctionDef': '#27AE60',  # Darker green for async functions
        
        # Variable and attribute types
        'Name': '#F39C12',             # Orange for variable names
        'Attribute': '#9B59B6',        # Purple for attributes
        'Constant': '#E67E22',         # Warm orange for constants
        
        # Control flow nodes
        'If': '#E74C3C',               # Red for if statements
        'For': '#3498DB',              # Blue for for loops
        'While': '#9B59B6',            # Purple for while loops
        'Try': '#1ABC9C',              # Teal for try blocks
        'Except': '#F1C40F',           # Yellow for except blocks
        
        # Expression and call types
        'Call': '#16A085',             # Teal for function calls
        'BinOp': '#D35400',            # Dark orange for binary operations
        'Compare': '#8E44AD',          # Deep purple for comparisons
        
        # Import and module-related
        'Import': '#34495E',           # Dark slate gray for imports
        'ImportFrom': '#2980B9',       # Slightly lighter blue for from imports
        
        # Java-specific node types
        'ClassDeclaration': '#3498DB',     # Blue for Java classes
        'MethodDeclaration': '#2ECC71',    # Green for Java methods
        'FieldDeclaration': '#F39C12',     # Orange for Java fields
        'ConstructorDeclaration': '#E74C3C', # Red for constructors
        'InterfaceDeclaration': '#9B59B6',  # Purple for interfaces
        
        # Default fallback
        'default': '#95A5A6'           # Light gray for unrecognized types
    }
    
    return color_map.get(node_type, color_map['default'])

def _generate_graph_image(G: nx.DiGraph) -> str:
    """
    Generate a graph visualization with Graphviz for enhanced spacing and coloring
    
    Args:
        G (nx.DiGraph): Input graph to visualize
    
    Returns:
        str: Base64 encoded SVG of the graph
    """
    # Ensure graph is not empty
    if len(G.nodes()) == 0:
        G.add_node("Empty Graph")
    
    # Create a new directed graph with enhanced styling
    dot = graphviz.Digraph(
        comment='Code Structure',
        engine='dot',  # Use dot layout engine for hierarchical layout
        graph_attr={
            'rankdir': 'TB',  # Top to Bottom layout
            'splines': 'ortho',  # Orthogonal edges
            'nodesep': '2.0',  # Significantly increased node horizontal separation
            'ranksep': '2.5',  # Significantly increased vertical rank separation
            'margin': '1.0',  # Add larger margin around the entire graph
        },
        node_attr={
            'style': 'filled,rounded',  # Rounded nodes
            'fontname': 'Arial',
            'fontsize': '10',
            'shape': 'box',
            'fontcolor': 'black',  # Explicit black font color
            'color': 'black',  # Black border
            'penwidth': '1.5',  # Thicker border
        },
        edge_attr={
            'color': 'gray',
            'penwidth': '1.0'
        }
    )

    # Color mapping function with improved palette
    def get_node_color(node_type):
        color_map = {
            'ClassDef': 'lightblue',
            'FunctionDef': 'lightgreen',
            'MethodDeclaration': 'lightyellow',
            'default': 'white'
        }
        return color_map.get(node_type, color_map['default'])

    # Add nodes with type-based coloring and enhanced labeling
    for node in G.nodes():
        node_type = G.nodes[node].get('type', 'default')
        node_label = G.nodes[node].get('value', node_type)
        
        # Truncate long labels with ellipsis
        if len(node_label) > 30:
            node_label = node_label[:30] + '...'
        
        dot.node(
            str(node), 
            node_label, 
            fillcolor=get_node_color(node_type),
            fontcolor='black',  # Ensure black text for each node
            color='black'  # Black border for each node
        )

    # Add edges with slight curve
    for edge in G.edges():
        dot.edge(str(edge[0]), str(edge[1]), style='curved')

    # Render to SVG with UTF-8 encoding
    svg_data = dot.pipe(format='svg', encoding='utf-8')
    
    # Encode to base64
    return base64.b64encode(svg_data).decode('utf-8')

def get_code_stats(code: str, language: str) -> dict:
    """Analyzes the code and returns basic statistics."""
    stats = {
        "lines_of_code": len([line for line in code.splitlines() if line.strip()]),
        "characters": len(code),
        "functions": 0,
        "classes": 0
    }

    try:
        if language == 'python':
            tree = ast.parse(code)
            stats["functions"] = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            stats["classes"] = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        elif language == 'java':
            import javalang
            tree = javalang.parse.parse(code)
            stats["functions"] = sum(1 for path, node in tree if isinstance(node, javalang.tree.MethodDeclaration))
            stats["classes"] = sum(1 for path, node in tree if isinstance(node, javalang.tree.ClassDeclaration))
    except Exception as e:
        stats["parse_error"] = str(e)

    return stats


if __name__ == '__main__':
    app.run(debug=True, threaded=True)