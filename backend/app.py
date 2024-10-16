"""
Group #9 Members: Joshua Ludolf, Samantha Jackson, Matthew Trevino, Jonathon Davis
Class: CSCI 4316 - Software Engineering 1
"""

from flask import Flask, render_template, request, jsonify
from silly_visualizer import generate_visualization

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/visualize', methods=['POST'])
def visualize():
    code = request.form['code']
    language = request.form['language']
    diagram_type = request.form['diagram_type']

    try:
        graph_image, title = generate_visualization(code, language, diagram_type)
        return jsonify({"image": graph_image, "title": title})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=False)