"""
Raspberry Pi Chess Server (Simplified for GUI Coordination)
Handles chess engine communication and game logic for the AI Chess project.
This server runs on the Raspberry Pi and communicates with the laptop GUI.

The GUI coordinates all moves - this Pi just maintains board state and calculates moves when asked.
"""

# Import Libraries
import chess
import chess.engine
from flask import Flask, request, jsonify
import json
import time
import os
import socket

# Call Flask
app = Flask(__name__)

# Global game state
board = chess.Board()
engine = None
game_active = False
current_player = "black"

# NNUE file paths (absolute paths)
NNUE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nnue'))
CARLSEN_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'carlsen_halfkav2_hm.nnue')
FISCHER_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'fischer_01.nnue')
YIFAN_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'yifan.nnue')
SPASSKY_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'spassky.nnue')
NAKAMURA_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'nakamura.nnue')
KRUSH_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'krush.nnue')
POLGAR_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'polgar.nnue')
ANAND_NNUE_PATH = os.path.join(NNUE_BASE_DIR, 'anand.nnue')

# Create Socket Port
HOST = "127.0.0.1"
PORT1 = 1234
PORT2 = 4321
s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s1.connect((HOST,PORT1)) ############### Code will crash if LCD code is not running!
s2.connect((HOST,PORT2))  ############### Code will crash if LED code is not running!

# Send to LED and lcd the Selection and draw screen while you wait for user to select overlay options
s1.sendall(b"selection\n")
s2.sendall(b"draw\n")

# Global variable to count number of wins
global_win_counter = 0;

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
        # get the whole board where all the pieces are on the board
        if piece:
            square_name = chess.square_name(square)
            piece_symbol = piece.symbol()
            board_state[square_name] = piece_symbol
    return board_state

def is_valid_move(from_square, to_square, piece_code):
    """Validate if a move is legal"""
    try:
        # Validate the moves the engine or player is trying to make
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
    print("!!!!!!!!!!!!!!!!MAKE_MOVE!!!!!!!!!!!!!")
    """Make a move on the board"""
    try:
        # Actually make the Move
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
    global global_win_counter
    global wdl
    if not engine:
        print("Engine not initialized")
        return None
        
    if board.is_game_over():
        print("Game is over, cannot get engine move")
        return None
    
    try:
        # Start thinking animaiton on LED and lcd screen
        #hardware.start_animation("thinking")        
        s1.sendall(f"score\n{global_win_counter}\n".encode())
        s2.sendall(b"thinking\n")
        # print(f"Getting engine move. Board FEN: {board.fen()}")
        legal_moves_list = list(board.legal_moves)
        # print(f"Legal moves count: {len(legal_moves_list)}")
        if legal_moves_list:
            print(f"Sample legal moves: {[board.san(move) for move in legal_moves_list[:10]]}")

        # Calculate thinking time based on game speed
        # At speed 1: 2.0 seconds (slow)
        # At speed 10: 0.2 seconds (moderate)
        # At speed 20: 0.1 seconds (fast)
        thinking_time = max(0.1, 2.0 / game_speed)  # Minimum 0.1 seconds
        # Cap maximum thinking time at 5 seconds to prevent long hangs
        thinking_time = min(thinking_time, 5.0)
        print(f"Game speed: {game_speed}, Thinking time: {thinking_time:.2f}s")
        
        # Use a timeout limit to prevent hanging (max 30 seconds total)
        time_limit = min(thinking_time * 2, 30.0)
        
        result = engine.play(board, chess.engine.Limit(time=thinking_time), info=chess.engine.Info.ALL)
        move = result.move
        info = result.info

        # Extract the WDL Probabilites
        if 'wdl' in info:
            wdl = info['wdl'].white()
            total = wdl.wins + wdl.draws + wdl.losses

            # Return the win loss and draw probabilities based on state of board
            if total > 0:
                wdl_stats = {
                    'win': round((wdl.wins / total) * 100, 1), 
                    'draw': round((wdl.draws / total) * 100, 1),
                    'loss': round((wdl.losses / total) * 100, 1)
                }
        
        print(f"Engine suggested move: {move}")
        
        # Double-check move is legal (should always be, but safety check)
        if move not in board.legal_moves:
            print(f"ERROR: Engine tried illegal move: {move}")
            print(f"Legal moves: {[str(m) for m in board.legal_moves]}")
            return None
        
        # Get piece and SAN before pushing
        piece = board.piece_at(move.from_square).symbol() if board.piece_at(move.from_square) else None
        san_notation = board.san(move)
        
        # Make the move
        board.push(move)        
     
        return {
            'from': chess.square_name(move.from_square),
            'to': chess.square_name(move.to_square),
            'piece': piece,
            'san': san_notation,
            'wdl': wdl_stats
        }

    except chess.engine.EngineTerminatedError as e:
        print(f"ERROR: Engine terminated unexpectedly: {e}")
        print("Attempting to reinitialize engine...")
        # Try to reinitialize the engine
        if initialize_engine():
            print("Engine reinitialized successfully")
            return None  # Return None so caller can retry
        else:
            print("Failed to reinitialize engine")
            return None
    except Exception as e:
        print(f"Engine move error: {e}")
        import traceback
        traceback.print_exc()
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

