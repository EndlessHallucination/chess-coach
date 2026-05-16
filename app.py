from flask import Flask, jsonify, request
import chess

app = Flask(__name__)

board = chess.Board()


@app.route("/")
def home():
    return jsonify({
        "fen":board.fen()
    })

@app.route("/move", methods=["POST"])
def move():
    print("move route hit")
    
    data = request.json
  
    print("data received:", data)
    move = data.get("move")

    try:

        board.push_san(move)

        return jsonify({
            "fen": board.fen(),
            "status": "ok"
        })

    except ValueError:

        return jsonify({
            "error": "illegal move",
            "status": "error"
        }), 400


if __name__ == "__main__":
    app.run(debug=False)

