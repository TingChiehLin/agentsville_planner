# AgentsVille Trip Planner

This repository contains the AgentsVille Trip Planner Jupyter notebook and supporting code. The app generates and refines travel itineraries using an LLM and simulated tools (weather and activities).

## Getting Started

### 1 Setup 
1. Create and activate a virtual environment:
   - macOS / Linux
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - Windows (PowerShell)
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Set API keys

```
OPENAI_API_KEY=sk-...
# If using Vocareum:
# VOC_API_BASE=https://openai.vocareum.com/v1
# VOC_API_KEY=voc-...
```

### How to run the agent

```
python app.py
# or
python3 app.py
```

### How to run tests
```
# ensure venv active and package installed in editable mode
pytest -q
```
