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
      You are a chess coach helping a beginner. Be brief and clear.

    Current position FEN:  {fen_to_english(board.fen())}

    Respond using EXACTLY this format with no deviations:
    HINT: [one sentence]
    CONCEPTS: [one sentence]
    BEST MOVE: [just the move like e4 or Nf3, nothing else] 
    EXPLANATION: [two sentences]

    Do not add any other text before or after.
        
    Example response:
    HINT: Develop your knights before bishops.
    CONCEPTS: Piece development is the priority in the opening.
    BEST MOVE: Nf3
    EXPLANATION: Nf3 develops a piece toward the center. It also prepares for castling kingside.
    """

    payload = {
        "model": "mistral",
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

@app.route("/board/analyze", methods=["POST"])
def analyze_board():
    url = "http://localhost:11434/api/generate"

    try:
        data = request.json

        move = data.get("move")
        fen = fen_to_english(board.fen())
        color = data.get("color")


        prompt = f"""
        You are a chess coach AI.
        A player has just made a move in a chess game.
        Analyze ONLY the move that was just played, based on the current board position after the move.
        You will receive:
        The move played in UCI format (example: e2e4)
        The current FEN position after the move
        The color of the player who made the move ("white" or "black")
        Your task:
        Explain what the move does strategically or tactically
        Mention whether it improves development, controls the center, attacks something, defends something, etc.
        If the move has a weakness or mistake, explain it briefly
        Keep the explanation beginner-friendly and concise
        Do NOT suggest future moves unless necessary for explaining the idea
        Do NOT analyze the entire game
        Focus only on the move that was just played
        Move: {move}
        Color: {color}
        FEN: {fen}
        Example style of response:
        "e4 is a strong opening move that controls the center and opens lines for the queen and bishop. It helps White develop pieces actively and fight for space early in the game."

        Respond ONLY in valid plain text format
        """

        payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
        response = requests.post(url, json=payload)
        ollama_data = response.json()
        
        return {"response": ollama_data["response"]}


    except Exception:
        return jsonify({
            "status": "error",
            "error": "Could not connect to Ollama"
        }), 500
    
@app.route("/board/undo", methods=["POST"])
def undo_move():
    if len(board.move_stack) == 0:
        return jsonify({"error": "no moves to undo"}), 400
    board.pop()
    return jsonify({
        "fen":board.fen()
    })

def fen_to_english(fen):
    turn_part = fen.split(" ")[1]
    turn = "White" if turn_part == "w" else "Black"
    files = "abcdefgh"
    pieces = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
    board_part = fen.split(" ")[0]
    white = []
    black = []
    file = 0
    rank = 7
    for char in board_part:
        if char == "/":
            file = 0
            rank -= 1
        elif char.isdigit():
            file += int(char)
        else:
            if char.islower():
               square = files[file] + str(rank+1)
               piece = pieces[char.lower()]
               black.append(piece + " on " + square)
            else: 
               square = files[file] + str(rank + 1)
               piece = pieces[char.lower()]
               white.append(piece + " on " + square)
            file += 1
    return f"It is {turn}'s turn.\nWhite pieces: {', '.join(white)}\nBlack pieces: {', '.join(black)}" 


if __name__ == "__main__":
    app.run(debug=False)

