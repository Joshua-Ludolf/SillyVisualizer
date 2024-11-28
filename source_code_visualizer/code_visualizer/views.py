from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import ast
import javalang
import networkx as nx
import graphviz
import os

def parse_python_ast(code):
    """Generate Abstract Syntax Tree for Python code."""
    try:
        tree = ast.parse(code)
        return _convert_ast_to_graph(tree)
    except SyntaxError as e:
        return {"error": str(e)}

def parse_java_ast(code):
    """Generate Abstract Syntax Tree for Java code."""
    try:
        tokens = list(javalang.tokenizer.tokenize(code))
        parser = javalang.parser.Parser(tokens)
        tree = parser.parse()
        return _convert_java_ast_to_graph(tree)
    except Exception as e:
        return {"error": str(e)}

def generate_control_flow_graph(code, language):
    """Generate Control Flow Graph for given code."""
    try:
        if language == 'python':
            tree = ast.parse(code)
            cfg = _build_python_cfg(tree)
        elif language == 'java':
            tokens = list(javalang.tokenizer.tokenize(code))
            parser = javalang.parser.Parser(tokens)
            tree = parser.parse()
            cfg = _build_java_cfg(tree)
        else:
            return {"error": "Unsupported language"}
        
        return cfg
    except Exception as e:
        return {"error": str(e)}

def generate_data_dependency_graph(code, language):
    """Generate Data Dependency Graph for given code."""
    try:
        if language == 'python':
            tree = ast.parse(code)
            ddg = _build_python_ddg(tree)
        elif language == 'java':
            tokens = list(javalang.tokenizer.tokenize(code))
            parser = javalang.parser.Parser(tokens)
            tree = parser.parse()
            ddg = _build_java_ddg(tree)
        else:
            return {"error": "Unsupported language"}
        
        return ddg
    except Exception as e:
        return {"error": str(e)}

def _graph_to_dict(graph):
    """Convert NetworkX graph to dictionary representation."""
    return {
        "nodes": [{"id": str(n), "label": str(graph.nodes[n].get('label', ''))} for n in graph.nodes],
        "edges": [{"source": str(e[0]), "target": str(e[1])} for e in graph.edges]
    }

def _convert_ast_to_graph(node, graph=None, parent=None):
    """Convert Python AST to NetworkX graph."""
    if graph is None:
        graph = nx.DiGraph()
    
    node_id = str(id(node))
    node_label = type(node).__name__
    
    # Add additional info for certain node types
    if isinstance(node, ast.Name):
        node_label += f" ({node.id})"
    elif isinstance(node, ast.Num):
        node_label += f" ({node.n})"
    elif isinstance(node, ast.Str):
        node_label += f" ({node.s})"
    
    graph.add_node(node_id, label=node_label)
    
    if parent is not None:
        parent_id = str(id(parent))
        graph.add_edge(parent_id, node_id)
    
    for child in ast.iter_child_nodes(node):
        _convert_ast_to_graph(child, graph, node)
    
    return {
        "nodes": [{"id": str(n), "label": str(graph.nodes[n].get('label', ''))} for n in graph.nodes],
        "edges": [{"source": str(e[0]), "target": str(e[1])} for e in graph.edges]
    }

def _convert_java_ast_to_graph(node, graph=None, parent=None):
    """Convert Java AST to NetworkX graph with enhanced OOP visualization."""
    if graph is None:
        graph = nx.DiGraph()
    
    node_id = str(id(node))
    node_label = type(node).__name__

    # Add more detailed information for different node types
    if hasattr(node, 'name') and node.name is not None:
        node_label += f"\n{node.name}"
    
    # Handle extends relationship
    if hasattr(node, 'extends') and node.extends is not None:
        if hasattr(node.extends, 'name') and node.extends.name is not None:
            node_label += f"\nextends {node.extends.name}"
    
    # Handle implements relationship
    if hasattr(node, 'implements') and node.implements is not None:
        implements = []
        for i in node.implements:
            if hasattr(i, 'name') and i.name is not None:
                implements.append(i.name)
        if implements:
            node_label += f"\nimplements {', '.join(implements)}"
    
    # Add node with enhanced label
    graph.add_node(node_id, label=node_label)
    
    if parent is not None:
        parent_id = str(id(parent))
        # Add different edge styles for different relationships
        if isinstance(node, javalang.tree.ClassDeclaration):
            if hasattr(node, 'extends') and node.extends is not None:
                graph.add_edge(node_id, parent_id, relationship='extends')
            if hasattr(node, 'implements') and node.implements:
                graph.add_edge(node_id, parent_id, relationship='implements')
        else:
            graph.add_edge(parent_id, node_id, relationship='contains')
    
    # Recursively process child nodes
    if hasattr(node, 'children'):
        for child in node.children:
            if child is not None:
                if isinstance(child, javalang.ast.Node):
                    _convert_java_ast_to_graph(child, graph, node)
                elif isinstance(child, list):
                    for item in child:
                        if item is not None and isinstance(item, javalang.ast.Node):
                            _convert_java_ast_to_graph(item, graph, node)
    
    return {
        "nodes": [{"id": str(n), "label": str(graph.nodes[n].get('label', '')).replace('\n', ' - ')} for n in graph.nodes],
        "edges": [{"source": str(e[0]), "target": str(e[1]), 
                  "relationship": graph.edges[e].get('relationship', 'contains')} for e in graph.edges]
    }

