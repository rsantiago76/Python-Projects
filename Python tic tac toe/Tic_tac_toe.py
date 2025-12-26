# Text-based Tic Tac Toe (2 players) - runs in terminal

def print_board(board):
    cells = [c if c != " " else str(i + 1) for i, c in enumerate(board)]
    print("\n")
    print(f" {cells[0]} | {cells[1]} | {cells[2]} ")
    print("---+---+---")
    print(f" {cells[3]} | {cells[4]} | {cells[5]} ")
    print("---+---+---")
    print(f" {cells[6]} | {cells[7]} | {cells[8]} ")
    print("\n")

def check_winner(board):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
        (0, 4, 8), (2, 4, 6)              # diagonals
    ]
    for a, b, c in wins:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    return None

def is_draw(board):
    return all(c != " " for c in board)

def get_move(player, board):
    while True:
        move = input(f"Player {player}, choose a spot (1-9): ").strip()
        if not move.isdigit():
            print("Please enter a number from 1 to 9.")
            continue

        idx = int(move) - 1
        if idx < 0 or idx > 8:
            print("Out of range. Pick 1 to 9.")
            continue

        if board[idx] != " ":
            print("That spot is taken. Choose another.")
            continue

        return idx

def play():
    board = [" "] * 9
    current = "X"

    print("Welcome to Tic Tac Toe!")
    print("Enter a number (1-9) to place your mark.\n")

    while True:
        print_board(board)
        idx = get_move(current, board)
        board[idx] = current

        winner = check_winner(board)
        if winner:
            print_board(board)
            print(f"🎉 Player {winner} wins!")
            break

        if is_draw(board):
            print_board(board)
            print("🤝 It's a draw!")
            break

        current = "O" if current == "X" else "X"

if __name__ == "__main__":
    play()
