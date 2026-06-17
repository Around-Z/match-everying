"""Development server runner."""
import sys
import os

# Pre-flight check: ensure required packages are installed
MISSING = []
for pkg in ("zhipuai", "pymilvus", "jose", "bcrypt", "fastapi", "uvicorn", "pymysql"):
    try:
        __import__(pkg)
    except ImportError:
        MISSING.append(pkg)

if MISSING:
    CONDA_PY = os.path.expandvars(r"%USERPROFILE%\anaconda3\python.exe")
    print(f"[ERROR] Missing packages: {', '.join(MISSING)}")
    print(f"[ERROR] You are using: {sys.executable}")
    if os.path.exists(CONDA_PY):
        print(f"[FIX] Use conda Python instead:")
        print(f"     {CONDA_PY} run.py")
    else:
        print(f"[FIX] Install missing packages: pip install {' '.join(MISSING)}")
    sys.exit(1)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
