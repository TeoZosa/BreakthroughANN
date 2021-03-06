
from Breakthrough_Player import breakthrough_player
from multiprocessing import freeze_support
from monte_carlo_tree_search.MCTS import  NeuralNetsCombined_128
import os
import gc
def play_games(time_to_think, num_games_to_play, white_player, black_opponent, policy_net):
    print(time_to_think)
    date = r'06212017'
    file_designator = '1_0699NetWin_WHITE_bothWinningNet_04UCTThreshOrPP'#''NoPruningNoBatch'#'10KSearches_origPruning_norm4Ago_Stoch'
    white_wins = 0
    black_wins = 0
    depth_limit = 1
    gc.disable()

    for i in range(0, num_games_to_play):
        root = None
        # path = OSX_path = str(time_to_think)

        path = Windows_path
        gameplay_file = open(os.path.join(path,
                                          r'{date}move_'  # {opponent}vsWanderer'
                                          r'depth{depth}_'
                                          r'ttt{time_to_think}{designator}.txt'.format(date=date,
                                                                                       opponent=player_for_path,
                                                                                       designator=file_designator,
                                                                                       depth=depth_limit,
                                                                                       time_to_think=time_to_think)),
                             'a')

        MCTS_logging_file = open(os.path.join(path,
                                              r'{date}log_'  # {opponent}vsWanderer'
                                              r'depth{depth}_'
                                              r'ttt{time_to_think}{designator}_{i}.txt'.format(i=i, date=date,
                                                                                               opponent=player_for_path,
                                                                                               designator=file_designator,
                                                                                               depth=depth_limit,
                                                                                               time_to_think=time_to_think)),
                                 'a')
        winner_color = breakthrough_player.play_game_vs_wanderer(white_player, black_opponent, depth_limit,
                                                                 time_to_think, gameplay_file,
                                                                 MCTS_logging_file, root, i, policy_net)
        if winner_color is not None:
            if winner_color == 'White':
                white_wins += 1
            else:
                black_wins += 1
            print("Game {game}  White Wins: {white_wins}    Black Wins: {black_wins}".format(
                game=i + 1, white_wins=white_wins, black_wins=black_wins), file=gameplay_file)
            print("game ended")
        else:
            print("ERROR: Wanderer failed to open".format(
                game=i + 1, white_wins=white_wins, black_wins=black_wins), file=gameplay_file)

        gameplay_file.close()
        MCTS_logging_file.close()
        gc.collect() #garbage collect between games


if __name__ == '__main__':#for Windows since it lacks os.fork
    freeze_support()

    num_games_to_play = 505 #in case some
    time_to_think = 150

    human = 'Human'
    wanderer = 'Wanderer'

    random_moves = 'Random'
    policy = "Policy"
    WaNN = 'WaNN'
    policy = "Policy"
    Windows_path = r'G:\TruncatedLogs\PythonDatasets\10ttt'
    OSX_path = r'/Users/TeofiloZosa/Dropbox/WaNNLogs/'
    player_for_path = WaNN
    white_player = WaNN
    black_opponent = wanderer

#REG COMBINED SWITCHED COLORS
    # policy_net = None# NeuralNetsCombined_128()
    with NeuralNetsCombined_128() as policy_net:
        multiproc_args = [
                        [1, num_games_to_play, white_player, black_opponent, policy_net],
                        [2, num_games_to_play, white_player, black_opponent, policy_net],
                        [3, num_games_to_play, white_player, black_opponent, policy_net],
                        [4, num_games_to_play, white_player, black_opponent, policy_net],
                        [5, num_games_to_play, white_player, black_opponent, policy_net],
                        [6, num_games_to_play, white_player, black_opponent, policy_net],
                        [7, 431, white_player, black_opponent, policy_net],
        #                   [8, num_games_to_play, white_player, black_opponent, policy_net],
        #                   [9, num_games_to_play, white_player, black_opponent, policy_net],
        #                   [10, num_games_to_play, white_player, black_opponent, policy_net]
        ]
        # multiproc_args = [[ttt, num_games_to_play, white_player, black_opponent, policy_net] for ttt in range(1,11)]
        play_games(time_to_think, num_games_to_play, white_player, black_opponent, policy_net)
  # pool = ThreadPool(processes=4)
  # pool.starmap_async(play_games, multiproc_args)
  # pool.close()
  # pool.join()
