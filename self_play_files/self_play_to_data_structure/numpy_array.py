import pickle
import numpy as np
import pandas as pd
import warnings
import h5py
import os
import random
import math
from tools.utils import index_lookup_by_move
# from Breakthrough_Player.policy_net_utils import instantiate_session_both_RNN

#TODO: redo logic and paths after directory restructuring
def write_np_array_to_disk(path, X, y, filterType, NNType):
    if filterType == r'Rank':
        XMatrix = open(path + r'XMatrixByRank.p', 'wb')
        pickle.dump(X, XMatrix)
        yVector = open(path + r'yVectorByRank.p', 'wb')
        pickle.dump(y, yVector)
    elif filterType == r'Win Ratio':
        XMatrix = open(path + r'XMatrixByWinRatio.p', 'wb')
        pickle.dump(X, XMatrix)
        yVector = open(path + r'yVectorByWinRatio.p', 'wb')
        pickle.dump(y, yVector)
    elif filterType == r'Binary Rank':
        XMatrix = open(path + r'value_net_rank_binary/NPDataSets/WBPOE/XMatrixByRankBinaryFeaturesWBPOEBiasNoZero.p', 'wb')
        pickle.dump(X, XMatrix)
        yVector = open(path + r'value_net_rank_binary/NPDataSets/WBPOE/yVectorByRankBinaryFeaturesWBPOEBiasNoZero.p', 'wb')
        pickle.dump(y, yVector)
    elif filterType == r'Self-Play':
        h5f = h5py.File(path + r'POEB.hdf5', 'w', driver='core')
        h5f.create_dataset(r'X', data=X)
        h5f.create_dataset(r'y', data=y)
        h5f.close()
    elif filterType == r'RNN':
        h5f = h5py.File(path + r'RNN40Inputs.hdf5', 'w', driver='core')
        h5f.create_dataset(r'X', data=X)
        h5f.create_dataset(r'y', data=y)
        h5f.close()
    elif filterType == r'CNN RNN':
        # XMatrix = open(path + r'X_CNNRNNSeparatedGames.p', 'wb')
        # pickle.dump(X, XMatrix)
        # yVector = open(path + r'y_CNNRNNSeparatedGames.p', 'wb')
        # pickle.dump(y, yVector)
        h5f = h5py.File(path + r'CNNRNNSeparatedGames.hdf5', 'w', driver='core')
        h5f.create_dataset(r'X', data=X)
        h5f.create_dataset(r'y', data=y)
        h5f.close()
    else:
        print ("Error: You must specify a valid Filter")

def filter_training_examples_and_labels(player_list, filter, NNType='ANN', game_stage='All', color='Both', policy_net=None):
    labels = None
    if filter == 'Win Ratio':
        training_data = filter_by_win_ratio(player_list)
    elif filter == 'Rank':
        training_data = filter_by_rank(player_list)
    elif filter == 'Self-Play':
        training_data = filter_for_self_play(player_list, NNType, game_stage, color)
    elif filter =='RNN':
        training_data, labels = filter_for_self_play_RNN(player_list, NNType, game_stage, color)
    elif filter =='CNN RNN':
        training_data = filter_for_self_play_CNN_RNN(player_list, NNType, game_stage, color)
        # sess, y_pred_white, X_white, y_pred_black, X_black = instantiate_session_both_RNN()
        # if color == 'White':
        #     output = y_pred_white
        #     input = X_white
        # elif color =='Black':
        #     output = y_pred_black
        #     input = X_black
        training_data, labels = split_data_to_training_examples_and_labels_for_CNN_RNN(training_data, NNType, policy_net, color)
    else:
        training_data = None
        print('Invalid Filter Specified')
        exit(-2)
    if labels is None:
        training_examples, labels = split_data_to_training_examples_and_labels_for_CNN(training_data, NNType)
    else:
        training_examples = training_data
    return np.array(training_examples, dtype=np.float32), np.array(labels, dtype=np.float32)


def filter_by_rank(playerList):
    X = []
    for player in playerList:
        if player['Rank'] >=2000:#Good players only
            for game in player['Games']:
                states = game['BoardStates']['States']
                mirrorStates = game['BoardStates']['MirrorStates']
                assert len(states) == len(mirrorStates)
                for i in range (0, len(states)):
                  X.append(states[i])
                  X.append(mirrorStates[i])
    print ('# of States If We Filter by Rank: {states}'.format(states=len(X)))
    return X

