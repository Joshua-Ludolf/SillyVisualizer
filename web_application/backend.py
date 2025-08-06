from flask import Flask, render_template, request, jsonify, send_from_directory, json
from werkzeug.utils import secure_filename
import os
from silly_visualizer import SourceCodeParser, DiagramGenerator
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


def networkx_to_interactive_svg(graph, metadata=None, title="Graph Visualization"):
    """
    Convert NetworkX graph to interactive SVG with embedded JavaScript.
    
    Args:
        graph: NetworkX graph object
        metadata: Optional metadata dictionary
        title: Title for the visualization
    
    Returns:
        str: Interactive SVG as string
    """
    import math
    
    print(f"DEBUG: Creating SVG for graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    
    # SVG dimensions - make larger for many nodes
    num_nodes = len(graph.nodes())
    if num_nodes > 100:
        width, height = 2000, 1500
    else:
        width, height = 1000, 800
    margin = 50
    
    # Calculate node positions using a simple layout to avoid scipy dependency
    import math
    
    num_nodes = len(graph.nodes())
    if num_nodes == 0:
        centered_pos = {}
    elif num_nodes == 1:
        # Single node at center
        node = list(graph.nodes())[0]
        centered_pos = {node: (width/2, height/2)}
    elif num_nodes <= 12:
        # Circular layout for small number of nodes
        centered_pos = {}
        radius = min(width, height) * 0.3  # 30% of the smaller dimension
        center_x, center_y = width/2, height/2
        
        nodes = list(graph.nodes())
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / num_nodes
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            centered_pos[node] = (x, y)
    else:
        # Grid layout for larger number of nodes
        centered_pos = {}
        nodes = list(graph.nodes())
        cols = math.ceil(math.sqrt(num_nodes))
        rows = math.ceil(num_nodes / cols)
        
        cell_width = (width - 100) / cols  # Leave 50px margin on each side
        cell_height = (height - 100) / rows
        
        # Ensure minimum spacing between nodes
        min_spacing = 40 if num_nodes > 500 else 50
        if cell_width < min_spacing or cell_height < min_spacing:
            # Increase canvas size if nodes would be too close
            if cell_width < min_spacing:
                width = cols * min_spacing + 100
                cell_width = min_spacing
            if cell_height < min_spacing:
                height = rows * min_spacing + 100
                cell_height = min_spacing
        
        for i, node in enumerate(nodes):
            col = i % cols
            row = i // cols
            x = 50 + (col + 0.5) * cell_width
            y = 50 + (row + 0.5) * cell_height
            centered_pos[node] = (x, y)
    
    print(f"DEBUG: Positioned {len(centered_pos)} nodes")
    if centered_pos:
        sample_node = list(centered_pos.keys())[0]
        print(f"DEBUG: Sample position - Node {sample_node}: {centered_pos[sample_node]}")
    
    # Start building SVG
    svg_parts = []
    svg_parts.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" 
     viewBox="0 0 {width} {height}" style="background: white; border: 1px solid #ddd;">
     
<defs>
    <!-- Gradients for node types -->''')
    
    # Add gradients for different node types
    node_types = {
        'Module': '#2C3E50',
        'ClassDef': '#3498DB', 
        'FunctionDef': '#2ECC71',
        'Name': '#F39C12',
        'Attribute': '#9B59B6',
        'Call': '#16A085',
        'Control': '#E74C3C',
        'default': '#95A5A6'
    }
    
    for node_type, color in node_types.items():
        svg_parts.append(f'''
    <radialGradient id="grad-{node_type}" cx="50%" cy="50%" r="50%">
        <stop offset="0%" style="stop-color:{color};stop-opacity:0.8" />
        <stop offset="100%" style="stop-color:{color};stop-opacity:1" />
    </radialGradient>''')
    
    # Arrow marker for edges
    svg_parts.append('''
    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
            refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
    </marker>
</defs>

<!-- Main graph group with zoom/pan transform -->
<g id="graph-content" transform="translate(0,0) scale(1)">''')
    
    # Add edges first (so they appear behind nodes)
    for source, target in graph.edges():
        edge_data = graph.edges[source, target]
        x1, y1 = centered_pos[source]
        x2, y2 = centered_pos[target]
        
        edge_type = edge_data.get('type', 'default')
        stroke_color = '#666'
        if edge_type == 'inheritance':
            stroke_color = '#e74c3c'
        elif edge_type == 'composition':
            stroke_color = '#3498db'
        elif edge_type == 'dependency':
            stroke_color = '#f39c12'
            
        svg_parts.append(f'''
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
          stroke="{stroke_color}" stroke-width="2" 
          marker-end="url(#arrowhead)" opacity="0.8"
          class="edge" data-source="{source}" data-target="{target}"/>''')
    
    # Add nodes
    nodes_added = 0
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        x, y = centered_pos[node_id]
        
        node_type = node_data.get('type', 'default')
        # Map node type to color
        mapped_type = 'default'
        if node_type in ['ClassDef', 'ClassDeclaration']:
            mapped_type = 'ClassDef'
        elif node_type in ['FunctionDef', 'MethodDeclaration']:
            mapped_type = 'FunctionDef'
        elif node_type in node_types:
            mapped_type = node_type
            
        value = node_data.get('value', str(node_id))
        lineno = node_data.get('lineno', '')
        
        # Node radius based on type and number of nodes
        base_radius = 15 if num_nodes > 500 else 20 if num_nodes > 100 else 25
        radius = base_radius
        if mapped_type == 'Module':
            radius = base_radius + 5
        elif mapped_type in ['ClassDef', 'FunctionDef']:
            radius = base_radius + 2
            
        # Create node group
        svg_parts.append(f'''
    <g class="node" data-id="{node_id}" data-type="{node_type}" 
       transform="translate({x},{y})" style="cursor: pointer;">
        <circle r="{radius}" fill="url(#grad-{mapped_type})" 
                stroke="white" stroke-width="2" class="node-circle"
                onmouseover="highlightNode(this)" onmouseout="unhighlightNode(this)"/>''')
        
        # Add text label if it's an important node type
        if mapped_type in ['Module', 'ClassDef', 'FunctionDef']:
            display_text = value[:12] + '...' if len(value) > 12 else value
            svg_parts.append(f'''
        <text text-anchor="middle" dy="{radius + 15}" fill="#333" 
              font-size="10" font-weight="bold" class="node-label"
              pointer-events="none">{display_text}</text>''')
        
        # Tooltip data
        tooltip_text = f"Type: {node_type}\\nValue: {value}"
        if lineno:
            tooltip_text += f"\\nLine: {lineno}"
            
        svg_parts.append(f'''
        <title>{tooltip_text}</title>
    </g>''')
        nodes_added += 1
    
    print(f"DEBUG: Added {nodes_added} nodes to SVG")
    
    svg_parts.append('''
</g>

<!-- Interactive controls -->
<g id="controls" style="font-family: Arial, sans-serif;">
    <!-- Zoom controls -->
    <g id="zoom-controls" transform="translate(20, 20)">
        <rect width="35" height="100" fill="rgba(255,255,255,0.9)" 
              stroke="#ddd" rx="5" />
        <text x="17.5" y="15" text-anchor="middle" font-size="10" fill="#666">Zoom</text>
        
        <!-- Zoom in button -->
        <g class="zoom-btn" onclick="zoomIn()" style="cursor: pointer;">
            <rect x="5" y="20" width="25" height="25" fill="white" 
                  stroke="#ddd" rx="3" onmouseover="this.setAttribute('fill','#f0f0f0')"
                  onmouseout="this.setAttribute('fill','white')"/>
            <text x="17.5" y="37" text-anchor="middle" font-size="16" font-weight="bold">+</text>
        </g>
        
        <!-- Zoom out button -->
        <g class="zoom-btn" onclick="zoomOut()" style="cursor: pointer;">
            <rect x="5" y="50" width="25" height="25" fill="white" 
                  stroke="#ddd" rx="3" onmouseover="this.setAttribute('fill','#f0f0f0')"
                  onmouseout="this.setAttribute('fill','white')"/>
            <text x="17.5" y="67" text-anchor="middle" font-size="16" font-weight="bold">−</text>
        </g>
        
        <!-- Reset button -->
        <g class="zoom-btn" onclick="resetView()" style="cursor: pointer;">
            <rect x="5" y="80" width="25" height="15" fill="white" 
                  stroke="#ddd" rx="3" onmouseover="this.setAttribute('fill','#f0f0f0')"
                  onmouseout="this.setAttribute('fill','white')"/>
            <text x="17.5" y="90" text-anchor="middle" font-size="10">⌂</text>
        </g>
    </g>
    
    <!-- Legend -->
    <g id="legend" transform="translate(20, 140)">
        <rect width="120" height="140" fill="rgba(255,255,255,0.9)" 
              stroke="#ddd" rx="5" />
        <text x="60" y="15" text-anchor="middle" font-size="12" font-weight="bold">Legend</text>''')
    
    # Add legend items
    legend_y = 30
    for i, (node_type, color) in enumerate(list(node_types.items())[:6]):  # Show first 6 types
        svg_parts.append(f'''
        <circle cx="15" cy="{legend_y}" r="8" fill="{color}" stroke="white" stroke-width="1"/>
        <text x="30" y="{legend_y + 4}" font-size="10" fill="#333">{node_type}</text>''')
        legend_y += 20
    
    svg_parts.append('''
    </g>
</g>

<script type="text/javascript"><![CDATA[
    let currentScale = 1;
    let currentX = 0;
    let currentY = 0;
    const minScale = 0.1;
    const maxScale = 3;
    
    function updateTransform() {
        const graphContent = document.getElementById('graph-content');
        graphContent.setAttribute('transform', 
            `translate(${currentX}, ${currentY}) scale(${currentScale})`);
    }
    
    function zoomIn() {
        if (currentScale < maxScale) {
            currentScale *= 1.2;
            updateTransform();
        }
    }
    
    function zoomOut() {
        if (currentScale > minScale) {
            currentScale /= 1.2;
            updateTransform();
        }
    }
    
    function resetView() {
        currentScale = 1;
        currentX = 0;
        currentY = 0;
        updateTransform();
    }
    
    function highlightNode(element) {
        const nodeGroup = element.parentNode;
        const nodeId = nodeGroup.getAttribute('data-id');
        
        // Highlight the node
        element.setAttribute('stroke', '#ffd700');
        element.setAttribute('stroke-width', '4');
        
        // Highlight connected edges
        const edges = document.querySelectorAll('.edge');
        edges.forEach(edge => {
            const source = edge.getAttribute('data-source');
            const target = edge.getAttribute('data-target');
            if (source === nodeId || target === nodeId) {
                edge.setAttribute('stroke-width', '4');
                edge.setAttribute('opacity', '1');
            } else {
                edge.setAttribute('opacity', '0.3');
            }
        });
        
        // Dim other nodes
        const nodes = document.querySelectorAll('.node-circle');
        nodes.forEach(node => {
            if (node !== element) {
                node.setAttribute('opacity', '0.5');
            }
        });
    }
    
    function unhighlightNode(element) {
        // Reset node highlighting
        element.setAttribute('stroke', 'white');
        element.setAttribute('stroke-width', '2');
        
        // Reset all edges
        const edges = document.querySelectorAll('.edge');
        edges.forEach(edge => {
            edge.setAttribute('stroke-width', '2');
            edge.setAttribute('opacity', '0.8');
        });
        
        // Reset all nodes
        const nodes = document.querySelectorAll('.node-circle');
        nodes.forEach(node => {
            node.setAttribute('opacity', '1');
        });
    }
    
    // Pan functionality
    let isPanning = false;
    let startX, startY;
    
    document.addEventListener('mousedown', function(e) {
        if (e.target.tagName === 'svg' || e.target.id === 'graph-content') {
            isPanning = true;
            startX = e.clientX - currentX;
            startY = e.clientY - currentY;
            e.preventDefault();
        }
    });
    
    document.addEventListener('mousemove', function(e) {
        if (isPanning) {
            currentX = e.clientX - startX;
            currentY = e.clientY - startY;
            updateTransform();
        }
    });
    
    document.addEventListener('mouseup', function() {
        isPanning = false;
    });
    
    // Mouse wheel zoom
    document.addEventListener('wheel', function(e) {
        e.preventDefault();
        if (e.deltaY < 0) {
            zoomIn();
        } else {
            zoomOut();
        }
    });
]]></script>

</svg>''')
    
    return ''.join(svg_parts)


def networkx_to_d3(graph, metadata=None):
    """Convert NetworkX graph to D3.js compatible format."""
    # Create nodes list
    nodes = []
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        nodes.append({
            'id': str(node_id),
            'label': node_data.get('value', str(node_id)),
            'type': node_data.get('type', 'default'),
            'value': node_data.get('value', ''),
            'lineno': node_data.get('lineno'),
            'details': node_data.get('details', ''),
            'group': _get_node_group(node_data.get('type', 'default'))
        })
    
    # Create links list
    links = []
    for source, target in graph.edges():
        edge_data = graph.edges[source, target]
        links.append({
            'source': str(source),
            'target': str(target),
            'type': edge_data.get('type', 'default'),
            'weight': edge_data.get('weight', 1),
            'label': edge_data.get('label', '')
        })
    
    return {
        'nodes': nodes,
        'links': links,
        'metadata': metadata or {}
    }


def _get_node_group(node_type):
    """Map node types to group numbers for D3.js visualization."""
    type_groups = {
        'Module': 1,
        'ClassDef': 2,
        'ClassDeclaration': 2,
        'FunctionDef': 3,
        'MethodDeclaration': 3,
        'Name': 4,
        'Attribute': 5,
        'Call': 6,
        'If': 7,
        'For': 7,
        'While': 7,
        'Return': 8,
        'Assign': 9,
        'BinOp': 10,
        'Compare': 10,
        'Constant': 11,
        'default': 0
    }
    return type_groups.get(node_type, 0)


def _create_cfg_graph(original_graph):
    """Create a Control Flow Graph by filtering relevant nodes."""
    cfg_graph = nx.DiGraph()
    
    # Filter for control flow nodes
    for node in original_graph.nodes():
        node_type = original_graph.nodes[node].get('type', '').lower()
        if any(cf in node_type for cf in ['if', 'for', 'while', 'functiondef', 'module', 'return', 'methoddeclaration', 'classdeclaration']):
            cfg_graph.add_node(node, **original_graph.nodes[node])
    
    # Add edges between control flow nodes
    for node in cfg_graph.nodes():
        for successor in original_graph.successors(node):
            if successor in cfg_graph.nodes():
                edge_data = original_graph.edges.get((node, successor), {})
                cfg_graph.add_edge(node, successor, **edge_data)
    
    return cfg_graph if len(cfg_graph.nodes()) > 0 else original_graph


def _create_ddg_graph(original_graph):
    """Create a Data Dependency Graph by filtering relevant nodes."""
    ddg_graph = nx.DiGraph()
    
    # Filter for data dependency nodes
    for node in original_graph.nodes():
        node_type = original_graph.nodes[node].get('type', '').lower()
        if any(data_type in node_type for data_type in ['name', 'attribute', 'constant', 'assign', 'binop', 'call', 'return']):
            ddg_graph.add_node(node, **original_graph.nodes[node])
    
    # Add edges representing data dependencies
    for node in ddg_graph.nodes():
        for successor in original_graph.successors(node):
            if successor in ddg_graph.nodes():
                edge_data = original_graph.edges.get((node, successor), {})
                edge_data['dependency_type'] = 'data_flow'
                ddg_graph.add_edge(node, successor, **edge_data)
    
    return ddg_graph if len(ddg_graph.nodes()) > 0 else original_graph


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
        
        # Generate visualization using specialized diagram functions
        try:
            # Parse the code first
            graph, parse_metadata = SourceCodeParser.parse(code, language)
            
            # Generate the appropriate diagram type but get the graph data
            if diagram_type == 'ast':
                title = f"Abstract Syntax Tree ({language.title()})"
                # For AST, use the original parsed graph
                final_graph = graph
            elif diagram_type == 'cfg':
                title = f"Control Flow Graph ({language.title()})"
                # Filter for control flow nodes
                final_graph = _create_cfg_graph(graph)
            elif diagram_type == 'ddg':
                title = f"Data Dependency Graph ({language.title()})"
                # Filter for data dependency nodes
                final_graph = _create_ddg_graph(graph)
            else:
                title = f"Abstract Syntax Tree ({language.title()})"
                final_graph = graph
            
            # Convert to D3.js format for SVG rendering
            d3_data = networkx_to_d3(final_graph, parse_metadata)
            
            return jsonify({
                'graph_data': d3_data,
                'title': title,
                'language': language,
                'diagram_type': diagram_type,
                'node_count': len(d3_data['nodes']),
                'edge_count': len(d3_data['links'])
            })
        except Exception as viz_error:
            app.logger.error(f"Visualization generation error: {str(viz_error)}")
            app.logger.error(f"Traceback: {traceback.format_exc()}")
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

    # Render to SVG as bytes (no encoding)
    svg_data = dot.pipe(format='svg')
    
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
            from javalang.tree import MethodDeclaration, ClassDeclaration
            tree = javalang.parse.parse(code)
            stats["functions"] = sum(1 for _, node in tree.filter(MethodDeclaration))
            stats["classes"] = sum(1 for _, node in tree.filter(ClassDeclaration))
    except Exception as e:
        # Optionally, log the error or handle it as needed, but do not add a string to the stats dict
        pass

    return stats


if __name__ == '__main__':
    app.run(debug=True, threaded=True)