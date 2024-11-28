# Source Code Visualizer

## Overview
A Django-based web application for visualizing source code through multiple graph representations, supporting Python and Java languages.

## Features
- Abstract Syntax Tree (AST) Generation
- Control Flow Graph (CFG) Generation
- Data Dependency Graph (DDG) Generation

## Prerequisites
- Python 3.8+
- pip

## Installation
1. Clone the repository
2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Start the development server
```bash
python manage.py runserver
```

## Usage
1. Navigate to the homepage
2. Select the programming language
3. Paste your source code
4. Click "Visualize" to generate graphs

## Supported Languages
- Python
- Java

## Contributing
Contributions are welcome! Please submit pull requests or open issues.

## License
MIT License