def filter_by_win_ratio(playerList):
    X = []
    for player in playerList:
        if player['Wins'] > 0 and player['Wins']/(player['Wins']+player['Losses']) >= .8:  # >=80% win rate
            for game in player['Games']:
                states = game['BoardStates']['States']
                mirrorStates = game['BoardStates']['MirrorStates']
                assert len(states) == len(mirrorStates)
                for i in range(0, len(states)):
                    X.append(states[i])
                    X.append(mirrorStates[i])
    print ('# of States If We Filter by Win Ratio: {states}'.format(states = len(X)))
    return X

def filter_for_self_play_CNN_RNN(self_play_data, NNType, game_stage='All', color='Both', shuffle=False, percent=50):
    training_data = []
    training_labels = []

    for self_play_log in self_play_data:
        i = 0
        for game in self_play_log['Games']: #each game is appended twice; White's game, then Black's game
            if color == 'White': #train on all white games
                color_to_filter = i % 2 == 0
                # win_filter = True
                win_filter = game['Win'] is True
            elif color =='Black': #only train on winning black games
                color_to_filter = i % 2 == 1
                win_filter = game['Win'] is True
            else:
                color_to_filter = True
                win_filter = True

            if color_to_filter:
                i+=1
                if win_filter:
                    game_length = len(game['BoardStates']['States'])
                    if game_stage == 'All':
                        start = 0
                        end = game_length
                    elif game_stage == '1st':
                        # Start-Game Value Net
                        start = 0
                        end = math.floor(game_length / 3)
                    elif game_stage == '2nd':
                        # Mid-Game Value Net
                        start = math.floor(game_length / 3)
                        end = math.floor(game_length / 3) * 2
                    elif game_stage == '3rd':
                        # End-Game Value Net
                        start = math.floor(game_length / 3) * 2
                        end = game_length
                    states = game['BoardStates']['States'][start:end]
                    # POV_states = game['BoardStates']['PlayerPOV'][start:end]

                    mirror_states = game['MirrorBoardStates']['States'][start:end]
                    if NNType == 'Policy':#TODO: unshuffle these?
                        num_random_states = len(states)
                    elif NNType == 'Value':
                        num_random_states = math.floor(len(states) * (percent/100))   #x% of moves
                        #if num_random_states == len(states), mixes state order to decorrelate NN training examples
                    else:
                        print('Invalid NN for self-play')
                        exit(-1)
                    if shuffle:
                        states_random_subset = random.sample(states, num_random_states)
                        mirror_states_random_subset = random.sample(mirror_states, num_random_states)
                    else:
                        states_random_subset = states
                        mirror_states_random_subset = mirror_states

                    training_data.append(states_random_subset)
                    training_data.append(mirror_states_random_subset)
            else:
                i+=1
    print('# of Games for Self-Play {NNType} CNN LSTM Game Stage {game_stage}: {states}'.format(states=len(training_data), NNType=NNType, game_stage=game_stage))
    return training_data
