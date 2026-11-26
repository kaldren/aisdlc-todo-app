import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_import_touches_no_files(tmp_path):
    """Importing app.main (as pytest and uvicorn do) must not create var/ files."""
    env = {k: v for k, v in os.environ.items() if k not in ("TODO_DB", "TODO_LOG")}
    env["PYTHONPATH"] = str(ROOT)
    code = "import app.main; assert app.main.app.title"
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, check=True)
    assert list(tmp_path.iterdir()) == []
