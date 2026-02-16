"""
Raspberry Pi Chess Server (Simplified for GUI Coordination)
Handles chess engine communication and game logic for the AI Chess project.
This server runs on the Raspberry Pi and communicates with the laptop GUI.

The GUI coordinates all moves - this Pi just maintains board state and calculates moves when asked.
"""

import chess
import chess.engine
from flask import Flask, request, jsonify
import json
import time
import os

app = Flask(__name__)

# Global game state
board = chess.Board()
engine = None
game_active = False
current_player = 'white'

# NNUE file path (absolute path)
NNUE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nnue', 'carlsen_halfkav2_hm.nnue'))

def initialize_engine():
    """Initialize the Stockfish chess engine"""
    global engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
        engine.configure({
            "Skill Level": 10,
            "UCI_LimitStrength": True,
            "UCI_Elo": 1350
        })
        print("Chess engine initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize chess engine: {e}")
        return False

def get_board_state():
    """Get current board state as a dictionary"""
    board_state = {}
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            square_name = chess.square_name(square)
            piece_symbol = piece.symbol()
            board_state[square_name] = piece_symbol
    return board_state

def is_valid_move(from_square, to_square, piece_code):
    """Validate if a move is legal"""
    try:
        print(f"Validating move: {from_square} to {to_square}")
        
        from_sq = chess.parse_square(from_square)
        to_sq = chess.parse_square(to_square)
        move = chess.Move(from_sq, to_sq)
        
        print(f"Move in legal moves: {move in board.legal_moves}")
        return move in board.legal_moves
    except Exception as e:
        print(f"Move validation error: {e}")
        return False

def make_move(from_square, to_square):
    """Make a move on the board"""
    try:
        from_sq = chess.parse_square(from_square)
        to_sq = chess.parse_square(to_square)
        move = chess.Move(from_sq, to_sq)
        
        if move in board.legal_moves:
            board.push(move)
            return True
        return False
    except Exception as e:
        print(f"Error making move: {e}")
        return False

def get_engine_move(game_speed=10):
    """Get the engine's move
    
    Args:
        game_speed: Speed multiplier (1-20). Higher = faster. Default 10.
                   Thinking time = 2.0 / game_speed seconds
    """
    if not engine:
        print("Engine not initialized")
        return None
        
    if board.is_game_over():
        print("Game is over, cannot get engine move")
        return None
    
    try:
        print(f"Getting engine move. Board FEN: {board.fen()}")
        print(f"Legal moves: {[board.san(move) for move in list(board.legal_moves)[:10]]}")
        
        # Calculate thinking time based on game speed
        # At speed 1: 2.0 seconds (slow)
        # At speed 10: 0.2 seconds (moderate)
        # At speed 20: 0.1 seconds (fast)
        thinking_time = max(0.1, 2.0 / game_speed)  # Minimum 0.1 seconds
        print(f"Game speed: {game_speed}, Thinking time: {thinking_time:.2f}s")
        
        result = engine.play(board, chess.engine.Limit(time=thinking_time))
        move = result.move
        
        print(f"Engine suggested move: {move}")
        
        if move not in board.legal_moves:
            print(f"Engine tried illegal move: {move}")
            return None
        
        # Get piece and SAN before pushing
        piece = board.piece_at(move.from_square).symbol() if board.piece_at(move.from_square) else None
        san_notation = board.san(move)
        
        # Make the move
        board.push(move)
        global current_player
        current_player = 'black' if current_player == 'white' else 'white'
        print(f"Engine move applied: {move}")
        
        return {
            'from': chess.square_name(move.from_square),
            'to': chess.square_name(move.to_square),
            'piece': piece,
            'san': san_notation
        }
    except Exception as e:
        print(f"Engine move error: {e}")
        return None