def filter_for_self_play(self_play_data, NNType, game_stage='All', color='Both', percent=50):
    training_data = []

    for self_play_log in self_play_data:
        i = 0
        for game in self_play_log['Games']: #each game is appended twice; White's game, then Black's game
            if color == 'White': #train on all white games
                color_to_filter = i % 2 == 0
                # win_filter = True
                win_filter = game['Win'] is True
            elif color =='Black': #only train on winning black games
                color_to_filter = i % 2 == 1
                # win_filter = game['Win'] is True
                win_filter = True
            elif color =='WINNR': #only train on winning games from both colors
                color_to_filter = True
                win_filter = game['Win'] is True
            elif color =='ALLMV': #train on all games from both colors
                color_to_filter = True
                # win_filter = game['Win'] is True
                win_filter = True

            else:
                color_to_filter = True
                win_filter = True

            if color_to_filter:
                i+=1
                if win_filter:
                    game_length = len(game['BoardStates']['PlayerPOV'])
                    if game_stage == 'All':
                        start = 0
                        end = game_length
                        if game['BoardStates']['PlayerPOV'][end-1][2][154] == 1:
                            end -=1
                    elif game_stage == '1st':
                        # Start-Game Value Net
                        start = 0
                        # end = math.floor(game_length / 3)
                        end = 10
                    elif game_stage == '2nd':
                        # Mid-Game Value Net
                        # start = math.floor(game_length / 3)
                        # end = math.floor(game_length / 3) * 2
                        start = 10
                        end = 30
                    elif game_stage == '3rd':
                        # End-Game Value Net
                        # start = math.floor(game_length / 3) * 2
                        start = 30
                        end = game_length
                        if game['BoardStates']['PlayerPOV'][end - 1][2][154] == 1:
                            end -= 1
                    states = game['BoardStates']['PlayerPOV'][start:end]
                    mirror_states = game['MirrorBoardStates']['PlayerPOV'][start:end]
                    if NNType == 'Policy':#TODO: unshuffle these?
                        num_random_states = len(states)
                    elif NNType == 'Value':
                        num_random_states = math.floor(len(states) * (percent/100))   #x% of moves
                        #if num_random_states == len(states), mixes state order to decorrelate NN training examples
                    else:
                        print('Invalid NN for self-play')
                        exit(-1)
                    shuffle = False
                    # if shuffle:
                    states_random_subset = random.sample(states, num_random_states)
                    mirror_states_random_subset = random.sample(mirror_states, num_random_states)
                    training_data.extend(states_random_subset)
                    training_data.extend(mirror_states_random_subset)
            else:
                i+=1
    print('# of States for Self-Play {NNType} Net Game Stage {game_stage}: {states}'.format(states=len(training_data), NNType=NNType, game_stage=game_stage))
    return training_data

def filter_for_self_play_RNN(self_play_data, NNType, game_stage='All', color='Both'):
    training_data = []
    labels_for_data = []

    for self_play_log in self_play_data:
        i = 0
        for game in self_play_log['Games']: #each game is appended twice; White's game, then Black's game
            if color == 'White': #train on all white games
                color_to_filter = i % 2 == 0
                # win_filter = True
                win_filter = game['Win'] is True
            elif color =='Black': #only train on winning black games
                color_to_filter = i % 2 == 1
                win_filter = game['Win'] is True
            else:
                color_to_filter = True
                win_filter = True

            if color_to_filter:
                i+=1
                if win_filter:
                    move_list, processed_move_list, mirror_move_list, processed_mirror_move_list = get_formatted_move_lists(game)
                    window_size = 40 #Don't forget to add 39 empty values for first move
                    num_moves = 155
                    k = 0
                    training_examples = []
                    mirror_training_examples = []
                    labels = []
                    mirror_labels = []
                    while k  <len(move_list):
                        if k % 2 == 1:
                            offset = 1
                        else:
                            offset = 0
                        training_examples.append(processed_move_list[k:k+window_size])
                        one_hot_label = np.zeros([155], dtype=np.float32)
                        one_hot_label[move_list[k]-(offset*num_moves)] = 1.0
                        labels.append(one_hot_label)

                        mirror_training_examples.append(processed_mirror_move_list[k:k+window_size])
                        one_hot_mirror_label = np.zeros([155], dtype=np.float32)
                        one_hot_mirror_label[mirror_move_list[k]-(offset*num_moves)] = 1.0
                        mirror_labels.append(one_hot_mirror_label)
                        k+=1
                    #TODO: UNSHUFFLED sorta
                    training_data.extend(np.array(training_examples, dtype=np.float32))
                    training_data.extend(np.array(mirror_training_examples, dtype=np.float32))

                    labels_for_data.extend(np.array(labels, dtype=np.float32))
                    labels_for_data.extend(np.array(mirror_labels, dtype=np.float32))


            else:
                i+=1
    print('# of States for Self-Play Recurrent {NNType} Net Game Stage {game_stage}: {states}'.format(states=len(training_data), NNType=NNType, game_stage=game_stage))
    return np.array(training_data, dtype=np.float32), np.array(labels_for_data, dtype=np.float32)

