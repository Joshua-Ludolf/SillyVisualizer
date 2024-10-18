from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
from silly_visualizer import generate_visualization
import ast
import re
import threading
import matplotlib

matplotlib.use('Agg')  # Use Agg backend to prevent GUI issues
import matplotlib.pyplot as plt

app = Flask(__name__)
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


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        uploaded_filename = None

        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
                uploaded_filename = filename
                os.remove(filepath)  # Clean up after reading
            else:
                return jsonify({"error": "Invalid file type. Only .py and .java files are allowed."})
        else:
            code = request.form.get('code', '').strip()
            if not code:
                return jsonify({"error": "No code provided. Please either upload a file or paste code."})

        language = request.form.get('language', 'auto')
        if language == 'auto':
            language = detect_language(code)

        diagram_type = request.form.get('diagram_type', 'ast')

        # Use thread lock for matplotlib operations
        with plot_lock:
            try:
                graph_image, title = generate_visualization(code, language, diagram_type)
            except Exception as viz_error:
                return jsonify({"error": f"Visualization error: {str(viz_error)}"})

        response_data = {
            "image": graph_image,
            "title": title,
            "code_stats": analyze_code(code, language),
            "language_used": language
        }

        if uploaded_filename:
            response_data["uploaded_file"] = uploaded_filename

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"})


def analyze_code(code: str, language: str) -> dict:
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
    app.run(debug=False, threaded=True)