import sys
from pathlib import Path

# Lets this script import code from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.knowledge import build_index

print("Pieces stored:", build_index())