# SillyVisualizer

## Overview
SillyVisualizer is an interactive code visualization tool that generates Abstract Syntax Trees (AST), Control Flow Graphs (CFG), and Data Dependency Graphs (DDG) for Python and Java source code.

## Features
- Interactive code visualization
- Support for Python and Java languages
- Multiple diagram types:
  * Abstract Syntax Tree (AST)
  * Control Flow Graph (CFG)
  * Data Dependency Graph (DDG)
- Node dragging and repositioning
- Zoom and pan functionality

## Prerequisites
- Python 3.8+
- pip (Python package manager)

## Installation

### Python Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Running the Application
```bash
python web_application/backend.py
```

## Development
- Backend: Flask
- Frontend: JavaScript, HTML, CSS
- Visualization: NetworkX, Matplotlib, Pygraphviz

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Contact
Joshua Ludolf - Jludo01@jaguar.tamu.edu (or use Discussions tab of this repository)