# Debug and retrieve data from the server
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

# This will send the move request to the server
@app.route('/api/move', methods=['POST'])
def handle_move():
    """Handle a move (validate and apply it to this Pi's board)"""
    global global_win_counter
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
            
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
            print(f"Current legal moves: {[board.san(move) for move in list(board.legal_moves)[:10]]}")
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
                print("======= NUMBA 1 ========")
                result = board.result()
                if result == '1-0':
                    winner = 'white'
                    print(f"!!!!!!!!!!!! WINNER {winner} !!!!!!!!!!!!!!!")
                    print(f"!!!!!!!!!!!! I AM {current_player} !!!!!!!!!!!!!!!")
                    if current_player == 'white':
                        s1.sendall(b"victory\n")
                        print("RESULT IF WIN: ", board.result())
                        s2.sendall(b"win\n")
                        global_win_counter += 1
                    else:
                        s1.sendall(b"lose\n")
                        s2.sendall(b"lose\n")
                        
                elif result == '0-1':
                    winner = 'black'
                    print(f"!!!!!!!!!!!! WINNER {winner} !!!!!!!!!!!!!!!")
                    if current_player == 'black':
                        s1.sendall(b"victory\n")
                        s2.sendall(b"win\n")
                    else:
                        s1.sendall(b"lose\n")
                        s2.sendall(b"lose\n")
                    
                else:
                    winner = 'draw'
                    s1.sendall(b"draw\n")
                    s2.sendall(b"draw\n")
                    
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
        print(f"Exception in handle_move: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/engine-move', methods=['POST'])
def handle_engine_move():
    """Get the engine's move"""
    global global_win_counter
    try:
        if not engine:
            # Try to reinitialize engine
            print("Engine not initialized, attempting to reinitialize...")
            if initialize_engine():
                print("Engine reinitialized successfully")
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Chess engine not initialized and reinitialization failed'
                }), 500
        
        # If the game is already over (checkmate / stalemate / draw), do NOT error.
        # Return a clean success response so the GUI can end/restart gracefully.
        if board.is_game_over():
            print("======= NUMBA 2 Chat IFK if this ever happens  ========")
            result = board.result()
            if result == '1-0':
                winner = 'white'
                # if current_player == 'white':
                #     s1.sendall(b"victory\n")
                #     s2.sendall(b"win\n")
                # else:
                #     s1.sendall(b"lose\n")
                #     s2.sendall(b"lose\n")

            elif result == '0-1':
                winner = 'black'
                # if current_player == 'black':
                #     s1.sendall(b"victory\n")
                #     s2.sendall(b"win\n")
                # else:
                #     s1.sendall(b"lose\n")
                #     s2.sendall(b"lose\n")

            else:
                winner = 'draw'
                # s1.sendall(b"draw\n")
                # s2.sendall(b"draw\n")

                
            return jsonify({
                'status': 'success',
                'engine_move': None,
                'board_state': get_board_state(),
                'game_over': True,
                'winner': winner,
                'message': 'Game is over'
            }), 200
        
        # Get game_speed from request (default to 10 if not provided)
        data = request.get_json() or {}
        game_speed = data.get('game_speed', 10)
        # Ensure game_speed is within valid range (1-20)
        try:
            game_speed = max(1, min(20, int(game_speed)))
        except (ValueError, TypeError):
            game_speed = 10  # Default to 10 if invalid
        
        # Get engine move with the specified game speed
        engine_move = get_engine_move(game_speed)
        
        if engine_move:
            # Check if game is over after engine move
            game_over = board.is_game_over()
            winner = None
            
            if game_over:
                print("======= NUMBA 3 ========")
                result = board.result()
                if result == '1-0':
                    winner = 'white'
                    print(f"!!!!!!!!!!!! WINNER {winner} !!!!!!!!!!!!!!!")
                    print(f"!!!!!!!!!!!! I AM {current_player} !!!!!!!!!!!!!!!")
                    if current_player == 'white':
                        s1.sendall(b"victory\n")
                        s2.sendall(b"win\n")
                        global_win_counter += 1
                        print("RESULT IF WIN: ", board.result())
                        
                    else:
                        s1.sendall(b"lose\n")
                        s2.sendall(b"lose\n")
                        
                elif result == '0-1':
                    winner = 'black'
                    print(f"!!!!!!!!!!!! WINNER {winner} !!!!!!!!!!!!!!!")
                    if current_player == 'black':
                        s1.sendall(b"victory\n")
                        s2.sendall(b"win\n")
                    else:
                        s1.sendall(b"lose\n")
                        s2.sendall(b"lose\n")

                else:
                    winner = 'draw'
                    s1.sendall(b"draw\n")
                    s2.sendall(b"draw\n")
                    
            return jsonify({
                'status': 'success',
                'engine_move': engine_move,
                'board_state': get_board_state(),
                'game_over': game_over,
                'winner': winner
            })
        else:
            # If engine move failed, try to check if engine is still alive
            try:
                # Quick health check
                test_result = engine.ping()
                if test_result is None:
                    raise Exception("Engine ping failed")
            except Exception as e:
                print(f"Engine health check failed: {e}")
                # Try to reinitialize
                if initialize_engine():
                    print("Engine reinitialized after health check failure")
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Engine failed and could not be reinitialized'
                    }), 500
            
            return jsonify({
                'status': 'error',
                'message': 'Failed to get engine move (engine may be busy or unresponsive)'
            }), 500
            
    except Exception as e:
        print(f"Exception in handle_engine_move: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Engine error: {str(e)}'
        }), 500

