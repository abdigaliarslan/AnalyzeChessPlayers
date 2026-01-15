# Analyze Chess Player

A tool for analyzing chess games from PNG files, generating detailed descriptions and visualizations of each game.

---

## Features
- Analyze chess game PNG files
- Generate game descriptions automatically
- Quick launch via Uvicorn web server

---

## Installation

```bash
# Clone the repository and navigate to the project directory
git clone https://github.com/abdigaliarslan/AnalyzeChessPlayers.git
cd AnalyzeChessPlayers

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --port 8080

After running, open your browser at http://127.0.0.1:8080 to access the application. 
