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

        # Define color palette and node shapes
        node_colors = []
        node_sizes = []
        node_shapes = []
        labels = {}

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
                node_colors.append(color_map['Method'])
                node_sizes.append(2000)
                node_shapes.append('o')  # Circle shape for methods/functions
            elif 'Class' in node_type:
                node_colors.append(color_map['Class'])
                node_sizes.append(2500)
                node_shapes.append('s')  # Square shape for classes
            elif 'Import' in str(node_value):
                node_colors.append(color_map['Import'])
                node_sizes.append(1500)
                node_shapes.append('D')  # Diamond shape for imports
            elif 'Variable' in str(node_value):
                node_colors.append(color_map['Variable'])
                node_sizes.append(1500)
                node_shapes.append('v')  # Triangle shape for variables
            else:
                node_colors.append(color_map['default'])
                node_sizes.append(1000)
                node_shapes.append('o')  # Default shape is circle

            # Create truncated labels if needed
            label = node_value if node_value else node_type
            if len(label) > 30:
                label = label[:27] + "..."
            labels[node] = label

        # Draw the graph
        for node, shape in zip(G.nodes(), node_shapes):
            nx.draw_networkx_nodes(G, pos, nodelist=[node], node_color=[node_colors[G.nodes[node]]], node_size=[node_sizes[G.nodes[node]]], node_shape=shape)

        # Draw edges (with arrows for direction)
        nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=15, edge_color='gray', width=1)

        # Draw labels on nodes
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_weight='bold', font_color='white')

        # Title for the plot
        plt.title("Abstract Syntax Tree (AST) Visualization", pad=20)

        return plt.gcf()

    @staticmethod
    def generate_cfg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
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

        # If no functions were found, add a message node
        if len(cfg.nodes()) == 0:
            cfg.add_node("No functions found", type="message")

        # Draw CFG
        pos = nx.spring_layout(cfg, k=2)
        node_colors = []
        node_sizes = []

        for node in cfg.nodes():
            if cfg.nodes[node]['type'] == 'function':
                node_colors.append('#1f77b4')
                node_sizes.append(2000)
            elif cfg.nodes[node]['type'] == 'entry':
                node_colors.append('#2ca02c')
                node_sizes.append(1500)
            elif cfg.nodes[node]['type'] == 'message':
                node_colors.append('#d62728')
                node_sizes.append(2000)
            else:  # exit nodes
                node_colors.append('#d62728')
                node_sizes.append(1500)

        nx.draw(cfg, pos,
                node_color=node_colors,
                node_size=node_sizes,
                with_labels=True,
                font_size=10,
                font_weight='bold',
                arrows=True,
                edge_color='gray',
                width=1,
                arrowsize=10)

        plt.title("Control Flow Graph (CFG) Visualization", pad=20)
        return plt.gcf()

    @staticmethod
    def generate_ddg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
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

        # Draw DDG
        pos = nx.spring_layout(ddg, k=2)
        node_colors = []
        node_sizes = []

        for node in ddg.nodes():
            node_type = ddg.nodes[node]['type']
            if node_type == 'function':
                node_colors.append('#1f77b4')
                node_sizes.append(2000)
            elif node_type == 'variable':
                node_colors.append('#2ca02c')
                node_sizes.append(1500)
            elif node_type == 'message':
                node_colors.append('#d62728')
                node_sizes.append(2000)
            else:  # arguments
                node_colors.append('#ff7f0e')
                node_sizes.append(1500)

        nx.draw(ddg, pos,
                node_color=node_colors,
                node_size=node_sizes,
                with_labels=True,
                font_size=10,
                font_weight='bold',
                arrows=True,
                edge_color='gray',
                width=1,
                arrowsize=10)

        plt.title("Data Dependency Graph (DDG) Visualization", pad=20)
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