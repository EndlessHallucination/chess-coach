from flask import Flask, jsonify, request
import chess

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





if __name__ == "__main__":
    app.run(debug=False)

