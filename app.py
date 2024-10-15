"""
    Group #9
    Members: Joshua Ludolf, Samantha Jackson, Matthew Trevino, Jonathon Davis

    Class: CSCI 4316 - Software Engineering 1
"""

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # return render_template('index.html')
     return render_template('frontend\src\App.js')

if __name__ == '__main__':
    app.run(debug=False)