def _build_python_cfg(node):
    """Build Control Flow Graph for Python code focusing on function-level control flow."""
    graph = nx.DiGraph()
    current_function = None
    
    def add_edge_if_new(source, target, label=""):
        if not graph.has_edge(source, target):
            graph.add_edge(source, target, label=label)
    
    def visit(node):
        nonlocal current_function
        
        if isinstance(node, ast.FunctionDef):
            # Create node for function
            graph.add_node(node.name, label=f"Function: {node.name}")
            prev_function = current_function
            current_function = node.name
            
            # Find all function calls within this function
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    called_func = child.func.id
                    if called_func in graph:
                        add_edge_if_new(current_function, called_func, "calls")
            
            current_function = prev_function
            
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # If we're in the global scope
            if current_function is None and node.func.id in graph:
                add_edge_if_new("Global", node.func.id, "calls")
        
        # Add entry point
        elif isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            if any(isinstance(c, ast.Name) and c.id == "__name__" for c in ast.walk(node.test)):
                if any(isinstance(c, ast.Str) and c.s == "__main__" for c in ast.walk(node.test)):
                    graph.add_node("Global", label="Program Entry")
                    for child in node.body:
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            add_edge_if_new("Global", child.func.id, "calls")
        
        # Recursively visit all children
        for child in ast.iter_child_nodes(node):
            visit(child)
    
    # Start visiting from the root
    visit(node)
    
    # Remove isolated nodes
    for node in list(graph.nodes()):
        if not list(graph.predecessors(node)) and not list(graph.successors(node)):
            graph.remove_node(node)
    
    return {
        "nodes": [{"id": n, "label": graph.nodes[n]["label"]} for n in graph.nodes],
        "edges": [{"source": e[0], "target": e[1], "label": graph.edges[e]["label"]} for e in graph.edges]
    }

def _build_java_cfg(node):
    """Build Control Flow Graph for Java code focusing on class and method-level control flow."""
    graph = nx.DiGraph()
    current_class = None
    current_method = None
    
    def add_edge_if_new(source, target, label=""):
        if not graph.has_edge(source, target):
            graph.add_edge(source, target, label=label)
    
    def get_full_method_name(method_name):
        return f"{current_class}.{method_name}" if current_class else method_name
    
    def visit(node):
        nonlocal current_class, current_method
        
        if isinstance(node, javalang.tree.ClassDeclaration):
            current_class = node.name
            # Add class node
            graph.add_node(current_class, label=f"Class: {current_class}")
            
            # Handle inheritance
            if node.extends:
                parent_class = node.extends.name
                graph.add_node(parent_class, label=f"Class: {parent_class}")
                add_edge_if_new(current_class, parent_class, "extends")
            
            # Handle interfaces
            if node.implements:
                for interface in node.implements:
                    interface_name = interface.name
                    graph.add_node(interface_name, label=f"Interface: {interface_name}")
                    add_edge_if_new(current_class, interface_name, "implements")
            
            # Visit class members
            for child in node.body:
                visit(child)
                
            current_class = None
            
        elif isinstance(node, javalang.tree.MethodDeclaration):
            method_name = get_full_method_name(node.name)
            graph.add_node(method_name, label=f"Method: {method_name}")
            prev_method = current_method
            current_method = method_name
            
            # Find method calls within this method
            for path, child in node.filter(javalang.tree.MethodInvocation):
                if hasattr(child, 'member'):
                    called_method = child.member
                    # If method call includes class qualifier, use it
                    if hasattr(child, 'qualifier') and child.qualifier:
                        called_method = f"{child.qualifier}.{called_method}"
                    else:
                        # Assume it's a method in the current class
                        called_method = get_full_method_name(called_method)
                    
                    if called_method != current_method:  # Avoid self-loops
                        graph.add_node(called_method, label=f"Method: {called_method}")
                        add_edge_if_new(current_method, called_method, "calls")
            
            current_method = prev_method
        
        # Visit all children
        if hasattr(node, 'children'):
            for child in node.children:
                if child is not None:
                    if isinstance(child, list):
                        for item in child:
                            if item is not None:
                                visit(item)
                    else:
                        visit(child)
    
    # Start visiting from the root
    visit(node)
    
    # Remove isolated nodes
    for node in list(graph.nodes()):
        if not list(graph.predecessors(node)) and not list(graph.successors(node)):
            graph.remove_node(node)
    
    return {
        "nodes": [{"id": n, "label": graph.nodes[n]["label"]} for n in graph.nodes],
        "edges": [{"source": e[0], "target": e[1], "label": graph.edges[e]["label"]} for e in graph.edges]
    }