@app.route('/api/status', methods=['GET'])
def status():
    """Check server status"""
    return jsonify({
        'status': 'running',
        'engine_connected': engine is not None,
        'game_active': game_active,
        'current_player': current_player,
        'board_fen': board.fen()
    })

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to see board state and legal moves"""
    legal_moves = []
    for move in board.legal_moves:
        legal_moves.append({
            'from': chess.square_name(move.from_square),
            'to': chess.square_name(move.to_square),
            'san': board.san(move)
        })
    
    return jsonify({
        'board_fen': board.fen(),
        'legal_moves': legal_moves,
        'turn': 'white' if board.turn else 'black'
    })

@app.route('/api/move', methods=['POST'])
def handle_move():
    """Handle a move (validate and apply it to this Pi's board)"""
    try:
        data = request.get_json()
        from_square = data.get('from')
        to_square = data.get('to')
        piece = data.get('piece')
        
        print(f"Received move: {from_square} to {to_square}, piece: {piece}")
        print(f"Current board FEN: {board.fen()}")
        
        if not from_square or not to_square:
            print("Error: Missing from or to square")
            return jsonify({
                'status': 'error',
                'message': 'Missing from or to square'
            }), 400
        
        # Validate the move
        if not is_valid_move(from_square, to_square, piece):
            print(f"Move validation failed: {from_square} to {to_square}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid move',
                'move_accepted': False
            }), 400
        
        # Make the move
        if make_move(from_square, to_square):
            # Check if game is over
            game_over = board.is_game_over()
            winner = None
            
            if game_over:
                result = board.result()
                if result == '1-0':
                    winner = 'white'
                elif result == '0-1':
                    winner = 'black'
                else:
                    winner = 'draw'
            
            return jsonify({
                'status': 'success',
                'move_accepted': True,
                'board_state': get_board_state(),
                'game_over': game_over,
                'winner': winner,
                'current_player': 'black' if current_player == 'white' else 'white'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to make move',
                'move_accepted': False
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/engine-move', methods=['POST'])
def handle_engine_move():
    """Get the engine's move"""
    try:
        if not engine:
            return jsonify({
                'status': 'error',
                'message': 'Chess engine not initialized'
            }), 500
        
        if board.is_game_over():
            return jsonify({
                'status': 'error',
                'message': 'Game is over'
            }), 400
        
        # Get game_speed from request (default to 10 if not provided)
        data = request.get_json() or {}
        game_speed = data.get('game_speed', 10)
        # Ensure game_speed is within valid range (1-20)
        game_speed = max(1, min(20, int(game_speed)))
        
        # Get engine move with the specified game speed
        engine_move = get_engine_move(game_speed)
        
        if engine_move:
            # Check if game is over after engine move
            game_over = board.is_game_over()
            winner = None
            
            if game_over:
                result = board.result()
                if result == '1-0':
                    winner = 'white'
                elif result == '0-1':
                    winner = 'black'
                else:
                    winner = 'draw'
            
            return jsonify({
                'status': 'success',
                'engine_move': engine_move,
                'board_state': get_board_state(),
                'game_over': game_over,
                'winner': winner
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get engine move'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Engine error: {str(e)}'
        }), 500

@app.route('/api/board-state', methods=['GET'])
def get_board_state_endpoint():
    """Get current board state"""
    try:
        return jsonify({
            'status': 'success',
            'board_state': get_board_state(),
            'current_player': current_player,
            'game_over': board.is_game_over(),
            'board_fen': board.fen()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting board state: {str(e)}'
        }), 500

@app.route('/api/game-control', methods=['POST'])
def game_control():
    """Handle game control commands"""
    try:
        data = request.get_json()
        command = data.get('command')
        
        if command == 'reset':
            global board, game_active, current_player
            board = chess.Board()
            current_player = 'white'
            return jsonify({
                'status': 'success',
                'message': 'Game reset to starting position',
                'board_state': get_board_state()
            })
        
        elif command == 'pause':
            game_active = False
            return jsonify({
                'status': 'success',
                'message': 'Game paused'
            })
        
        elif command == 'resume':
            game_active = True
            return jsonify({
                'status': 'success',
                'message': 'Game resumed'
            })
        
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown command: {command}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Control error: {str(e)}'
        }), 500

@app.route('/api/set-bot-difficulty', methods=['POST'])
def set_bot_difficulty():
    """Set bot difficulty level (ELO and skill) and optionally configure NNUE"""
    try:
        if not engine:
            return jsonify({
                'status': 'error',
                'message': 'Engine not initialized'
            }), 500
        
        data = request.get_json()
        elo = data.get('elo', 1350)
        skill = data.get('skill', 10)
        use_nnue = data.get('use_nnue', False)
        
        # Ensure ELO is within Stockfish's supported range (1350-2850)
        elo = max(1350, min(2850, elo))
        skill = max(0, min(20, skill))
        
        # Configure the engine with the new settings
        config = {
            "Skill Level": skill,
            "UCI_LimitStrength": True,
            "UCI_Elo": elo
        }
        
        # If NNUE is requested, configure the evaluation file
        if use_nnue:
            if os.path.exists(NNUE_FILE_PATH):
                config["EvalFile"] = NNUE_FILE_PATH
                print(f"Configuring NNUE evaluation file: {NNUE_FILE_PATH}")
            else:
                print(f"Warning: NNUE file not found at {NNUE_FILE_PATH}, using default evaluation")
        
        engine.configure(config)
        
        # Reset the board to starting position when setting difficulty
        global board
        board = chess.Board()
        
        nnue_status = "with NNUE" if use_nnue else "standard evaluation"
        print(f"Bot difficulty set: ELO {elo}, Skill Level {skill}, {nnue_status}")
        print(f"Board reset to starting position")
        
        return jsonify({
            'status': 'success',
            'message': f'Bot difficulty set: ELO {elo}, Skill Level {skill}, {nnue_status}',
            'elo': elo,
            'skill': skill,
            'nnue_enabled': use_nnue,
            'board_state': get_board_state()
        })
        
    except Exception as e:
        print(f"Error setting bot difficulty: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to set bot difficulty: {str(e)}'
        }), 500

def cleanup():
    """Cleanup resources"""
    global engine
    if engine:
        engine.quit()
        print("Chess engine closed")

if __name__ == '__main__':
    print("="*60)
    print("Starting Raspberry Pi Chess Server (Simplified)")
    print("This Pi will respond to GUI commands")
    print("="*60)
    
    # Initialize chess engine
    if initialize_engine():
        print("Server ready! Listening on port 5002")
        try:
            app.run(host='0.0.0.0', port=5002, debug=False)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            cleanup()
    else:
        print("Failed to initialize chess engine. Server cannot start.")
