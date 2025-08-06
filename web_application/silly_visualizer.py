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
import hashlib
import numpy as np

class ASTNode:
    """
    Represents a node in an Abstract Syntax Tree (AST).

    Attributes:
        type (str): The type of the AST node.
        value (str): The value associated with the AST node.
        children (List[ASTNode]): A list of child AST nodes.
        lineno (int, optional): The line number in the source code where this node is found. Defaults to None.
    """
    def __init__(self, type: str, value: str, children: List['ASTNode'], lineno: int | None = None):
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
    def parse(code: str, language: str, max_depth: int = 10) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Parse code and generate a networkx graph representation with enhanced error handling and depth limiting.
        
        Args:
            code (str): Source code to parse
            language (str): Programming language ('python' or 'java')
            max_depth (int): Maximum recursion depth to prevent infinite recursion
        
        Returns:
            Tuple[nx.DiGraph, Dict[str, Any]]: Parsed graph and metadata
        """
        G = nx.DiGraph()
        metadata: Dict[str, Any] = {
            'parse_error': None,
            'total_nodes': 0,
            'language': language,
            'max_depth_reached': False
        }

        # Preprocessing: Remove BOM and normalize line endings
        code = code.replace('\ufeff', '').replace('\r\n', '\n')

        try:
            if language == 'python':
                # More robust Python parsing
                try:
                    tree = ast.parse(code)
                except SyntaxError as e:
                    # Attempt partial parsing for incomplete code
                    try:
                        tree = ast.parse(code, mode='eval')
                    except Exception:
                        # Create an error graph if parsing completely fails
                        G.add_node("Python Parsing Error", 
                                   type="Error", 
                                   value=f"Line {e.lineno}: {e.text}")
                        metadata['parse_error'] = str(e)
                        return G, metadata
                
                def add_node(node, parent=None, depth: int = 0, visited: set | None = None):
                    # Prevent infinite recursion
                    if visited is None:
                        visited = set()
                    
                    if depth > max_depth:
                        metadata['max_depth_reached'] = True
                        return
                    
                    # Prevent revisiting nodes to break potential cycles
                    node_id = id(node)
                    if node_id in visited:
                        return
                    visited.add(node_id)
                    
                    node_type = node.__class__.__name__
                    
                    # More comprehensive node value extraction
                    node_value = ""
                    try:
                        if isinstance(node, ast.Name):
                            node_value = node.id
                        elif isinstance(node, ast.FunctionDef):
                            node_value = node.name
                        elif isinstance(node, ast.ClassDef):
                            node_value = node.name
                        elif isinstance(node, ast.Attribute):
                            node_value = node.attr
                        elif isinstance(node, ast.Call):
                            node_value = getattr(node.func, 'id', str(node.func))
                        else:
                            node_value = str(node)
                    except Exception:
                        node_value = str(node)
                    
                    # Add node to graph with error handling
                    try:
                        G.add_node(node_id, type=node_type, value=node_value)
                        
                        # Connect to parent if exists
                        if parent is not None:
                            G.add_edge(id(parent), node_id)
                        
                        # Recursively process child nodes
                        child_nodes = list(ast.iter_child_nodes(node))
                        for child in child_nodes:
                            add_node(child, node, depth + 1, visited)
                    except Exception as child_error:
                        print(f"Error processing child node: {child_error}")

                # Start parsing from the root
                add_node(tree)
                
                metadata['total_nodes'] = len(G.nodes())

            elif language == 'java':
                # More robust Java parsing
                try:
                    tree = javalang.parse.parse(code)
                except Exception as e:
                    # Create an error graph if parsing fails
                    G.add_node("Java Parsing Error", 
                               type="Error", 
                               value=str(e))
                    metadata['parse_error'] = str(e)
                    return G, metadata
                
                def add_java_node(node, parent=None, depth: int = 0, visited: set | None = None):
                    # Prevent infinite recursion
                    if visited is None:
                        visited = set()
                    
                    if depth > max_depth:
                        metadata['max_depth_reached'] = True
                        return
                    
                    # Prevent revisiting nodes to break potential cycles
                    node_id = id(node)
                    if node_id in visited:
                        return
                    visited.add(node_id)
                    
                    node_type = node.__class__.__name__
                    
                    # More comprehensive node value extraction
                    node_value = ""
                    try:
                        if hasattr(node, 'name'):
                            node_value = node.name
                        elif hasattr(node, 'type'):
                            node_value = str(node.type)
                        else:
                            node_value = str(node)
                    except Exception:
                        node_value = str(node)
                    
                    # Add node to graph with error handling
                    try:
                        G.add_node(node_id, type=node_type, value=node_value)
                        
                        # Connect to parent if exists
                        if parent is not None:
                            G.add_edge(id(parent), node_id)
                        
                        # Recursively process child nodes
                        for _, child in node:
                            if isinstance(child, (list, tuple)):
                                for sub_child in child:
                                    if hasattr(sub_child, '__class__'):
                                        add_java_node(sub_child, node, depth + 1, visited)
                            elif hasattr(child, '__class__'):
                                add_java_node(child, node, depth + 1, visited)
                    except Exception as child_error:
                        print(f"Error processing Java child node: {child_error}")
                
                # Start parsing from the root
                try:
                    # Try to access types attribute
                    for type_declaration in tree.types:  # type: ignore
                        add_java_node(type_declaration)
                except AttributeError:
                    # Fallback if tree structure is different
                    add_java_node(tree)
                
                metadata['total_nodes'] = len(G.nodes())

            else:
                raise ValueError(f"Unsupported language: {language}")

            # Ensure graph is not empty
            if len(G.nodes()) == 0:
                G.add_node("Empty Graph", type="Placeholder", value="No nodes found")

            return G, metadata

        except Exception as e:
            # Comprehensive fallback for any unexpected errors
            G.add_node("Parsing Error", type="Error", value=str(e))
            metadata['parse_error'] = str(e)
            return G, metadata

class DiagramGenerator:
    @staticmethod
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
            
            # Default fallback
            'default': '#95A5A6'           # Light gray for unrecognized types
        }
        
        # Java-specific node types (additional mapping)
        java_color_map = {
            'ClassDeclaration': '#3498DB',     # Blue for Java classes
            'MethodDeclaration': '#2ECC71',    # Green for Java methods
            'FieldDeclaration': '#F39C12',     # Orange for Java fields
            'ConstructorDeclaration': '#E74C3C', # Red for constructors
            'InterfaceDeclaration': '#9B59B6'  # Purple for interfaces
        }
        
        # Merge mappings, with Java types taking precedence if needed
        color_map.update(java_color_map)
        
        # Return color, defaulting to light gray if not found
        return color_map.get(node_type, color_map['default'])

    @staticmethod
    def generate_ast(G: nx.DiGraph, metadata: Dict[str, Any]) -> str:
        """Generate AST with hierarchical layout."""
        try:
            # Ensure graph is not empty
            if len(G.nodes()) == 0:
                G.add_node("Empty AST", type="placeholder", value="No nodes found")
            
            # Dynamic scaling based on node count for better readability
            node_count = len(G.nodes())
            
            # For very large graphs, filter to show only the most important nodes
            if node_count > 150:
                filtered_graph = nx.DiGraph()
                important_types = ['Module', 'ClassDef', 'FunctionDef', 'ClassDeclaration', 'MethodDeclaration']
                
                # Add important nodes first
                for node in G.nodes():
                    node_type = G.nodes[node].get('type', '')
                    if any(imp_type in node_type for imp_type in important_types):
                        filtered_graph.add_node(node, **G.nodes[node])
                
                # Add their direct connections
                for node in list(filtered_graph.nodes()):
                    for successor in G.successors(node):
                        if successor in G.nodes():
                            filtered_graph.add_node(successor, **G.nodes[successor])
                            filtered_graph.add_edge(node, successor, **G.edges.get((node, successor), {}))
                    for predecessor in G.predecessors(node):
                        if predecessor in G.nodes():
                            filtered_graph.add_node(predecessor, **G.nodes[predecessor])
                            filtered_graph.add_edge(predecessor, node, **G.edges.get((predecessor, node), {}))
                
                G = filtered_graph
                node_count = len(G.nodes())
                print(f"Filtered large AST from {len(list(G.nodes()))} to {node_count} nodes for better readability")
            if node_count > 100:
                k_value, scale_value, iterations = 25.0, 12, 800
                min_dist = 3.0
            elif node_count > 50:
                k_value, scale_value, iterations = 20.0, 10, 600  
                min_dist = 2.5
            else:
                k_value, scale_value, iterations = 15.0, 8, 500
                min_dist = 2.0
            
            # Create hierarchical layout for AST with maximum spacing
            try:
                # Use dynamic spacing parameters based on graph size
                pos = nx.spring_layout(G, k=k_value, iterations=iterations, scale=scale_value)
            except Exception as e:
                print(f"Spring layout failed: {e}")
                # Fallback to grid-based layout for maximum separation
                try:
                    import math
                    nodes = list(G.nodes())
                    grid_size = int(math.ceil(math.sqrt(len(nodes))))
                    pos = {}
                    for i, node in enumerate(nodes):
                        x = (i % grid_size) * 2.0  # 2.0 spacing between grid positions
                        y = (i // grid_size) * 2.0
                        pos[node] = [x, y]
                except Exception:
                    pos = {node: [i*3.0, 0] for i, node in enumerate(G.nodes())}
            
            # Adjust y-coordinates based on node depth for tree structure
            root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            for root in root_nodes:
                try:
                    bfs_edges = list(nx.bfs_edges(G, root))
                    levels = {root: 0}
                    for u, v in bfs_edges:
                        levels[v] = levels[u] + 1
                    
                    # Normalize depths with much larger vertical spacing
                    max_depth = max(levels.values()) if levels else 0
                    if max_depth > 0:
                        for node in levels:
                            if node in pos:
                                pos[node][1] = (max_depth - levels[node]) * 3.0  # 3x vertical spacing
                except Exception:
                    pass  # Continue with spring layout if hierarchy fails

            plt.figure(figsize=(30, 24), facecolor='white')  # Much larger figure size
            
            # Convert pos to mutable dict and apply aggressive node separation
            pos = dict(pos)
            # Use dynamic minimum distance based on graph size
            # Apply multiple iterations of separation to really spread nodes out
            for iteration in range(3):  # Multiple passes for better separation
                for node1 in list(pos.keys()):
                    for node2 in list(pos.keys()):
                        if node1 != node2:
                            x1, y1 = pos[node1]
                            x2, y2 = pos[node2]
                            distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                            if distance < min_dist and distance > 0:
                                # Move nodes apart more aggressively
                                angle = np.arctan2(y2-y1, x2-x1)
                                separation = min_dist * 1.2  # 20% extra separation
                                pos[node2] = [x1 + separation * np.cos(angle), 
                                             y1 + separation * np.sin(angle)]
            
            # Draw edges as tree branches (straight lines)
            nx.draw_networkx_edges(G, pos, edge_color='#2c3e50', 
                                 arrows=True, arrowsize=15,
                                 connectionstyle='arc3,rad=0',
                                 width=1.5)

            # Draw nodes with type-based colors and larger sizes for better readability
            node_colors = []
            node_sizes = []
            for node in G.nodes():
                node_type = G.nodes[node].get('type', 'default')
                if node_type in ['Module', 'ClassDef', 'ClassDeclaration']:
                    node_sizes.append(3000)  # Increased from 2000
                elif node_type in ['FunctionDef', 'MethodDeclaration']:
                    node_sizes.append(2500)  # Increased from 1500
                else:
                    node_sizes.append(2000)  # Increased from 1000
                node_colors.append(DiagramGenerator._get_node_color(node_type))

            # Use circular nodes for AST - draw nodes individually
            for i, node in enumerate(G.nodes()):
                nx.draw_networkx_nodes(G, pos, 
                                     nodelist=[node],
                                     node_color=node_colors[i] if i < len(node_colors) else '#95A5A6', 
                                     node_size=node_sizes[i] if i < len(node_sizes) else 1000, 
                                     node_shape='o',
                                     edgecolors='black', linewidths=1)

            # Add labels with larger font for better readability
            labels = {node: G.nodes[node].get('value', '') for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=11, font_weight='bold')

            plt.axis('off')
            
            # Save to buffer with increased padding for better spacing
            buffer = io.BytesIO()
            plt.savefig(buffer, format='svg', bbox_inches='tight', 
                       dpi=150, pad_inches=1.5, facecolor='white')  # Increased padding
            plt.close()
            
            svg_data = buffer.getvalue().decode('utf-8')
            return base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        except Exception as e:
            print(f"Error generating AST visualization: {str(e)}")
            return ""

    @staticmethod
    def generate_cfg(G: nx.DiGraph, metadata: Dict[str, Any]) -> str:
        """Generate Control Flow Graph with flowchart-style layout and distinct styling."""
        try:
            # Ensure graph is not empty
            if len(G.nodes()) == 0:
                G.add_node("Empty CFG", type="placeholder", value="No control flow found")
            
            # Create a simplified CFG-focused graph
            cfg_graph = nx.DiGraph()
            
            # Filter and transform nodes for control flow emphasis
            control_flow_nodes = []
            for node in G.nodes():
                node_type = G.nodes[node].get('type', '').lower()
                node_value = G.nodes[node].get('value', '')
                
                # Focus on control flow elements
                if any(cf in node_type for cf in ['if', 'for', 'while', 'functiondef', 'module', 'return']):
                    control_flow_nodes.append(node)
                    cfg_graph.add_node(node, **G.nodes[node])
            
            # Add edges between control flow nodes
            for node in control_flow_nodes:
                for successor in G.successors(node):
                    if successor in control_flow_nodes:
                        cfg_graph.add_edge(node, successor, **G.edges[node, successor])
            
            # Use the CFG graph for layout
            target_graph = cfg_graph if len(cfg_graph.nodes()) > 0 else G
            
            # Dynamic scaling for CFG based on node count
            node_count = len(target_graph.nodes())
            if node_count > 80:
                k_value, scale_value, iterations = 30.0, 12, 1000
                min_dist = 3.5
            elif node_count > 40:
                k_value, scale_value, iterations = 25.0, 10, 800  
                min_dist = 3.0
            else:
                k_value, scale_value, iterations = 20.0, 8, 600
                min_dist = 2.5
            
            # Use layout better suited for control flow with dynamic spacing
            try:
                pos = nx.kamada_kawai_layout(target_graph, scale=scale_value)
            except ImportError:
                try:
                    # Hierarchical layout for control flow with dynamic spacing
                    pos = nx.spring_layout(target_graph, k=k_value, iterations=iterations, scale=scale_value)
                except Exception:
                    # Force-based grid layout as fallback
                    import math
                    nodes = list(target_graph.nodes())
                    grid_size = int(math.ceil(math.sqrt(len(nodes))))
                    pos = {}
                    spacing = min_dist * 2  # Grid spacing based on minimum distance
                    for i, node in enumerate(nodes):
                        x = (i % grid_size) * spacing
                        y = (i // grid_size) * spacing
                        pos[node] = [x, y]
            
            # Convert to mutable dict and add dynamic node separation
            pos = dict(pos)
            # Apply multiple aggressive separation passes
            for iteration in range(4):  # Even more passes for CFG
                for node1 in list(pos.keys()):
                    for node2 in list(pos.keys()):
                        if node1 != node2:
                            x1, y1 = pos[node1]
                            x2, y2 = pos[node2]
                            distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                            if distance < min_dist and distance > 0:
                                angle = np.arctan2(y2-y1, x2-x1)
                                separation = min_dist * 1.5  # 50% extra separation
                                pos[node2] = [x1 + separation * np.cos(angle), 
                                             y1 + separation * np.sin(angle)]
            
            plt.figure(figsize=(32, 24), facecolor='white')  # Maximum size for CFG
            plt.suptitle('Control Flow Graph', fontsize=16, fontweight='bold', color='#2c3e50')
            
            # Draw different types of edges with very distinct styles
            edge_styles = {
                'condition': ('#e74c3c', '--', 3),  # Thick red dashed for conditions
                'loop': ('#3498db', ':', 4),        # Thick blue dotted for loops  
                'normal': ('#2c3e50', '-', 2)       # Medium dark solid for normal flow
            }
            
            for (u, v) in target_graph.edges():
                edge_type = target_graph.edges[u, v].get('type', '').lower()
                u_type = str(target_graph.nodes[u].get('type', '')).lower()
                
                if 'if' in u_type or 'condition' in edge_type:
                    color, style, width = edge_styles['condition']
                elif any(loop_word in u_type for loop_word in ['for', 'while']) or 'loop' in edge_type:
                    color, style, width = edge_styles['loop']
                else:
                    color, style, width = edge_styles['normal']
                
                nx.draw_networkx_edges(target_graph, pos, edgelist=[(u, v)],
                                     edge_color=color,
                                     style=style,
                                     width=width,
                                     arrows=True,
                                     arrowsize=25,
                                     arrowstyle='->',
                                     connectionstyle='arc3,rad=0.15')

            # Draw nodes with very distinct shapes for control flow
            condition_nodes = []
            loop_nodes = []
            function_nodes = []
            regular_nodes = []
            
            for node in target_graph.nodes():
                node_type = target_graph.nodes[node].get('type', '').lower()
                if 'if' in node_type:
                    condition_nodes.append(node)
                elif any(loop in node_type for loop in ['for', 'while']):
                    loop_nodes.append(node)
                elif 'function' in node_type or 'module' in node_type:
                    function_nodes.append(node)
                else:
                    regular_nodes.append(node)

            # Draw condition nodes as extra large yellow diamonds
            if condition_nodes:
                nx.draw_networkx_nodes(target_graph, pos, nodelist=condition_nodes,
                                     node_color='#f1c40f', node_size=4000,  # Increased from 2500
                                     node_shape='D', edgecolors='#f39c12', linewidths=3)
            
            # Draw loop nodes as extra large blue squares
            if loop_nodes:
                nx.draw_networkx_nodes(target_graph, pos, nodelist=loop_nodes,
                                     node_color='#3498db', node_size=3500,  # Increased from 2200
                                     node_shape='s', edgecolors='#2980b9', linewidths=3)
            
            # Draw function nodes as extra large green circles
            if function_nodes:
                nx.draw_networkx_nodes(target_graph, pos, nodelist=function_nodes,
                                     node_color='#2ecc71', node_size=3200,  # Increased from 2000
                                     node_shape='o', edgecolors='#27ae60', linewidths=3)
            
            # Draw regular nodes as larger gray circles
            if regular_nodes:
                nx.draw_networkx_nodes(target_graph, pos, nodelist=regular_nodes,
                                     node_color='#bdc3c7', node_size=2400,  # Increased from 1400
                                     node_shape='o', edgecolors='#95a5a6', linewidths=2)

            # Add labels with background for better readability and larger font
            labels = {}
            for node in target_graph.nodes():
                value = target_graph.nodes[node].get('value', str(node))
                if len(str(value)) > 20:  # Allow longer labels
                    value = str(value)[:17] + "..."
                labels[node] = value
                
            nx.draw_networkx_labels(target_graph, pos, labels, font_size=12, font_weight='bold',
                                  bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                                           edgecolor='gray', alpha=0.95, linewidth=1.5))

            plt.axis('off')
            plt.tight_layout()
            
            # Save to buffer with extra padding
            buffer = io.BytesIO()
            plt.savefig(buffer, format='svg', bbox_inches='tight', dpi=150, 
                       pad_inches=2.0, facecolor='white')  # More padding for CFG
            plt.close()
            
            svg_data = buffer.getvalue().decode('utf-8')
            return base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        except Exception as e:
            print(f"Error generating CFG visualization: {str(e)}")
            return ""

    @staticmethod
    def generate_ddg(G: nx.DiGraph, metadata: Dict[str, Any]) -> str:
        """Generate Data Dependency Graph with emphasis on data flow and variable relationships."""
        try:
            # Ensure graph is not empty
            if len(G.nodes()) == 0:
                G.add_node("Empty DDG", type="placeholder", value="No data dependencies found")
            
            # Create a data-focused graph
            ddg_graph = nx.DiGraph()
            
            # Filter nodes for data dependency focus
            data_nodes = []
            for node in G.nodes():
                node_type = G.nodes[node].get('type', '').lower()
                node_value = str(G.nodes[node].get('value', '')).lower()
                
                # Focus on data-related elements: variables, assignments, operations
                if any(data_type in node_type for data_type in ['name', 'attribute', 'constant', 'assign', 'binop', 'call', 'return']):
                    data_nodes.append(node)
                    ddg_graph.add_node(node, **G.nodes[node])
            
            # Add edges representing data dependencies
            for node in data_nodes:
                for successor in G.successors(node):
                    if successor in data_nodes:
                        ddg_graph.add_edge(node, successor, dependency_type='data_flow')
            
            # Use the DDG graph for layout
            target_graph = ddg_graph if len(ddg_graph.nodes()) > 0 else G
            
            # Dynamic scaling for DDG based on node count (most aggressive)
            node_count = len(target_graph.nodes())
            if node_count > 60:
                k_value, scale_value, iterations = 35.0, 15, 1200
                min_dist = 4.0
            elif node_count > 30:
                k_value, scale_value, iterations = 30.0, 12, 1000  
                min_dist = 3.5
            else:
                k_value, scale_value, iterations = 25.0, 10, 800
                min_dist = 3.0
            
            # Use radial/circular layout to emphasize data relationships with dynamic spacing
            try:
                pos = nx.circular_layout(target_graph, scale=scale_value)
            except Exception:
                pos = nx.spring_layout(target_graph, k=k_value, iterations=iterations, scale=scale_value)
            
            # Convert to mutable dict and add maximum node separation for DDG
            pos = dict(pos)
            # Apply most aggressive separation passes
            for iteration in range(5):  # Maximum passes for DDG
                for node1 in list(pos.keys()):
                    for node2 in list(pos.keys()):
                        if node1 != node2:
                            x1, y1 = pos[node1]
                            x2, y2 = pos[node2]
                            distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                            if distance < min_dist and distance > 0:
                                angle = np.arctan2(y2-y1, x2-x1)
                                separation = min_dist * 1.8  # 80% extra separation
                                pos[node2] = [x1 + separation * np.cos(angle), 
                                             y1 + separation * np.sin(angle)]
            
            plt.figure(figsize=(36, 28), facecolor='#f8f9fa')  # Maximum figure for DDG
            plt.suptitle('Data Dependency Graph', fontsize=16, fontweight='bold', color='#8e44ad')
            
            # Analyze nodes for data types with more granular classification
            variable_nodes = []
            operation_nodes = []
            assignment_nodes = []
            constant_nodes = []
            function_call_nodes = []
            
            for node in target_graph.nodes():
                node_type = target_graph.nodes[node].get('type', '').lower()
                node_value = str(target_graph.nodes[node].get('value', '')).lower()
                
                if 'name' in node_type and 'assign' not in node_type:
                    variable_nodes.append(node)
                elif 'constant' in node_type or node_value.isdigit():
                    constant_nodes.append(node)
                elif 'assign' in node_type:
                    assignment_nodes.append(node)
                elif 'call' in node_type:
                    function_call_nodes.append(node)
                elif any(op_type in node_type for op_type in ['binop', 'unaryop', 'compare']):
                    operation_nodes.append(node)
                else:
                    operation_nodes.append(node)  # Default classification
            
            # Draw edges with strong emphasis on data flow (thick purple arrows)
            for (u, v) in target_graph.edges():
                nx.draw_networkx_edges(target_graph, pos, edgelist=[(u, v)],
                                     edge_color='#8e44ad',
                                     arrows=True,
                                     arrowsize=30,
                                     arrowstyle='->',
                                     connectionstyle='arc3,rad=0.4',
                                     width=4,
                                     alpha=0.7)
            
            # Draw variable nodes as extra large red hexagons
            if variable_nodes:
                nx.draw_networkx_nodes(target_graph, pos,
                                     nodelist=variable_nodes,
                                     node_color='#e74c3c',
                                     node_size=3600,  # Increased from 2400
                                     node_shape='h',  # hexagon for variables
                                     edgecolors='#c0392b',
                                     linewidths=4)
            
            # Draw constant nodes as larger orange triangles
            if constant_nodes:
                nx.draw_networkx_nodes(target_graph, pos,
                                     nodelist=constant_nodes,
                                     node_color='#f39c12',
                                     node_size=2800,  # Increased from 1600
                                     node_shape='^',  # triangle for constants
                                     edgecolors='#e67e22',
                                     linewidths=3)
            
            # Draw assignment nodes as extra large blue diamonds
            if assignment_nodes:
                nx.draw_networkx_nodes(target_graph, pos,
                                     nodelist=assignment_nodes,
                                     node_color='#3498db',
                                     node_size=3400,  # Increased from 2200
                                     node_shape='D',  # diamond for assignments
                                     edgecolors='#2980b9',
                                     linewidths=4)
            
            # Draw function call nodes as large green pentagons (star shape)
            if function_call_nodes:
                nx.draw_networkx_nodes(target_graph, pos,
                                     nodelist=function_call_nodes,
                                     node_color='#2ecc71',
                                     node_size=3200,  # Increased from 2000
                                     node_shape='*',  # star for function calls
                                     edgecolors='#27ae60',
                                     linewidths=3)
            
            # Draw operation nodes as large purple squares
            if operation_nodes:
                nx.draw_networkx_nodes(target_graph, pos,
                                     nodelist=operation_nodes,
                                     node_color='#9b59b6',
                                     node_size=3000,  # Increased from 1800
                                     node_shape='s',  # square for operations
                                     edgecolors='#8e44ad',
                                     linewidths=3)
            
            # Add labels with better contrast and data-focused styling
            labels = {}
            for node in target_graph.nodes():
                value = target_graph.nodes[node].get('value', str(node))
                if len(str(value)) > 18:  # Allow longer labels
                    value = str(value)[:15] + "..."
                labels[node] = value
                
            nx.draw_networkx_labels(target_graph, pos, labels, font_size=13, font_weight='bold',
                                  bbox=dict(boxstyle='round,pad=0.6', facecolor='white',
                                           edgecolor='#8e44ad', alpha=0.95, linewidth=2))
            
            # Add a legend for data dependency graph
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='h', color='w', markerfacecolor='#e74c3c', 
                          markersize=15, label='Variables', markeredgecolor='#c0392b', markeredgewidth=2),
                Line2D([0], [0], marker='^', color='w', markerfacecolor='#f39c12', 
                          markersize=12, label='Constants', markeredgecolor='#e67e22', markeredgewidth=2),
                Line2D([0], [0], marker='D', color='w', markerfacecolor='#3498db', 
                          markersize=13, label='Assignments', markeredgecolor='#2980b9', markeredgewidth=2),
                Line2D([0], [0], marker='*', color='w', markerfacecolor='#2ecc71', 
                          markersize=15, label='Function Calls', markeredgecolor='#27ae60', markeredgewidth=2),
                Line2D([0], [0], marker='s', color='w', markerfacecolor='#9b59b6', 
                          markersize=12, label='Operations', markeredgecolor='#8e44ad', markeredgewidth=2)
            ]
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))

            plt.axis('off')
            plt.tight_layout()
            
            # Save to buffer with maximum padding for DDG
            buffer = io.BytesIO()
            plt.savefig(buffer, format='svg', bbox_inches='tight', dpi=150, 
                       pad_inches=2.5, facecolor='#f8f9fa')  # Maximum padding for DDG
            plt.close()
            
            svg_data = buffer.getvalue().decode('utf-8')
            return base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        except Exception as e:
            print(f"Error generating DDG visualization: {str(e)}")
            return ""

    @staticmethod
    def _generate_graph_image(G: nx.DiGraph) -> str:
        """
        Convert networkx graph to base64 encoded image with improved layout
        
        Args:
            G (nx.DiGraph): Graph to visualize
        
        Returns:
            str: Base64 encoded image
        """
        # Ensure graph is not empty
        if len(G.nodes()) == 0:
            G.add_node("Empty Graph")
        
        # Calculate node depths from root nodes (nodes with no incoming edges)
        def get_node_depth(G, node, visited=None):
            """Calculate the depth of a node in the graph."""
            if visited is None:
                visited = set()
            
            # Handle cycles and already visited nodes
            if node in visited:
                return 0
            visited.add(node)
            
            try:
                # Get predecessors safely with error handling
                predecessors = list(G.predecessors(node)) if G.has_node(node) else []
                if not predecessors:  # If node has no predecessors (root node)
                    return 0
                    
                # Calculate max depth from predecessors
                max_depth = 0
                for pred in predecessors:
                    if pred not in visited and G.has_node(pred):  # Check if predecessor exists
                        try:
                            depth = get_node_depth(G, pred, visited.copy())  # Use copy to prevent modifying original set
                            max_depth = max(max_depth, depth)
                        except Exception as e:
                            print(f"Error in depth calculation for predecessor {pred}: {str(e)}")
                            continue  # Skip problematic predecessors
                return max_depth + 1
            except Exception as e:
                print(f"Error in get_node_depth for node {node}: {str(e)}")
                return 0  # Return safe default

        # Calculate depths for all nodes with error handling
        try:
            node_depths = {}
            for node in list(G.nodes()):  # Convert to list to avoid modification during iteration
                try:
                    if G.has_node(node):  # Verify node still exists
                        node_depths[node] = get_node_depth(G, node)
                    else:
                        node_depths[node] = 0
                except Exception as e:
                    print(f"Error calculating depth for node {node}: {str(e)}")
                    node_depths[node] = 0  # Default to 0 for problematic nodes
            
            max_depth = max(node_depths.values()) if node_depths else 0
        except Exception as e:
            print(f"Error in depth calculation: {str(e)}")
            # Fallback to simple layout if depth calculation fails
            node_depths = {node: 0 for node in G.nodes()}
            max_depth = 0

        # Use spring layout with custom parameters for better distribution
        try:
            if len(G.nodes()) > 1:
                pos = nx.spring_layout(
                    G,
                    k=25.0,  # Large spacing between nodes
                    iterations=1000  # More iterations for better distribution
                )
            else:
                # For single node or empty graph, use simple circular layout
                pos = nx.circular_layout(G)
        except Exception as e:
            print(f"Error in spring layout: {str(e)}")
            # Fallback to simpler layout if spring layout fails
            try:
                pos = nx.shell_layout(G)
            except:
                # Last resort: manual positioning
                pos = {node: [0.5, 0.5] for node in G.nodes()}

        # Adjust y-coordinates based on depth with error handling
        for node in list(pos.keys()):  # Convert to list to avoid modification during iteration
            try:
                if node not in G.nodes():  # Skip if node no longer exists
                    continue
                    
                depth = node_depths.get(node, 0)  # Use get() with default value
                if max_depth > 0:  # Avoid division by zero
                    pos[node][1] = 1.0 - (depth / (max_depth + 1)) * 2
                else:
                    pos[node][1] = 0.5  # Center nodes vertically if no depth info
                
                # Add minimal controlled randomness to x-coordinate
                if max_depth > 0:
                    pos[node][0] *= (1 + 0.05 * (depth / max_depth))  # Reduced randomness factor
            except Exception as e:
                print(f"Error adjusting position for node {node}: {str(e)}")
                # Provide safe default position if adjustment fails
                if isinstance(pos, dict):
                    pos[node] = [0.5, 0.5]
        
        # Enhanced node styling with error handling
        node_colors = []
        node_sizes = []
        node_labels = {}
        edge_colors = []
        edge_styles = []
        
        try:
            # Process nodes with comprehensive error handling
            for node in G.nodes():
                try:
                    node_type = G.nodes[node].get('type', 'default')
                    node_colors.append(DiagramGenerator._get_node_color(node_type))
                    
                    # Determine node size based on type and connections
                    size_factor = 1000  # Base size
                    if node_type in ['Module', 'ClassDef', 'ClassDeclaration']:
                        size_factor = 2000
                    elif node_type in ['FunctionDef', 'MethodDeclaration']:
                        size_factor = 1500
                    node_sizes.append(size_factor)
                    
                    # Create safe node labels
                    label = str(G.nodes[node].get('value', '')).replace('"', '').replace("'", "")
                    if len(label) > 20:  # Truncate long labels
                        label = label[:17] + "..."
                    node_labels[node] = label
                except Exception as e:
                    print(f"Error processing node {node}: {str(e)}")
                    node_colors.append('#CCCCCC')  # Default gray
                    node_sizes.append(1000)  # Default size
                    node_labels[node] = str(node)[:10]  # Safe truncated label
            
            # Process edges with error handling
            for edge in G.edges():
                try:
                    edge_colors.append('#666666')  # Consistent edge color
                    edge_styles.append('-')  # Solid line style
                except Exception as e:
                    print(f"Error processing edge {edge}: {str(e)}")
                    edge_colors.append('#CCCCCC')  # Default edge color
                    edge_styles.append(':')  # Dotted line for error cases
            
            # Clear any existing plots
            plt.clf()
            
            # Create figure with white background
            fig = plt.figure(figsize=(12, 8), facecolor='white')
            ax = fig.add_subplot(1, 1, 1)
            ax.set_facecolor('white')
            
            # Draw the graph with safe defaults
            if not pos:  # If position calculation failed
                pos = nx.spring_layout(G)  # Fallback layout
            
            # Draw nodes with error handling - draw individually
            try:
                # Ensure we have valid node colors and sizes
                if node_colors and len(node_colors) == len(G.nodes()):
                    final_node_colors = node_colors
                else:
                    final_node_colors = ['#CCCCCC'] * len(G.nodes())
                
                if node_sizes and len(node_sizes) == len(G.nodes()):
                    final_node_sizes = node_sizes
                else:
                    final_node_sizes = [1000] * len(G.nodes())
                
                # Draw nodes individually to avoid list parameter issues
                for i, node in enumerate(G.nodes()):
                    nx.draw_networkx_nodes(G, pos, 
                                         nodelist=[node],
                                         node_color=final_node_colors[i] if i < len(final_node_colors) else '#CCCCCC',
                                         node_size=final_node_sizes[i] if i < len(final_node_sizes) else 1000)
            except Exception as e:
                print(f"Error drawing nodes: {str(e)}")
                # Fallback to simple node drawing
                nx.draw_networkx_nodes(G, pos, node_color='#CCCCCC', node_size=1000)
            
            # Draw edges with error handling
            try:
                if edge_colors and len(edge_colors) == len(G.edges()):
                    # Draw edges individually with their respective colors
                    for i, edge in enumerate(G.edges()):
                        try:
                            color = edge_colors[i] if i < len(edge_colors) else '#666666'
                            style = edge_styles[i] if edge_styles and i < len(edge_styles) else '-'
                            nx.draw_networkx_edges(G, pos, edgelist=[edge],
                                                 edge_color=color,
                                                 style=style,
                                                 arrows=True, arrowsize=20)
                        except Exception as edge_error:
                            print(f"Error drawing edge {edge}: {str(edge_error)}")
                            continue
                else:
                    # Use single color for all edges
                    nx.draw_networkx_edges(G, pos, 
                                         edge_color='#666666',
                                         style='-',
                                         arrows=True, arrowsize=20)
            except Exception as e:
                print(f"Error drawing edges: {str(e)}")
                # Fallback to simple edge drawing
                nx.draw_networkx_edges(G, pos, edge_color='#666666')
            
            # Draw labels with error handling
            try:
                nx.draw_networkx_labels(G, pos, node_labels,
                                      font_size=8,
                                      font_family='sans-serif')
            except Exception as e:
                print(f"Error drawing labels: {str(e)}")
                # Fallback to simple labels
                nx.draw_networkx_labels(G, pos, {n: str(n)[:10] for n in G.nodes()})
            
            # Remove axes
            plt.axis('off')
            
        except Exception as e:
            print(f"Critical error in graph drawing: {str(e)}")
            # Create a minimal fallback visualization
            plt.clf()
            fig = plt.figure(figsize=(8, 6), facecolor='white')
            ax = fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, f"Error generating visualization:\n{str(e)}", 
                   horizontalalignment='center', verticalalignment='center')
            ax.axis('off')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight', dpi=150, 
                   pad_inches=0.5, facecolor='white', edgecolor='none')
        plt.close()
        
        # Encode to base64
        svg_data = buffer.getvalue().decode('utf-8')
        svg_base64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        return svg_base64

def generate_visualization(code: str, language: str, diagram_type: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate visualization for the given code and diagram type.
    
    Args:
        code (str): Source code to visualize
        language (str): Programming language ('python' or 'java')
        diagram_type (str): Type of diagram to generate ('ast', 'cfg', 'ddg')
    
    Returns:
        Tuple[str, str, Dict[str, Any]]: Base64 encoded SVG, title, and parsing metadata
    """
    plt.close('all')  # Ensure all previous plots are closed
    
    try:
        # Generate a consistent seed based on the code content
        import hashlib
        # Create a hash of the code and diagram type
        seed_string = f"{code}{language}{diagram_type}"
        hash_object = hashlib.md5(seed_string.encode())
        # Convert first 4 bytes of hash to integer and ensure it's within valid range
        seed = int.from_bytes(hash_object.digest()[:4], byteorder='big') & 0x7FFFFFFF  # Ensures value between 0 and 2^31-1
        
        # Set random seeds for consistent layout
        import random
        random.seed(seed)
        np.random.seed(seed)
        
        # Parse the code and generate graph
        G, metadata = SourceCodeParser.parse(code, language)
        
        # Generate the appropriate diagram based on type
        if diagram_type.lower() == 'ast':
            svg_base64 = DiagramGenerator.generate_ast(G, metadata)
            title = f"Abstract Syntax Tree ({language.title()})"
        elif diagram_type.lower() == 'cfg':
            svg_base64 = DiagramGenerator.generate_cfg(G, metadata)
            title = f"Control Flow Graph ({language.title()})"
        elif diagram_type.lower() == 'ddg':
            svg_base64 = DiagramGenerator.generate_ddg(G, metadata)
            title = f"Data Dependency Graph ({language.title()})"
        else:
            # Fallback to AST if unknown type
            svg_base64 = DiagramGenerator.generate_ast(G, metadata)
            title = f"Code Visualization ({language.title()})"
        
        return svg_base64, title, metadata
    
    except Exception as e:
        # Comprehensive error handling
        plt.close('all')
        error_metadata = {
            'parse_error': str(e),
            'total_nodes': 0,
            'language': language,
            'max_depth_reached': False
        }
        
        # Create an error visualization
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Visualization Error:\n{str(e)}", 
                 horizontalalignment='center', 
                 verticalalignment='center', 
                 color='red')
        plt.axis('off')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight')
        plt.close()
        
        # Encode to base64
        svg_data = buffer.getvalue().decode('utf-8')
        svg_base64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        return svg_base64, 'Visualization Error', error_metadata