def _build_python_ddg(node):
    """Build Data Dependency Graph for Python code."""
    graph = nx.DiGraph()
    variables = {}
    
    def visit(node, parent_id=None):
        node_id = str(id(node))
        node_label = type(node).__name__
        
        if isinstance(node, ast.Name):
            node_label += f" ({node.id})"
            if isinstance(parent_id, ast.Assign):
                # Variable definition
                variables[node.id] = node_id
            elif node.id in variables:
                # Variable usage - create dependency edge
                graph.add_edge(variables[node.id], node_id)
        
        graph.add_node(node_id, label=node_label)
        
        if parent_id:
            graph.add_edge(str(id(parent_id)), node_id)
        
        for child in ast.iter_child_nodes(node):
            visit(child, node)
    
    if isinstance(node, ast.AST):
        visit(node)
    
    return {
        "nodes": [{"id": str(n), "label": str(graph.nodes[n].get('label', ''))} for n in graph.nodes],
        "edges": [{"source": str(e[0]), "target": str(e[1])} for e in graph.edges]
    }

def _build_java_ddg(node):
    """Build Data Dependency Graph for Java code with field dependencies."""
    graph = nx.DiGraph()
    variables = {}
    
    def visit(node, parent_id=None):
        node_id = str(id(node))
        node_label = type(node).__name__
        
        # Track field declarations and method parameters
        if isinstance(node, javalang.tree.FieldDeclaration):
            for declarator in node.declarators:
                var_name = declarator.name
                node_label = f"Field: {var_name}"
                variables[var_name] = node_id
        elif isinstance(node, javalang.tree.FormalParameter):
            var_name = node.name
            node_label = f"Parameter: {var_name}"
            variables[var_name] = node_id
        elif isinstance(node, javalang.tree.VariableDeclarator):
            var_name = node.name
            node_label = f"Variable: {var_name}"
            variables[var_name] = node_id
        elif isinstance(node, javalang.tree.MemberReference):
            if node.member in variables:
                graph.add_edge(variables[node.member], node_id)
        
        graph.add_node(node_id, label=node_label)
        
        if parent_id:
            graph.add_edge(str(id(parent_id)), node_id)
        
        # Process children
        for child in node.children:
            if isinstance(child, javalang.ast.Node):
                visit(child, node)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, javalang.ast.Node):
                        visit(item, node)
    
    if isinstance(node, javalang.ast.Node):
        visit(node)
    
    return {
        "nodes": [{"id": str(n), "label": str(graph.nodes[n].get('label', ''))} for n in graph.nodes],
        "edges": [{"source": str(e[0]), "target": str(e[1])} for e in graph.edges]
    }

@csrf_exempt
def upload_code(request):
    """Handle code upload and visualization."""
    if request.method == 'POST':
        code = request.POST.get('code', '')
        language = request.POST.get('language', 'python')
        
        # Validate input
        if not code:
            return JsonResponse({"error": "No code provided"}, status=400)
        
        # Validate language
        if language not in ['python', 'java']:
            return JsonResponse({"error": "Unsupported language"}, status=400)
        
        try:
            # Generate visualizations based on language
            if language == 'python':
                tree = ast.parse(code)
                ast_graph = _convert_ast_to_graph(tree)
                cfg_graph = _build_python_cfg(tree)
                ddg_graph = _build_python_ddg(tree)
            else:  # java
                tokens = list(javalang.tokenizer.tokenize(code))
                parser = javalang.parser.Parser(tokens)
                tree = parser.parse()
                ast_graph = _convert_java_ast_to_graph(tree)
                cfg_graph = _build_java_cfg(tree)
                ddg_graph = _build_java_ddg(tree)
            
            return JsonResponse({
                "ast": ast_graph,
                "cfg": cfg_graph,
                "ddg": ddg_graph
            })
        except SyntaxError as e:
            return JsonResponse({
                "error": f"Syntax error in {language} code: {str(e)}"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "error": f"Error processing {language} code: {str(e)}"
            }, status=500)
    
    return render(request, 'code_visualizer/upload.html')
