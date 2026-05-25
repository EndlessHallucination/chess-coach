from flask import Flask, jsonify, request
import chess
import requests
from stockfish import Stockfish

sf = Stockfish(path="/opt/homebrew/bin/stockfish")
app = Flask(__name__)

board = chess.Board()


# ── helpers ──────────────────────────────────────────────────────────────────

def fen_to_english(fen):
    """Convert FEN to a plain-English piece list. Fixed rank calculation."""
    files = "abcdefgh"
    pieces = {
        "p": "pawn", "n": "knight", "b": "bishop",
        "r": "rook",  "q": "queen",  "k": "king"
    }
    board_part = fen.split(" ")[0]
    turn_part  = fen.split(" ")[1]
    turn = "White" if turn_part == "w" else "Black"

    white, black = [], []
    file = 0
    rank = 7  # rank 7 = row '8' on the board (FEN starts from rank 8)

    for char in board_part:
        if char == "/":
            file = 0
            rank -= 1
        elif char.isdigit():
            file += int(char)
        else:
            # rank is 0-indexed here; rank 0 = rank '1', rank 7 = rank '8'
            square = files[file] + str(rank + 1)
            piece  = pieces[char.lower()]
            if char.islower():
                black.append(f"{piece} on {square}")
            else:
                white.append(f"{piece} on {square}")
            file += 1

    return (
        f"It is {turn}'s turn.\n"
        f"White pieces: {', '.join(white) or 'none'}\n"
        f"Black pieces: {', '.join(black) or 'none'}"
    )


def position_context(b: chess.Board) -> str:
    """Compact position string: move number + FEN + English layout."""
    fen = b.fen()
    return (
        f"Move {b.fullmove_number}.\n"
        f"FEN: {fen}\n"
        f"{fen_to_english(fen)}"
    )


def get_recent_moves(b: chess.Board, n: int = 6) -> str:
    """
    Return the last n half-moves formatted as chess notation with move numbers.
    Example: "8. Nf3 Nc6  9. Bb5 a6"
    """
    temp = chess.Board()
    numbered = []  # list of (move_number, color, san)

    for i, move in enumerate(b.move_stack):
        san        = temp.san(move)
        move_num   = (i // 2) + 1
        color      = "white" if i % 2 == 0 else "black"
        numbered.append((move_num, color, san))
        temp.push(move)

    recent = numbered[-n:] if numbered else []
    if not recent:
        return "opening — no moves yet"

    # Group into pairs for display
    parts = []
    i = 0
    while i < len(recent):
        num, col, san = recent[i]
        if col == "white":
            white_san = san
            black_san = recent[i + 1][2] if i + 1 < len(recent) else "..."
            parts.append(f"{num}. {white_san} {black_san}")
            i += 2
        else:
            # Starts mid-pair (e.g. after undo)
            parts.append(f"{num}... {san}")
            i += 1

    return "  ".join(parts)


def ollama_post(prompt: str, temperature: float = 0.3) -> dict:
    """Single place to call Ollama so options stay consistent everywhere."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "temperature": temperature,
        }
    }
    response = requests.post(url, json=payload)
    return response.json()


# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/board")
def show_board():
    return jsonify({"fen": board.fen()})


@app.route("/board/status")
def check_status():
    return jsonify({
        "checkmate": board.is_checkmate(),
        "stalemate": board.is_stalemate(),
        "check":     board.is_check(),
        "game_over": board.is_game_over(),
        "turn":      "white" if board.turn == chess.WHITE else "black"
    })


@app.route("/board/reset", methods=["POST"])
def reset():
    board.reset()
    return jsonify({"fen": board.fen()})


@app.route("/board/history", methods=["GET"])
def history():
    temp_board = chess.Board()
    moves = []
    for move in board.move_stack:
        moves.append(temp_board.san(move))
        temp_board.push(move)
    return jsonify({"moves": moves})


@app.route("/move", methods=["POST"])
def move():
    data = request.json
    uci  = data.get("move")
    try:
        chess_move = board.parse_uci(uci)
        san        = board.san(chess_move)  
        board.push(chess_move)
        return jsonify({"fen": board.fen(), "status": "ok", "san": san})
    except ValueError:
        return jsonify({"error": "illegal move", "status": "error"}), 400
 

@app.route("/board/hint", methods=["POST"])
def get_hint():
    sf.set_fen_position(board.fen())
    best_move = sf.get_best_move()

    # NOTE: legal_san list removed — it bloated context and confused the model
    # in complex positions. The position_context already tells the LLM everything
    # it needs to reason about the board.
    prompt = f"""You are an encouraging chess coach for beginners. Do not reveal the best move yet.

Recent moves: {get_recent_moves(board)}
{position_context(board)}

Give a hint that guides the player toward finding the best move themselves.
Respond with EXACTLY this format — no preamble, no extra text before or after:

HINT: [one sentence — guide their thinking without naming the move]
CONCEPT: [one sentence — name the chess idea involved, e.g. "fork", "pin", "development"]
BEST MOVE: {best_move}
EXPLANATION: [two sentences — why this move is strong in plain English]"""

    try:
        data = ollama_post(prompt, temperature=0.3)
        response_text = data["response"].strip()

        # Ensure Stockfish's best move is preserved even if the model rewrote it
        suggested = None
        for line in response_text.splitlines():
            if line.strip().upper().startswith("BEST MOVE:"):
                suggested = line.split(":", 1)[-1].strip()
                break

        if suggested and suggested != best_move:
            response_text = response_text.replace(suggested, best_move)

        return jsonify({"hint": response_text, "best_move": best_move})

    except Exception as e:
        return jsonify({"status": "error", "error": "Could not connect to Ollama"}), 500


@app.route("/board/analyze", methods=["POST"])
def analyze_board():
    req   = request.json
    move  = req.get("move")   
    color = req.get("color")
 
    prompt = f"""You are a friendly chess coach for beginners.
 
{position_context(board)}
Recent moves: {get_recent_moves(board)}
 
{color.capitalize()} just played: {move}
 
Looking only at the pieces and pawns listed above, in 2-3 sentences explain:
1. What {move} does immediately on THIS board — which piece moved, what it captures or controls
2. One concrete strength or weakness of this move given the current piece positions
 
Do not mention pieces that are not in the piece list above.
Do not suggest alternative moves.
Write in plain, encouraging English."""
 
    try:
        data = ollama_post(prompt, temperature=0.2)
        return jsonify({"response": data["response"].strip()})
    except Exception:
        return jsonify({"status": "error", "error": "Could not connect to Ollama"}), 500
 


@app.route("/board/undo", methods=["POST"])
def undo_move():
    if len(board.move_stack) == 0:
        return jsonify({"error": "no moves to undo"}), 400
    board.pop()
    return jsonify({"fen": board.fen()})


if __name__ == "__main__":
    app.run(debug=False)