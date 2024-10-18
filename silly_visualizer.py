"""
Group #9 Members: Joshua Ludolf, Samantha Jackson, Matthew Trevino, Jonathon Davis
Class: CSCI 4316 - Software Engineering 1
"""

import ast
import javalang
from typing import List, Tuple
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, Any


class ASTNode:
    def __init__(self, type: str, value: str, children: List['ASTNode'], lineno: int = None):
        self.type = type
        self.value = value
        self.children = children
        self.lineno = lineno


class SourceCodeParser:
    @staticmethod
    def parse(source_code: str, language: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Parse source code and return both AST and metadata."""
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

            # Extract node information
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
            elif isinstance(node, ast.Import):
                for name in node.names:
                    metadata["imports"].append({
                        "name": name.name,
                        "alias": name.asname,
                        "line": node.lineno
                    })

            # Add node to graph
            G.add_node(node_id,
                       type=node_type,
                       value=node_value,
                       lineno=getattr(node, 'lineno', None))

            if parent_id is not None:
                G.add_edge(parent_id, node_id)

            # Process children
            for child in ast.iter_child_nodes(node):
                add_node(child, node_id)

        add_node(tree)
        return G, metadata

    @staticmethod
    def _parse_java(source_code: str) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        tree = javalang.parse.parse(source_code)
        G = nx.DiGraph()
        metadata = {
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": []
        }

        def add_node(node, parent_id=None):
            node_id = id(node)

            # Extract node information
            node_type = type(node).__name__
            node_value = ""

            if isinstance(node, javalang.tree.MethodDeclaration):
                node_value = f"Method: {node.name}"
                metadata["functions"].append({
                    "name": node.name,
                    "return_type": str(node.return_type),
                    "modifiers": list(node.modifiers)
                })
            elif isinstance(node, javalang.tree.ClassDeclaration):
                node_value = f"Class: {node.name}"
                metadata["classes"].append({
                    "name": node.name,
                    "extends": node.extends.name if node.extends else None,
                    "implements": [impl.name for impl in node.implements] if node.implements else []
                })
            elif isinstance(node, javalang.tree.ImportDeclaration):
                metadata["imports"].append({
                    "path": node.path,
                    "static": node.static,
                    "wildcard": node.wildcard
                })

            # Add node to graph
            G.add_node(node_id, type=node_type, value=node_value)

            if parent_id is not None:
                G.add_edge(parent_id, node_id)

            # Process children
            for child in node.children:
                if isinstance(child, javalang.ast.Node):
                    add_node(child, node_id)
                elif isinstance(child, list):
                    for item in child:
                        if isinstance(item, javalang.ast.Node):
                            add_node(item, node_id)

        add_node(tree)
        return G, metadata


class DiagramGenerator:
    @staticmethod
    def generate_ast(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
        plt.figure(figsize=(15, 10))
        pos = nx.spring_layout(G, k=1, iterations=50)

        # Draw nodes with different colors based on type
        node_colors = []
        node_sizes = []
        labels = {}

        for node in G.nodes():
            node_type = G.nodes[node]['type']
            node_value = G.nodes[node]['value']

            if 'Function' in str(node_type) or 'Method' in str(node_type):
                node_colors.append('#ff7f0e')  # Orange for functions
                node_sizes.append(2000)
            elif 'Class' in str(node_type):
                node_colors.append('#1f77b4')  # Blue for classes
                node_sizes.append(2500)
            elif 'Import' in str(node_type):
                node_colors.append('#2ca02c')  # Green for imports
                node_sizes.append(1500)
            else:
                node_colors.append('#d62728')  # Red for other nodes
                node_sizes.append(1000)

            # Create meaningful labels
            labels[node] = f"{node_type}\n{node_value}" if node_value else node_type

        # Draw the graph
        nx.draw(G, pos, node_color=node_colors, node_size=node_sizes,
                labels=labels, with_labels=True, font_size=8,
                font_weight='bold', arrows=True)

        # Add title and legend
        plt.title("Abstract Syntax Tree (AST) Visualization", pad=20)

        return plt.gcf()

    @staticmethod
    def generate_cfg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
        plt.figure(figsize=(15, 10))

        # Create a control flow graph from the AST
        cfg = nx.DiGraph()

        # Add function nodes
        for func in metadata["functions"]:
            cfg.add_node(func["name"], type="function")

            # Add entry and exit nodes for each function
            entry_node = f"{func['name']}_entry"
            exit_node = f"{func['name']}_exit"
            cfg.add_node(entry_node, type="entry")
            cfg.add_node(exit_node, type="exit")
            cfg.add_edge(entry_node, func["name"])
            cfg.add_edge(func["name"], exit_node)

        # Draw the CFG
        pos = nx.spring_layout(cfg)
        node_colors = ['#1f77b4' if cfg.nodes[node]['type'] == 'function' else
                       '#2ca02c' if cfg.nodes[node]['type'] == 'entry' else
                       '#d62728' for node in cfg.nodes()]

        nx.draw(cfg, pos, node_color=node_colors, with_labels=True,
                node_size=2000, font_size=10, font_weight='bold',
                arrows=True)

        plt.title("Control Flow Graph (CFG) Visualization", pad=20)
        return plt.gcf()

    @staticmethod
    def generate_ddg(G: nx.DiGraph, metadata: Dict[str, Any]) -> plt.Figure:
        plt.figure(figsize=(15, 10))

        # Create a data dependency graph
        ddg = nx.DiGraph()

        # Add variable nodes and their dependencies
        for var in metadata.get("variables", []):
            ddg.add_node(var["name"], type="variable")

        # Add function nodes and their dependencies
        for func in metadata["functions"]:
            ddg.add_node(func["name"], type="function")
            # Add edges for function arguments
            for arg in func.get("args", []):
                ddg.add_node(arg, type="argument")
                ddg.add_edge(arg, func["name"])

        # Draw the DDG
        pos = nx.spring_layout(ddg)
        node_colors = ['#1f77b4' if ddg.nodes[node]['type'] == 'function' else
                       '#2ca02c' if ddg.nodes[node]['type'] == 'variable' else
                       '#d62728' for node in ddg.nodes()]

        nx.draw(ddg, pos, node_color=node_colors, with_labels=True,
                node_size=2000, font_size=10, font_weight='bold',
                arrows=True)

        plt.title("Data Dependency Graph (DDG) Visualization", pad=20)
        return plt.gcf()


def generate_visualization(code: str, language: str, diagram_type: str) -> Tuple[str, str]:
    """Generate visualization for the given code and diagram type."""
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
