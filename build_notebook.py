"""Build story.ipynb from story.py and execute it, so the notebook on GitHub shows every chart.

    python build_notebook.py

story.py stays the source of truth (it runs as a plain script too); the notebook is generated.
Needs: pip install -r requirements-notebook.txt
"""
from pathlib import Path

import jupytext
import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent

notebook = jupytext.read(HERE / "story.py")
notebook.metadata.pop("jupytext", None)
NotebookClient(notebook, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(HERE)}}).execute()
nbformat.write(notebook, HERE / "story.ipynb")
charts = sum(1 for cell in notebook.cells for out in cell.get("outputs", []) if "image/png" in out.get("data", {}))
print(f"wrote story.ipynb: {len(notebook.cells)} cells, {charts} charts")
