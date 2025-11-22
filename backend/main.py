import sys
import uvicorn
from pathlib import Path

# Ajouter le répertoire courant (backend) au sys.path pour trouver 'app'
# Cela permet de faire 'from app.main import app' même si lancé depuis la racine
sys.path.append(str(Path(__file__).parent))

from app.main import app

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