@app.route('/api/board-state', methods=['GET'])
def get_board_state_endpoint():
    """Get current board state"""
    try:
        game_over = board.is_game_over()
        winner = None
        
        if game_over:
            print("======= NUMA 4 Chat IDK if this happens ever ========")
            result = board.result()
            if result == '1-0':
                winner = 'white'
                # if current_player == 'white':
                #     s1.sendall(b"victory\n")
                #     s2.sendall(b"win\n")
                # else:
                #     s1.sendall(b"lose\n")
                #     s2.sendall(b"lose\n")

            elif result == '0-1':
                winner = 'black'
                # if current_player == 'black':
                #     s1.sendall(b"victory\n")
                #     s2.sendall(b"win\n")
                # else:
                #     s1.sendall(b"lose\n")
                #     s2.sendall(b"lose\n")
           
            else:
                winner = 'draw'
                # s1.sendall(b"draw\n")
                # s2.sendall(b"draw\n")
        
        return jsonify({
            'status': 'success',
            'board_state': get_board_state(),
            'current_player': current_player,
            'game_over': game_over,
            'winner': winner,
            'board_fen': board.fen()
        })
    except Exception as e:
        print(f"Error getting board state: {e}")
        import traceback
        traceback.print_exc()
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
    global global_win_counter
    global board
    
    #  Reset win back to zero
    if board.result() == "*":
        global_win_counter = 0;
        
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
        nnue_model = data.get('nnue_model', 'carlsen')  
        
        # Ensure ELO is within Stockfish's supported range (1350-2850)
        elo = max(1350, min(2850, elo))
        skill = max(0, min(20, skill))
        
        # Configure the engine with the new settings
        config = {
            "Skill Level": skill,
            "UCI_LimitStrength": True,
            "UCI_Elo": elo,
            "UCI_ShowWDL": True
        }
        
        # If NNUE is requested, configure the evaluation file
        if use_nnue:
            # Select the appropriate NNUE file based on model
            if nnue_model == 'fischer':
                nnue_path = FISCHER_NNUE_PATH
            elif nnue_model == 'yifan':
                nnue_path = YIFAN_NNUE_PATH
            elif nnue_model == 'spassky':
                nnue_path = SPASSKY_NNUE_PATH
            elif nnue_model == 'nakamura':
                nnue_path = NAKAMURA_NNUE_PATH
            elif nnue_model == 'krush':
                nnue_path = KRUSH_NNUE_PATH
            elif nnue_model == 'polgar':
                nnue_path = POLGAR_NNUE_PATH
            elif nnue_model == 'anand':
                nnue_path = ANAND_NNUE_PATH
            else:  # default to carlsen
                nnue_path = CARLSEN_NNUE_PATH
            
            if os.path.exists(nnue_path):
                config["EvalFile"] = nnue_path
                print(f"Configuring NNUE evaluation file: {nnue_path} (model: {nnue_model})")
            else:
                print(f"Warning: NNUE file not found at {nnue_path}, using default evaluation")
        
        engine.configure(config)
        
        # Reset the board to starting position when setting difficulty
        board = chess.Board()
        
        nnue_status = f"with NNUE ({nnue_model})" if use_nnue else "standard evaluation"
        print(f"Bot difficulty set: ELO {elo}, Skill Level {skill}, {nnue_status}")
        print(f"Board reset to starting position")
        
        return jsonify({
            'status': 'success',
            'message': f'Bot difficulty set: ELO {elo}, Skill Level {skill}, {nnue_status}',
            'elo': elo,
            'skill': skill,
            'nnue_enabled': use_nnue,
            'nnue_model': nnue_model if use_nnue else None,
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
        print("Configured for long-running operation with improved error handling")
        try:
            # Use threaded mode for better concurrent request handling
            app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"\nFatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cleanup()
    else:
        print("Failed to initialize chess engine. Server cannot start.")
