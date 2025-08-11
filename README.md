# SillyVisualizer

## Overview
SillyVisualizer is a web app that turns Python and Java source code into interactive diagrams. It can generate Abstract Syntax Trees (AST), Control Flow Graphs (CFG), and Data Dependency Graphs (DDG) and render them interactively in your browser.

## Features
- Interactive, browser-based visualization (zoom, pan, drag)
- Supports Python and Java
- Diagram types:
  - Abstract Syntax Tree (AST)
  - Control Flow Graph (CFG)
  - Data Dependency Graph (DDG)
- Auto language detection (optional)
- Basic code stats (lines, functions, classes, characters)

## Tech stack
- Backend: Flask
- Parsing/graphs: ast (Python), javalang (Java), NetworkX, NumPy, Matplotlib
- Frontend: D3.js, jQuery, Tailwind CSS
- Optional: graphviz (Python package) for alternative SVG generation (not required for the main interactive UI)

## Prerequisites
- Python 3.11+
- pip
- Windows users: PowerShell 5.1+ (for the examples below)

## Setup (local)

Windows PowerShell
```powershell
# From the repo root
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

You can run the app either via the Docker entrypoint (port 3000) or via the Flask dev server.

Option A — Recommended (consistent with Docker):
```powershell
python .\main.py
# Starts on 0.0.0.0:3000 (use http://localhost:3000)
```

Option B — Flask dev server (default Flask port):
```powershell
python .\web_application\backend.py
# Starts on http://127.0.0.1:5000
```

Environment variables (when running main.py):
- PORT (default: 3000)
- HOST (default: 0.0.0.0)
- DEBUG (default: False)

## Docker

Using Docker Compose (recommended):
```powershell
docker compose up --build
# App available at http://localhost:3000 (override host port with APP_PORT env var)
```

Environment:
- docker-compose.yml maps ${APP_PORT:-3000}:3000
- The container runs `python main.py` and exposes container port 3000

## Using the web UI
Open the app in your browser. Paste code or upload a .py/.java file, pick a language (or Auto), choose AST/CFG/DDG, then click Visualize. The interactive D3 graph appears on the right.

## HTTP API

Endpoints
- GET / — serves the web UI
- POST /visualize — create a graph from code

Request (JSON)
```json
{
  "code": "def hello():\n    print('hi')\n",
  "language": "python",    // "python" | "java" | "auto"
  "diagram_type": "ast"     // "ast" | "cfg" | "ddg"
}
```

Response (JSON; abbreviated)
```json
{
  "graph_data": {
    "nodes": [{"id": "...", "label": "...", "type": "...", "group": 1}],
    "links": [{"source": "...", "target": "...", "type": "..."}],
    "metadata": {"language": "python"}
  },
  "title": "Abstract Syntax Tree (Python)",
  "language": "python",
  "diagram_type": "ast",
  "node_count": 12,
  "edge_count": 11
}
``;

Windows PowerShell example
```powershell
$body = @{ code = "public class A { void x(){} }"; language = "java"; diagram_type = "cfg" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:3000/visualize -ContentType application/json -Body $body
```

Optional curl example
```bash
curl -X POST http://localhost:3000/visualize \
  -H "Content-Type: application/json" \
  -d '{"code":"def f():\n  return 1","language":"python","diagram_type":"ddg"}'
```

## Tests
```powershell
pytest -q
```

## Project layout
```
.
├─ main.py                        # Entry for Docker/local (port 3000 by default)
├─ web_application/
│  ├─ backend.py                  # Flask app (also runnable directly on :5000)
│  ├─ silly_visualizer.py         # Parsing + diagram generation
│  └─ frontend/                   # D3 UI (index.html, script.js, styles)
├─ requirements.txt               # Runtime dependencies
├─ docker-compose.yml / Dockerfile
└─ tests: test_api.py, test_web_endpoint.py, ...
```

## Notes
- Graphviz (system binary) is not required for the interactive UI. The Python `graphviz` package is present for alternate SVG generation paths, but `/visualize` returns D3-ready data.
- Large inputs produce large graphs; try filtering your code or starting with AST.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Contact
Joshua Ludolf - Jludo01@jaguar.tamu.edu (or use the Discussions tab)
