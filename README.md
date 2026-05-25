# Chess Coach ♟️

A local chess app with an AI coaching layer built on top of Stockfish and a local LLM (Mistral via Ollama). Play a game, get hints without spoilers, and receive plain-English analysis of your moves — all running on your own machine.

---

## What it does

- **Play chess** — drag and drop pieces on an interactive board
- **Get hints** — asks the LLM to guide your thinking toward the best move without giving it away directly; Stockfish guarantees the suggested move is actually correct
- **Move analysis** — after each move, get a 2-3 sentence breakdown of what the move accomplishes and its strengths or weaknesses
- **Move history** — live notation panel updates as you play
- **Undo** — take back the last move
- **Flip board** — switch perspective

---

## Stack

| Layer | Tech |
|---|---|
| Board UI | [chessboard.js](https://chessboardjs.com) |
| Chess logic (frontend) | plain JS |
| Backend | Python / Flask |
| Chess logic (backend) | [python-chess](https://python-chess.readthedocs.io) |
| Engine | [Stockfish](https://stockfishchess.org) |
| LLM | [Mistral](https://mistral.ai) via [Ollama](https://ollama.com) |

---

## Requirements

- Python 3.10+
- [Stockfish](https://stockfishchess.org/download/) installed locally
- [Ollama](https://ollama.com) running locally with the Mistral model pulled

```bash
ollama pull mistral
```

---

## Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/chess-coach.git
cd chess-coach

# Install Python dependencies
pip install flask python-chess stockfish requests

# Update the Stockfish path in app.py if needed
# Default is: /opt/homebrew/bin/stockfish  (macOS Homebrew)

# Run
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

---

## Project structure

```
chess-coach/
├── app.py              # Flask backend — routes, Stockfish, Ollama prompts
├── static/
│   ├── main.js         # Board logic, fetch calls, UI updates
│   └── index.html      # App shell
└── README.md
```

---

## Known limitations / future ideas

- No computer opponent — human vs human (or human vs yourself) only
- LLM analysis can hallucinate piece positions in complex endgames; Stockfish move suggestions are always accurate
- No time controls
- Possible future additions: engine play mode, game import/export via PGN, opening name detection, eval bar

---

## License

MIT