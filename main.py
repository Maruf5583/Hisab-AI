import os
import sys
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
venv_python = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")

# If executed with global python and venv python exists, re-exec via venv python
if os.path.exists(venv_python) and os.path.normpath(sys.executable) != os.path.normpath(venv_python):
    result = subprocess.run([venv_python, __file__] + sys.argv[1:])
    sys.exit(result.returncode)

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  HisabAI — Accounting Backend Server")
    print("  Host: http://127.0.0.1:8000")
    print("  Swagger UI: http://127.0.0.1:8000/docs")
    print("  Redoc: http://127.0.0.1:8000/redoc")
    print("  Health: http://127.0.0.1:8000/health")
    print("=" * 60)

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
