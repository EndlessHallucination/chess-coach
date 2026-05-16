import chess

board = chess.Board()

print(board)
print("White to move" if board.turn == chess.WHITE else "Black to move")