def get_formatted_move_lists(game):
    raw_move_list = game['OriginalVisualizationURL'][len(
        r'http://www.trmph.com/breakthrough/board#8,'):]
    raw_mirror_move_list = game['MirrorVisualizationURL'][len(r'http://www.trmph.com/breakthrough/board#8,'):]

    move_list = parse_move_list_string(raw_move_list)
    mirror_move_list = parse_move_list_string(raw_mirror_move_list)

    moves_as_indexes_list = convert_formatted_move_list_to_indexes(move_list)
    mirror_moves_as_indexes_list = convert_formatted_move_list_to_indexes(mirror_move_list)

    formatted_move_list = preprocess_move_list(move_list)
    formatted_mirror_move_list = preprocess_move_list(mirror_move_list)

    converted_move_list = convert_formatted_move_list_to_indexes(formatted_move_list)
    converted_mirror_move_list = convert_formatted_move_list_to_indexes(formatted_mirror_move_list)

    return moves_as_indexes_list, converted_move_list, mirror_moves_as_indexes_list, converted_mirror_move_list

def parse_move_list_string(move_list):
    window_size = 4
    parsed_move_list = []
    i = 0
    while (i+1)*window_size < len(move_list):
        move = move_list[i*window_size:(i+1)*window_size]
        move = move[0:2] + '-' + move[2:len(move)]
        parsed_move_list.append(move)
        i+=1
    return parsed_move_list

def convert_formatted_move_list_to_indexes(move_list):
    converted_move_list = []
    i = 0
    num_moves = 155
    for move in move_list:
        if i % 2 == 1:#black move
            offset = 1
        else:
            offset = 0
        converted_move_list.append(index_lookup_by_move(move)+ (num_moves*offset))#keep moves unique by adding 154 to black's version. else map onto the same relative position.
        i+=1
    if converted_move_list[-1] <num_moves:#final move was a white move
        converted_move_list.append(index_lookup_by_move('no-move') + (num_moves*1)) #black gameover
    else:
        converted_move_list.append(index_lookup_by_move('no-move'))#white gameover
    return converted_move_list

def preprocess_move_list(move_list):
    formatted_move_list = ['no-move']*40
    formatted_move_list.extend(move_list)
    return formatted_move_list

def split_data_to_training_examples_and_labels_for_CNN(array_to_split, NNType):
    training_examples = []
    labels = []
    for training_example in array_to_split:  # probability space for transitions
        formatted_example, formatted_label = split_training_examples_and_labels(training_example, NNType)
        training_examples.append(formatted_example)
        labels.append(formatted_label)  # transition number
    return training_examples, labels

def split_training_examples_and_labels(training_example, NNType):
    formatted_example = format_training_example(training_example[0])
    if NNType == 'Policy':
         formatted_label = label_for_policy(transition_vector=training_example[2])
    else: # Value Net
         formatted_label = label_for_value(win=training_example[1])
    return formatted_example, formatted_label

