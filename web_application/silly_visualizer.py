"""
Group #9 Members: Joshua Ludolf, Samantha Jackson, Matthew Trevino, Jonathon Davis
Class: CSCI 4316 - Software Engineering 1
"""

import ast
import javalang
from typing import List, Tuple, Dict, Any
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64

class ASTNode:
    """
    Represents a node in an Abstract Syntax Tree (AST).

    Attributes:
        type (str): The type of the AST node.
        value (str): The value associated with the AST node.
        children (List[ASTNode]): A list of child AST nodes.
        lineno (int, optional): The line number in the source code where this node is found. Defaults to None.
    """
    def __init__(self, type: str, value: str, children: List['ASTNode'], lineno: int = None):
        self.type = type
        self.value = value
        self.children = children
        self.lineno = lineno

class SourceCodeParser:
    """
    A class used to parse source code and generate a directed graph representation along with metadata.
    Methods
    -------
    parse(source_code: str, language: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        Parses the given source code based on the specified language and returns a directed graph and metadata.
    _parse_python(source_code: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        Parses Python source code and returns a directed graph and metadata.
    _parse_java(source_code: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        Parses Java source code and returns a directed graph and metadata.
    """
    @staticmethod
    def parse(source_code: str, language: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        if language == 'python':
            return SourceCodeParser._parse_python(source_code)
        elif language == 'java':
            return SourceCodeParser._parse_java(source_code)
        else:
            raise ValueError(f"Unsupported language: {language}")

    @staticmethod
    def _parse_python(source_code: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        tree = ast.parse(source_code)
        G = nx.DiGraph()
        metadata = {
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": []
        }

        def add_node(node, parent_id=None):
            node_id = id(node)
            node_type = type(node).__name__
            node_value = ""

            if isinstance(node, ast.FunctionDef):
                node_value = f"Function: {node.name}"
                metadata["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args]
                })
            elif isinstance(node, ast.ClassDef):
                node_value = f"Class: {node.name}"
                metadata["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [base.id for base in node.bases if isinstance(base, ast.Name)]
                })
            elif isinstance(node, ast.Name):
                node_value = f"Name: {node.id}"
                if isinstance(node.ctx, ast.Store):
                    metadata["variables"].append({
                        "name": node.id,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.Import):
                for name in node.names:
                    metadata["imports"].append({
                        "name": name.name,
                        "alias": name.asname,
                        "line": node.lineno
                    })

            G.add_node(node_id, type=node_type, value=node_value, lineno=getattr(node, 'lineno', None))
            if parent_id is not None:
                G.add_edge(parent_id, node_id)

            for child in ast.iter_child_nodes(node):
                add_node(child, node_id)

        add_node(tree)
        return G, metadata

    @staticmethod
    def _parse_java(source_code: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        try:
            tree = javalang.parse.parse(source_code)
            G = nx.DiGraph()
            metadata = {
                "functions": [],
                "classes": [],
                "variables": [],
                "imports": []
            }

            def process_node(node, parent_id=None):
                node_id = id(node)
                node_type = type(node).__name__
                node_value = ""

                # Handle different Java node types
                if isinstance(node, javalang.tree.MethodDeclaration):
                    node_value = f"Method: {node.name}"
                    metadata["functions"].append({
                        "name": node.name,
                        "return_type": str(node.return_type) if node.return_type else "void",
                        "modifiers": list(node.modifiers) if node.modifiers else []
                    })
                elif isinstance(node, javalang.tree.ClassDeclaration):
                    node_value = f"Class: {node.name}"
                    metadata["classes"].append({
                        "name": node.name,
                        "extends": node.extends.name if node.extends else None,
                        "implements": [impl.name for impl in node.implements] if node.implements else []
                    })
                elif isinstance(node, javalang.tree.VariableDeclarator):
                    node_value = f"Variable: {node.name}"
                    metadata["variables"].append({
                        "name": node.name,
                        "type": str(node.type) if hasattr(node, 'type') else None
                    })
                elif isinstance(node, javalang.tree.Import):  # Changed from ImportDeclaration to Import
                    path = '.'.join(node.path)
                    node_value = f"Import: {path}"
                    metadata["imports"].append({
                        "path": path,
                        "static": node.static if hasattr(node, 'static') else False,
                        "wildcard": node.wildcard if hasattr(node, 'wildcard') else False
                    })

                G.add_node(node_id, type=node_type, value=node_value)
                if parent_id is not None:
                    G.add_edge(parent_id, node_id)

                # Process all attributes of the node that might contain child nodes
                for attr_name, attr_value in node.__dict__.items():
                    if isinstance(attr_value, javalang.ast.Node):
                        process_node(attr_value, node_id)
                    elif isinstance(attr_value, list):
                        for item in attr_value:
                            if isinstance(item, javalang.ast.Node):
                                process_node(item, node_id)

            process_node(tree)
            if len(G.nodes()) == 0:
                raise ValueError("No nodes were generated from the Java code")

            return G, metadata

        except Exception as e:
            raise ValueError(f"Failed to parse Java code: {str(e)}")

class DiagramGenerator:
    """
    A class used to generate various types of diagrams for visualizing code structures.
    Methods
    -------
    generate_ast(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure
        Generates an Abstract Syntax Tree (AST) visualization from a directed graph.
    generate_cfg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure
        Generates a Control Flow Graph (CFG) visualization from a directed graph.
    generate_ddg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure
        Generates a Data Dependency Graph (DDG) visualization from a directed graph.
    """
    @staticmethod
    def generate_ast(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
        # Create the figure with a larger size for clarity
        plt.figure(figsize=(15, 10))
    
        # Layout for nodes with a bit more space for readability
        pos = nx.spring_layout(G, k=0.15, iterations=200)

        # Prepare node colors, sizes, and shapes before drawing
        node_color_dict = {}
        node_size_dict = {}
        node_shape_dict = {}

        # Color mapping based on node type
        color_map = {
            'Method': '#FF6347',   # Tomato for Methods/Functions
            'Function': '#FF6347', # Tomato for Functions
            'Class': '#4682B4',    # SteelBlue for Classes
            'Import': '#32CD32',   # LimeGreen for Imports
            'Variable': '#8A2BE2', # BlueViolet for Variables
            'default': '#D3D3D3'    # LightGray for other nodes
        }

        # Iterate through the nodes to assign colors, sizes, and labels
        for node in G.nodes():
            node_type = G.nodes[node].get('type', '')
            node_value = G.nodes[node].get('value', '')

            # Assign colors based on node type
            if 'Method' in node_type or 'Function' in str(node_value):
                node_color_dict[node] = color_map['Method']
                node_size_dict[node] = 2000
                node_shape_dict[node] = 'o'  # Circle shape for methods/functions
            elif 'Class' in node_type:
                node_color_dict[node] = color_map['Class']
                node_size_dict[node] = 2500
                node_shape_dict[node] = 's'  # Square shape for classes
            elif 'Import' in str(node_value):
                node_color_dict[node] = color_map['Import']
                node_size_dict[node] = 1500
                node_shape_dict[node] = 'D'  # Diamond shape for imports
            elif 'Variable' in str(node_value):
                node_color_dict[node] = color_map['Variable']
                node_size_dict[node] = 1500
                node_shape_dict[node] = 'v'  # Triangle shape for variables
            else:
                node_color_dict[node] = color_map['default']
                node_size_dict[node] = 1000
                node_shape_dict[node] = 'o'  # Default shape is circle

        # Draw the graph
        plt.clf()  # Clear the current figure
        plt.figure(figsize=(15, 10))
        plt.title("Abstract Syntax Tree (AST) Visualization", pad=20)
        
        # Use a larger figure and adjust subplot parameters for better visibility
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        # Enable interactive pan and zoom
        plt.rcParams['toolbar'] = 'toolmanager'
        
        # Draw nodes
        for node in G.nodes():
            nx.draw_networkx_nodes(G, pos, 
                                   nodelist=[node], 
                                   node_color=[node_color_dict[node]], 
                                   node_size=[node_size_dict[node]], 
                                   node_shape=node_shape_dict[node])

        # Draw edges (with arrows for direction)
        nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=15, edge_color='gray', width=1)

        # Draw labels on nodes
        labels = {node: (node_value if node_value else node_type)[:30] + 
                  ("..." if len(node_value or node_type) > 30 else "") 
                  for node, node_value in nx.get_node_attributes(G, 'value').items()}
        
        nx.draw_networkx_labels(
            G, pos, labels=labels,
            font_size=10, font_weight='bold', font_color='black',
            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.3')
        )

        # Set plot limits to show entire graph
        x_values = [x for x, y in pos.values()]
        y_values = [y for x, y in pos.values()]
        x_margin = (max(x_values) - min(x_values)) * 0.1
        y_margin = (max(y_values) - min(y_values)) * 0.1
        plt.xlim(min(x_values) - x_margin, max(x_values) + x_margin)
        plt.ylim(min(y_values) - y_margin, max(y_values) + y_margin)
        
        # Remove axis for cleaner look
        plt.axis('off')

        return plt.gcf()

    @staticmethod
    def generate_cfg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
        # Create a new figure with a larger size for clarity
        plt.figure(figsize=(15, 10))
        cfg = nx.DiGraph()

        # Create CFG nodes for functions/methods
        for func in metadata["functions"]:
            func_name = func["name"]
            cfg.add_node(func_name, type="function")
            entry_node = f"{func_name}_entry"
            exit_node = f"{func_name}_exit"

            cfg.add_node(entry_node, type="entry")
            cfg.add_node(exit_node, type="exit")
            cfg.add_edge(entry_node, func_name)
            cfg.add_edge(func_name, exit_node)

        # If no functions are found, add a message node
        if len(cfg.nodes()) == 0:
            cfg.add_node("No functions found", type="message")

        # Define color palette and node shapes
        node_colors = []
        node_sizes = []
        node_shapes = []

        # Color and shape mappings
        color_map = {
            'function': '#FF6347',  # Tomato for function nodes
            'entry': '#32CD32',     # LimeGreen for entry nodes
            'exit': '#FFD700',      # Gold for exit nodes
            'message': '#D3D3D3',   # LightGray for message node
        }

        shape_map = {
            'function': 'o',   # Circle for function nodes
            'entry': 's',      # Square for entry nodes
            'exit': '^',       # Triangle for exit nodes
            'message': 'D',    # Diamond for message node
        }

        # Assign colors, sizes, and shapes based on node type
        for node in cfg.nodes():
            node_type = cfg.nodes[node]['type']
            
            # Assign colors, sizes, and shapes based on node type
            node_colors.append(color_map.get(node_type, '#d62728'))  # Default to red
            node_sizes.append(2000 if node_type == 'function' else 1500)
            node_shapes.append(shape_map.get(node_type, 'o'))  # Default to circle

        # Draw the graph with different node shapes and colors
        pos = nx.spring_layout(cfg, k=0.15, iterations=200)
        plt.clf()  # Clear the current figure
        plt.figure(figsize=(15, 10))
        plt.title("Control Flow Graph (CFG) Visualization", pad=20)
        
        # Use a larger figure and adjust subplot parameters for better visibility
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        # Enable interactive pan and zoom
        plt.rcParams['toolbar'] = 'toolmanager'
        
        for node, shape in zip(cfg.nodes(), node_shapes):
            nx.draw_networkx_nodes(cfg, pos, nodelist=[node], node_color=[node_colors[cfg.nodes[node]]], node_size=[node_sizes[cfg.nodes[node]]], node_shape=shape)

        # Draw edges with arrows for direction
        nx.draw_networkx_edges(cfg, pos, arrowstyle='-|>', arrowsize=15, edge_color='gray', width=1)

        # Draw labels on nodes
        labels = {node: node for node in cfg.nodes()}
        nx.draw_networkx_labels(
            cfg, pos, labels=labels,
            font_size=10, font_weight='bold', font_color='black',
            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.3')
        )
        
        # Set plot limits to show entire graph
        x_values = [x for x, y in pos.values()]
        y_values = [y for x, y in pos.values()]
        x_margin = (max(x_values) - min(x_values)) * 0.1
        y_margin = (max(y_values) - min(y_values)) * 0.1
        plt.xlim(min(x_values) - x_margin, max(x_values) + x_margin)
        plt.ylim(min(y_values) - y_margin, max(y_values) + y_margin)
        
        # Remove axis for cleaner look
        plt.axis('off')

        return plt.gcf()

    @staticmethod
    def generate_ddg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
        # Create the figure with a larger size for clarity
        plt.figure(figsize=(15, 10))
        ddg = nx.DiGraph()

        # Add variables and their dependencies
        var_nodes = set()
        for var in metadata["variables"]:
            var_name = var["name"]
            var_nodes.add(var_name)
            ddg.add_node(var_name, type="variable")

        # Add functions and their variable dependencies
        for func in metadata["functions"]:
            func_name = func["name"]
            ddg.add_node(func_name, type="function")

            # Connect function arguments
            if "args" in func:
                for arg in func["args"]:
                    ddg.add_node(arg, type="argument")
                    ddg.add_edge(arg, func_name)

        # If no nodes were added, add a message node
        if len(ddg.nodes()) == 0:
            ddg.add_node("No data dependencies found", type="message")

        # Define color palette and node shapes
        node_colors = []
        node_sizes = []
        node_shapes = []

        # Color and shape mappings
        color_map = {
            'function': '#FF6347',  # Tomato for function nodes
            'variable': '#32CD32',  # LimeGreen for variable nodes
            'message': '#D3D3D3',   # LightGray for message node
            'argument': '#FF8C00',  # DarkOrange for argument nodes
        }

        shape_map = {
            'function': 'o',    # Circle for function nodes
            'variable': 's',    # Square for variable nodes
            'message': 'D',     # Diamond for message node
            'argument': '^',    # Triangle for argument nodes
        }

        # Assign colors, sizes, and shapes based on node type
        for node in ddg.nodes():
            node_type = ddg.nodes[node]['type']
            
            # Assign colors, sizes, and shapes based on node type
            node_colors.append(color_map.get(node_type, '#d62728'))  # Default to red
            node_sizes.append(2000 if node_type == 'function' else 1500)
            node_shapes.append(shape_map.get(node_type, 'o'))  # Default to circle

        # Draw the graph with different node shapes and colors
        pos = nx.spring_layout(ddg, k=0.15, iterations=200)
        plt.clf()  # Clear the current figure
        plt.figure(figsize=(15, 10))
        plt.title("Data Dependency Graph (DDG) Visualization", pad=20)
        
        # Use a larger figure and adjust subplot parameters for better visibility
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        # Enable interactive pan and zoom
        plt.rcParams['toolbar'] = 'toolmanager'
        
        for node, shape in zip(ddg.nodes(), node_shapes):
            nx.draw_networkx_nodes(ddg, pos, nodelist=[node], node_color=[node_colors[ddg.nodes[node]]], node_size=[node_sizes[ddg.nodes[node]]], node_shape=shape)

        # Draw edges with arrows for direction
        nx.draw_networkx_edges(ddg, pos, arrowstyle='-|>', arrowsize=15, edge_color='gray', width=1)

        # Draw labels on nodes
        labels = {node: node for node in ddg.nodes()}
        nx.draw_networkx_labels(
            ddg, pos, labels=labels,
            font_size=10, font_weight='bold', font_color='black',
            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.3')
        )
        
        # Set plot limits to show entire graph
        x_values = [x for x, y in pos.values()]
        y_values = [y for x, y in pos.values()]
        x_margin = (max(x_values) - min(x_values)) * 0.1
        y_margin = (max(y_values) - min(y_values)) * 0.1
        plt.xlim(min(x_values) - x_margin, max(x_values) + x_margin)
        plt.ylim(min(y_values) - y_margin, max(y_values) + y_margin)
        
        # Remove axis for cleaner look
        plt.axis('off')

        return plt.gcf()

def generate_visualization(code: str, language: str, diagram_type: str) -> Tuple[str, str]:
    """Generate visualization for the given code and diagram type."""
    try:
        # Parse the code
        G, metadata = SourceCodeParser.parse(code, language)

        # Generate the appropriate diagram
        if diagram_type == 'ast':
            fig = DiagramGenerator.generate_ast(G, metadata)
            title = "Abstract Syntax Tree (AST)"
        elif diagram_type == 'cfg':
            fig = DiagramGenerator.generate_cfg(G, metadata)
            title = "Control Flow Graph (CFG)"
        elif diagram_type == 'ddg':
            fig = DiagramGenerator.generate_ddg(G, metadata)
            title = "Data Dependency Graph (DDG)"
        else:
            raise ValueError(f"Unknown diagram type: {diagram_type}")

        # Convert plot to base64 string
        img_data = io.BytesIO()
        fig.savefig(img_data, format='png', bbox_inches='tight')
        img_data.seek(0)
        plt.close(fig)

        graph_url = base64.b64encode(img_data.getvalue()).decode()
        return f"data:image/png;base64,{graph_url}", title

    except Exception as e:
        plt.close('all')  # Clean up any open figures
        raise ValueError(f"Visualization failed: {str(e)}")
