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
                
                def add_node(node, parent=None, depth: int = 0, visited: set = None):
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
                
                def add_java_node(node, parent=None, depth: int = 0, visited: set = None):
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
                for type_declaration in tree.types:
                    add_java_node(type_declaration)
                
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
            # Create hierarchical layout
            pos = nx.spring_layout(G, k=2)
            
            # Adjust y-coordinates based on node depth
            root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            for root in root_nodes:
                bfs_edges = list(nx.bfs_edges(G, root))
                levels = {root: 0}
                for u, v in bfs_edges:
                    levels[v] = levels[u] + 1
                
                # Normalize depths
                max_depth = max(levels.values()) if levels else 0
                if max_depth > 0:
                    for node in levels:
                        if node in pos:
                            pos[node][1] = 1 - (levels[node] / max_depth)

            plt.figure(figsize=(12, 8), facecolor='white')
            
            # Draw edges as straight lines
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                 arrows=True, arrowsize=15,
                                 connectionstyle='arc3,rad=0')

            # Draw nodes with type-based colors and sizes
            node_colors = []
            node_sizes = []
            for node in G.nodes():
                node_type = G.nodes[node].get('type', 'default')
                if node_type in ['Module', 'ClassDef', 'ClassDeclaration']:
                    node_sizes.append(2000)
                elif node_type in ['FunctionDef', 'MethodDeclaration']:
                    node_sizes.append(1500)
                else:
                    node_sizes.append(1000)
                node_colors.append(DiagramGenerator._get_node_color(node_type))

            nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                 node_size=node_sizes, alpha=0.9)

            # Add labels
            labels = {node: G.nodes[node].get('value', '') for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)

            plt.axis('off')
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='svg', bbox_inches='tight', 
                       dpi=150, pad_inches=0.5, facecolor='white')
            plt.close()
            
            svg_data = buffer.getvalue().decode('utf-8')
            return base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        except Exception as e:
            print(f"Error generating AST visualization: {str(e)}")
            return ""

    @staticmethod
    def generate_cfg(G: nx.DiGraph, metadata: Dict[str, Any]) -> str:
        """Generate Control Flow Graph with traditional style."""
        try:
            # Use layout better suited for control flow
            pos = nx.kamada_kawai_layout(G)
            
            plt.figure(figsize=(12, 8), facecolor='white')
            
            # Draw different types of edges
            edge_styles = {'condition': ('red', '--'), 
                         'loop': ('blue', ':'),
                         'normal': ('black', '-')}
            
            for (u, v) in G.edges():
                edge_type = G.edges[u, v].get('type', '').lower()
                if 'condition' in edge_type:
                    color, style = edge_styles['condition']
                elif 'loop' in edge_type:
                    color, style = edge_styles['loop']
                else:
                    color, style = edge_styles['normal']
                
                nx.draw_networkx_edges(G, pos, edgelist=[(u, v)],
                                     edge_color=color,
                                     style=style,
                                     arrows=True,
                                     arrowsize=20,
                                     arrowstyle='->',
                                     connectionstyle='arc3,rad=0.2')

            # Draw nodes as rectangles with light background
            node_shapes = []
            node_colors = []
            node_sizes = []
            
            for node in G.nodes():
                node_type = G.nodes[node].get('type', '').lower()
                if 'condition' in node_type:
                    node_shapes.append('d')  # diamond for conditions
                    node_colors.append('lightblue')
                    node_sizes.append(2000)
                elif 'loop' in node_type:
                    node_shapes.append('s')  # square for loops
                    node_colors.append('lightgreen')
                    node_sizes.append(1800)
                else:
                    node_shapes.append('o')  # circle for other nodes
                    node_colors.append('white')
                    node_sizes.append(1500)

            # Draw nodes with different shapes
            for shape in set(node_shapes):
                node_list = [node for i, node in enumerate(G.nodes()) if node_shapes[i] == shape]
                if node_list:
                    nx.draw_networkx_nodes(G, pos,
                                         nodelist=node_list,
                                         node_color=[c for i, c in enumerate(node_colors) if node_shapes[i] == shape],
                                         node_size=[s for i, s in enumerate(node_sizes) if node_shapes[i] == shape],
                                         node_shape=shape,
                                         edgecolors='black')

            # Add labels
            labels = {node: G.nodes[node].get('value', '') for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)

            plt.axis('off')
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='svg', bbox_inches='tight', 
                       dpi=150, pad_inches=0.5, facecolor='white')
            plt.close()
            
            svg_data = buffer.getvalue().decode('utf-8')
            return base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
        
        except Exception as e:
            print(f"Error generating CFG visualization: {str(e)}")
            return ""

    @staticmethod
    def generate_ddg(G: nx.DiGraph, metadata: Dict[str, Any]) -> str:
        """Generate Data Dependency Graph with emphasis on data flow."""
        try:
            # Use circular layout for data dependency visualization
            pos = nx.circular_layout(G)
            
            plt.figure(figsize=(12, 8), facecolor='white')
            
            # Draw edges with dependency labels
            edge_labels = {}
            for (u, v) in G.edges():
                dep_type = G.edges[u, v].get('dependency_type', '')
                edge_labels[(u, v)] = dep_type
                
                # Draw curved arrows for dependencies
                nx.draw_networkx_edges(G, pos, edgelist=[(u, v)],
                                     edge_color='#2980b9',
                                     arrows=True,
                                     arrowsize=20,
                                     arrowstyle='->',
                                     connectionstyle='arc3,rad=0.3',
                                     width=2)
            
            # Draw edge labels if they exist
            if edge_labels:
                nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)
            
            # Draw nodes with different styles based on type
            var_nodes = []
            op_nodes = []
            for node in G.nodes():
                if G.nodes[node].get('type') == 'variable':
                    var_nodes.append(node)
                else:
                    op_nodes.append(node)
            
            # Draw variable nodes
            if var_nodes:
                nx.draw_networkx_nodes(G, pos,
                                     nodelist=var_nodes,
                                     node_color='#e74c3c',
                                     node_size=2000,
                                     node_shape='o')
            
            # Draw operation nodes
            if op_nodes:
                nx.draw_networkx_nodes(G, pos,
                                     nodelist=op_nodes,
                                     node_color='#2ecc71',
                                     node_size=1500,
                                     node_shape='s')
            
            # Add labels
            labels = {node: G.nodes[node].get('value', '') for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
            plt.axis('off')
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='svg', bbox_inches='tight', 
                       dpi=150, pad_inches=0.5, facecolor='white')
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
                    iterations=1000,  # More iterations for better distribution
                    scale=15.0,  # Large scale for overall spacing
                    weight=None  # Ignore edge weights
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
            
            # Draw nodes with error handling
            try:
                nx.draw_networkx_nodes(G, pos, 
                                     node_color=node_colors if node_colors else '#CCCCCC',
                                     node_size=node_sizes if node_sizes else 1000)
            except Exception as e:
                print(f"Error drawing nodes: {str(e)}")
                # Fallback to simple node drawing
                nx.draw_networkx_nodes(G, pos, node_color='#CCCCCC', node_size=1000)
            
            # Draw edges with error handling
            try:
                nx.draw_networkx_edges(G, pos, 
                                     edge_color=edge_colors if edge_colors else '#666666',
                                     style=edge_styles if edge_styles else '-',
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
        
        # Generate the diagram based on type
        plt.figure(figsize=(14, 12), dpi=150)
        
        # Ensure graph is not empty
        if len(G.nodes()) == 0:
            # Create a placeholder graph if no nodes exist
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
                    iterations=1000,  # More iterations for better distribution
                    scale=15.0,  # Large scale for overall spacing
                    weight=None,  # Ignore edge weights
                    seed=seed  # Use our consistent seed
                )
            else:
                # For single node or empty graph, use simple circular layout
                pos = nx.circular_layout(G, scale=10.0)
        except Exception as e:
            print(f"Error in spring layout: {str(e)}")
            # Fallback to simpler layout if spring layout fails
            try:
                pos = nx.shell_layout(G, scale=10.0)
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
            
            # Draw nodes with error handling
            try:
                nx.draw_networkx_nodes(G, pos, 
                                     node_color=node_colors if node_colors else '#CCCCCC',
                                     node_size=node_sizes if node_sizes else 1000)
            except Exception as e:
                print(f"Error drawing nodes: {str(e)}")
                # Fallback to simple node drawing
                nx.draw_networkx_nodes(G, pos, node_color='#CCCCCC', node_size=1000)
            
            # Draw edges with error handling
            try:
                nx.draw_networkx_edges(G, pos, 
                                     edge_color=edge_colors if edge_colors else '#666666',
                                     style=edge_styles if edge_styles else '-',
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
        
        return svg_base64, 'Code Visualization', metadata
    
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
