from flask import Flask, jsonify, request
import chess
import requests

app = Flask(__name__)

board = chess.Board()

@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/board")
def show_board():
    return jsonify({
        "fen":board.fen()
    })

@app.route("/board/reset", methods=["POST"])
def reset():
    board.reset()
    return jsonify({"fen": board.fen()})

@app.route("/move", methods=["POST"])
def move():
    
    data = request.json
  
    move = data.get("move")

    try:

        board.push_uci(move)

        return jsonify({
            "fen": board.fen(),
            "status": "ok"
        })

    except ValueError:

        return jsonify({
            "error": "illegal move",
            "status": "error"
        }), 400

@app.route("/board/hint", methods=["POST"])
def get_hint():

    url = "http://localhost:11434/api/generate"

    prompt = f"""
        You are a friendly chess coach helping a beginner improve.

        Current board position in FEN:
        {board.fen()}

        Your job is NOT to simply give the best move immediately.

        Instead:
        1. Briefly describe the current position.
        2. Explain important ideas in the position:
        - king safety
        - development
        - center control
        - piece activity
        - tactical threats
        3. Give 2-3 candidate moves the player should consider.
        4. Explain the pros and cons of each move.
        5. Give a coaching-style hint first.
        6. Only after the explanation, recommend the strongest move.
        7. Keep explanations simple and educational.
        8. Encourage the player to think instead of just memorizing moves.

        Respond ONLY in valid JSON using this format:

        {{
        "hint": "...",
        "concepts": "...",
        "candidate_moves": [
            {{
            "move": "...",
            "idea": "..."
            }}
        ],
        "best_move": "...",
        "explanation": "..."
        }}
        """

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }
    

    try:

        response = requests.post(url, json=payload)
        data = response.json()

        return jsonify({"hint": data["response"]})

    except Exception:

        return jsonify({
            "status": "error",
            "error": "Could not connect to Ollama"
        }), 500

  



if __name__ == "__main__":
    app.run(debug=False)

