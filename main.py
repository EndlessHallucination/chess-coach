import chess

board = chess.Board()


while not board.is_game_over():
    print(board)
    print()

    print("White to move" if board.turn == chess.WHITE else "Black to move")
    
    move = input("Type your move or 'quit'>> ")

    if move == 'quit':
        break
    try: 
        board.push_san(move)
    except ValueError:
        print("Illegal move! Try again")

print(board)

if board.is_checkmate():
    winner = "Black" if board.turn == chess.WHITE else "White"

    print(f"Checkmate!, {winner} wins!")
else: 
    print("Stalemate")