def format_training_example(training_example):
    formatted_example = []
    for plane in training_example:
        formatted_example += plane  # flatten 2d matrix
    formatted_example = np.reshape(np.array(formatted_example, dtype=np.float32),
                                   (len(formatted_example) // 64, 8, 8))  # feature_plane x row x co)
    for i in range(0, len(formatted_example)):
        formatted_example[i] = formatted_example[
            i].transpose()  # transpose (row x col) to get feature_plane x col x row
    formatted_example = formatted_example.transpose()  # transpose to get proper dimensions: row x col  x feature plane
    return formatted_example

# def get_hidden_layer_transform(formatted_examples):
#     sess, y_pred_white, X_white, y_pred_black, X_black = instantiate_session_both_RNN()
#     formatted_example = sess.run(y_pred_black, feed_dict={X_black: formatted_examples})
#     placeholder = np.append(np.zeros([40, 8, 8, 1], dtype=np.float32 ), formatted_example, axis=0)
#     # placeholder.extend(formatted_example)
#     formatted_example = placeholder
#
#     return formatted_example


def split_data_to_training_examples_and_labels_for_CNN_RNN(array_to_split, NNType, policy_net, color):
    training_examples = []
    labels = []
    for training_example in array_to_split:  # probability space for transitions
        formatted_example, formatted_label = split_training_examples_and_labels_CNN_RNN(training_example, NNType, policy_net, color)
        training_examples.extend(formatted_example)
        labels.extend(formatted_label)  # transition number
    return training_examples, labels

def split_training_examples_and_labels_CNN_RNN(training_example, NNType, policy_net, color):
    formatted_examples = []
    formatted_labels = []

    if NNType == 'Policy':
        i = 0
        for state in training_example:
            if color == 'White':
                if i %2 == 1:
                    #black's state, switch Player and Opponent Planes and convert to POV Rep for NN Eval
                    temp_player = state[0][1][:]#opponent (Black) copy
                    state[0][1] = state[0][0][-1::-1]#opponent (Black) becames reversed player
                    state[0][0] = temp_player[-1::-1]#player becomes reversed opponent (Black)
                    state[0][2] = state[0][2][-1::-1]#empty reversed
                    player_color = 'Black'

                else:
                    #white is default POV and already player, leave it alone
                    player_color = 'White'
            elif color == 'Black':
                if i % 2 == 1:  # black's state,
                    #already player, just need to flip for POV
                    state[0][0] = state[0][0][-1::-1]
                    state[0][1] = state[0][1][-1::-1]
                    state[0][2] = state[0][2][-1::-1]
                    player_color = 'Black'
                else:
                    #White is default POV, just switch player and opponent
                    temp_player = state[0][1][:]
                    state[0][1] = state[0][0][:]
                    state[0][0] = temp_player
                    player_color = 'White'
            formatted_examples.append(policy_net.evaluate([format_training_example(state[0])], player_color=player_color, already_converted=True)[0])
            formatted_labels.append(label_for_policy(transition_vector=state[2]))
            i +=1

    # formatted_examples = sess.run(output, feed_dict={input: formatted_examples})

    formatted_examples = np.append(np.zeros([40, 8, 8, 1], dtype=np.float32 ), formatted_examples, axis=0)

    window_size = 40
    training_examples = []
    for k in range(0, len(formatted_labels)):
        training_examples.append(formatted_examples[k:k + window_size])
    return np.array(training_examples, dtype=np.float32), np.array(formatted_labels, dtype=np.float32)

def label_for_policy(transition_vector, one_hot_indexes=False):
    # if one_hot_indexes:
    #     # x still a 1d array; must stay one-hotted to be reshaped properly
    #     formatted_example = np.array([index for index, has_piece in enumerate(formatted_example) if has_piece == 1], dtype=np.float32)
    #     # if we just want the transition index vs a pre-one-hotted vector
    #     formatted_label = label.index(1)  # assumes no errors, y has a single value of 1
    formatted_label = np.array(transition_vector, dtype=np.float32)  # One hot transition vector
    return formatted_label

def label_for_value(win):
    if win:
        formatted_label = 1
        complement = 0
    else:
        formatted_label = 0
        complement = 1
    return np.array([formatted_label, complement], dtype=np.float32)

    


def SplitArraytoXMatrixAndYTransitionVectorCNN(arrayToSplit):  # only for boards with pd dataframe
    warnings.warn("Only for use with PD Dataframe data; "
                  "Removed in favor of performing conversion later in the pipeline. "
                  "Else, earlier stages of pipeline will be computationally expensive, "
                  "memory intensive, and require large amounts of disk space "
                  , DeprecationWarning)
    X = []
    y = []
    for trainingExample in arrayToSplit:  # probability space for transitions
        x = []
        for plane in trainingExample[0]:
            x.append(plane.as_matrix()) #convert pd dataframe to np array
        board_dimensions = (8, 8)
        x.append(np.ones(board_dimensions, dtype=np.int32)) # 1 bias plane
        one_hot_transitions = None
        for transition in range(0, len(trainingExample[2])):
            if trainingExample[2][transition] == 1:
                one_hot_transitions = transition
                break
        if one_hot_transitions == None:  # no move
            # one_hot_transitions = -1  # tf.one_hot will return a vector of all 0s
            one_hot_transitions = 155  # DNNClassifier => 155 == no move category
        y.append(one_hot_transitions)  # transition vector
        X.append(np.array(x, dtype=np.int32))
    return X, y


def GenerateCSV(X, isX = True):
    if isX == True:
     np.savetxt(r'/Users/TeofiloZosa/PycharmProjects/BreakthroughANN/value_net_rank_binary/NPDataSets/WBPOEUnshuffledBinaryFeaturePlanesWBPOETrainingExamples.csv', X, delimiter=',', fmt='%1i')
    else:
        np.savetxt(
            r'/Users/TeofiloZosa/PycharmProjects/BreakthroughANN/value_net_rank_binary/NPDataSets/WBPOE/UnshuffledBinaryFeaturePlanesWBPOETrainingExampleOutcomes.csv',
            X, delimiter=',', fmt='%1i')
def SplitListInHalf(a_list):
    half = len(a_list)//2
    return a_list[:half], a_list[half:]
def PreprocessXLSX(X):
    XLSX_X = []
    X = filter_by_rank(X)
    for x in X:  # more efficient numpy version somewhere
        XLSX_X.append(x[0] + [x[1]])
    XLSX_X1, XLSX_X2 = SplitListInHalf(XLSX_X)
    XLSX_X1 = np.matrix(XLSX_X1, dtype=np.int8)
    XLSX_X2 = np.matrix(XLSX_X2, dtype=np.int8)
    #data too large, bug causes a fail to write unless we split the data
    GenerateXLSX(XLSX_X1, which=1)
    GenerateXLSX(XLSX_X2, which=2)
def GenerateXLSX(X, which=1):
    columns = []
    # generate column names
    for dimension in ['White', 'Black', 'Player', 'Opponent', 'Empty']:
        for i in range(1, 9):
            for char in 'abcdefgh':
                position = 'Position: ' + char + str(i) + ' (' + dimension + ')'
                columns.append(position)
    columns.append('White\'s Move Preceded This State')
    columns.append('Outcome')
    frame = pd.DataFrame(X, columns=columns)
    if which==1:
        writer = pd.ExcelWriter(r'/Users/TeofiloZosa/PycharmProjects/BreakthroughANN/value_net_rank_binary/NPDataSets/WBPOE/UnshuffledBinaryFeaturePlanesDataset1.xlsx', engine='xlsxwriter')
    else:
        writer = pd.ExcelWriter(r'/Users/TeofiloZosa/PycharmProjects/BreakthroughANN/value_net_rank_binary/NPDataSets/WBPOE/UnshuffledBinaryFeaturePlanesDataset2.xlsx', engine='xlsxwriter')

    frame.to_excel(writer, 'Sheet1')
    writer.save()
def assign_filter(fileName):
    if fileName == r'PlayerDataPythonDataSetsorted.p':
        filter = r'Rank'
    elif fileName == r'PlayerDataBinaryFeaturesWBPOEDataSetsorted.p':
        filter = r'Binary Rank'
    else:
        filter = r'UNDEFINED'
    return filter
def assign_path(deviceName ='Workstation'):
    if  deviceName == 'MBP2011_':
       path =  r'/Users/teofilozosa/PycharmProjects/BreakthroughANN/'
    elif deviceName == 'MBP2014':
       path = r'/Users/TeofiloZosa/PycharmProjects/BreakthroughANN/'
    elif deviceName == 'MBP2011':
       path = r'/Users/Home/PycharmProjects/BreakthroughANN/'
    elif deviceName == 'Workstation':
        path ='G:\TruncatedLogs\PythonDataSets\DataStructures'
    else:
        path = ''#todo:error checking
    return path

def self_player_driver(filter, NNType, path, fileName, game_stage='All', color='Both', policy_net=None):
    file = open(os.path.join(path, fileName), 'r+b')
    player_list = pickle.load(file)
    file.close()
    # for player in player_list:
    #     for game in player['Games']:
    #         if game['Win'] is True:
    #            print(game['OriginalVisualizationURL'])
    #            print(game['MirrorVisualizationURL'])
    # exit(-1)

    training_examples, labels = filter_training_examples_and_labels(player_list, filter, NNType, game_stage, color, policy_net)
    write_path = os.path.join(path,"NumpyArrays",'PolicyNet','POE','4DArraysHDF5(RxCxF)POE{NNType}Net{game_stage}Third{color}'.format(NNType=NNType, game_stage=game_stage, color=color), fileName[0:-len(r'DataPython.p')])
    write_np_array_to_disk(write_path, training_examples, labels, filter, NNType)
