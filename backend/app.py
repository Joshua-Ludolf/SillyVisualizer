from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from silly_visualizer import generate_visualization
import ast
import javalang
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
ALLOWED_EXTENSIONS = {'py', 'java'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                with open(filepath, 'r') as f:
                    code = f.read()

                # Clean up the uploaded file
                os.remove(filepath)
            else:
                return jsonify({"error": "Invalid file type. Only .py and .java files are allowed."})
        else:
            code = request.form['code']

        language = request.form['language']
        diagram_type = request.form['diagram_type']

        graph_image, title = generate_visualization(code, language, diagram_type)
        return jsonify({
            "image": graph_image,
            "title": title,
            "code_stats": analyze_code(code, language)
        })
    except Exception as e:
        return jsonify({"error": str(e)})


def analyze_code(code: str, language: str) -> dict:
    """Analyzes the code and returns basic statistics."""
    stats = {
        "lines_of_code": len(code.splitlines()),
        "characters": len(code),
        "functions": 0,
        "classes": 0
    }

    if language == 'python':
        tree = ast.parse(code)
        stats["functions"] = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        stats["classes"] = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
    elif language == 'java':
        tree = javalang.parse.parse(code)
        stats["functions"] = len([node for path, node in tree.filter(javalang.tree.MethodDeclaration)])
        stats["classes"] = len([node for path, node in tree.filter(javalang.tree.ClassDeclaration)])

    return stats


if __name__ == '__main__':
    app.run(debug=False)