# from Breakthrough_Player import breakthrough_player
# from multiprocessing import freeze_support
# import os
# import pickle
# from copy import deepcopy
# # from time import  sleep
# import gc
# if __name__ == '__main__':#for Windows since it lacks os.fork
#   freeze_support()
#
#   white_wins = 0
#   black_wins = 0
#
#   num_games_to_play = 501
#   time_to_think = 10
#   depth_limit = 5
#   date = r'05222017'
#   file_designator = '0699EPch14WinNet_NNScale1_4TL_UCTChoosableOnlyMostRootPlus_GCManual'
#   #BatchExpansionsH40_Depth80__3at40to65_2at65to69_3at70_WM_2at40to51_3at52to60_2at61to69BM
#   expansion_MCTS = 'Expansion MCTS'
#   expansion_MCTS_pruning = 'Expansion MCTS Pruning'
#   expansion_MCTS_post_pruning = 'Expansion MCTS Post-Pruning'
#   async_MCTS = 'MCTS Asynchronous'
#
#   human = 'Human'
#   wanderer = 'Wanderer'
#
#   random_moves = 'Random'
#   BFS_MCTS = 'BFS MCTS'
#   WaNN = 'WaNN'
#   policy = "Policy"
#   # player_for_path = 'EMCTSPruning'
#   player_for_path = WaNN
#   Windows_path = r'G:\TruncatedLogs\PythonDatasets\10ttt'
#   OSX_path = r'/Users/TeofiloZosa/BreakthroughData/03122017SelfPlay'
#   path = Windows_path
#   white_player = WaNN
#   black_opponent = wanderer
#   # root = None
#
#   # # input_file = open(
#   # #     r'G:\TruncatedLogs\PythonDataSets\DataStructures\GameTree\AgnosticRoot{}.p'.format(str(6)),
#   # #     'r+b')
#   # input_file = open(
#   #     r'G:\TruncatedLogs\PythonDataSets\DataStructures\GameTree\0409201710secsDepth80_TrueWinLossFieldBlack{}.p'.format(
#   #         str(17)),  # 17?
#   #     'r+b')
#   # original_root = pickle.load(input_file)
#   # input_file.close()
#
#   gc.disable() #don't spend time garbage collecting
#
#   for time_to_think in range(10, 1001, 10):
#       for depth_limit in range(1, 2):
#           white_wins = 0
#           black_wins = 0
#           for i in range(0, num_games_to_play):
#             # input_file = open(
#             #       r'G:\TruncatedLogs\PythonDataSets\DataStructures\GameTree\0409201710secsDepth80_TrueWinLossFieldBlack{}.p'.format(
#             #           str(17)),  # 17?
#             #       'r+b')
#             # root = pickle.load(input_file)
#             # input_file.close()
#             root=None
#             gameplay_file = open(os.path.join(path,
#                                               r'{date}move_'#{opponent}vsWanderer'
#                                               r'depth{depth}_'
#                                               r'ttt{time_to_think}{designator}.txt'.format(date=date,
#                                                                                            opponent=player_for_path,
#                                                                                            designator=file_designator,
#                                                                                            depth=depth_limit,
#                                                                                            time_to_think=time_to_think)),
#                                  'a')
#
#             MCTS_logging_file = open(os.path.join(path,
#                                                     r'{date}log_'#{opponent}vsWanderer'
#                                                     r'depth{depth}_'
#                                                     r'ttt{time_to_think}{designator}_{i}.txt'.format(i=i,date=date, opponent=player_for_path,
#                                                                                                  designator=file_designator,
#                                                                                                  depth=depth_limit,
#                                                                                                  time_to_think=time_to_think)),
#                                        'a')
#             winner_color =   breakthrough_player.play_game_vs_wanderer(white_player, black_opponent, depth_limit, time_to_think, gameplay_file, MCTS_logging_file, root, i)
#             if winner_color is not None:
#                 if winner_color == 'White':
#                   white_wins += 1
#                 else:
#                   black_wins += 1
#                 print("Game {game}  White Wins: {white_wins}    Black Wins: {black_wins}".format(
#                     game=i+1, white_wins=white_wins, black_wins=black_wins ), file=gameplay_file)
#                 print("game ended")
#             else:
#                 print("Error: Wanderer didn't open properly", file=gameplay_file)
#
#             gameplay_file.close()
#             MCTS_logging_file.close()
#             gc.collect() #gc between games
#
#       #       bonus = 1;
#       #       supportct = 0;
#       #       enemyct = 0;
#       #       if (column > 0 & & column - 1 != wpt[p]->getColumn() & & board[row-1][column-1].getColor() == WHITE )
#       #       supportct + +;
#       #     if (column < base - 1 & & column + 1 != wpt[p]->getColumn() & & board[row-1][column+1].getColor() == WHITE )
#       #     supportct + +;
#       #
#       # if (column > 0 & & board[row + 1][column - 1].getColor() == BLACK)
#       #     enemyct + +;
#       # if (column < base - 1 & & board[row + 1][column + 1].getColor() == BLACK)
#       #     enemyct + +;
#       #
#       # if (supportct >= enemyct)
#       #     {
#       #     if (board[row][column].getColor() != NONE)
#       #     bonus += 50; // gain
#       #     a
#       #     piece
#       #     else
#       #     bonus += 20; // safe
#       #     move
#       #     }
#       #     else
#       #     {
#       #     if (board[row][column].getColor() != NONE)
#       #     {
#       #     if (gameprog >= 70 & & row >= base / 2)
#       #     bonus += 1; // early
#       #     capture in enemy
#       #     territory
#       #     else if (row <= 3)
#       #     bonus += 30; // captures are always safe  -- same bonus as safe move
#       #     else
#       #     bonus += 5;
#       #     }
#       #     }
#       #
#       #     if (row == base - 3)
#       #         bonus *= 3;
#       #     else if (row == base - 4)
#       #     bonus *= 2;
#       #
#       # bonus = 1 + (bonus - 1) * gameprog / 100;
#       #
#       # legalMove += bonus;
#       # if (ran_num[thread].Integer(legalMove) <= bonus)
#       #     {
#       #         rand_FromRow = row - 1;
#       #     rand_FromCol = wpt[p]->getColumn();
#       #     rand_ToRow = row;
#       #     rand_ToCol = column;
#       #     }