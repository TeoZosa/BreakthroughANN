import re as re  # regular expressions
import os, fnmatch  # to retrieve file information from path
import pickle  # serialize the data structure
import mmap #read entire files into memory for (only for workstation)
import copy
import math
from psutil import virtual_memory

def ProcessDirectoryOfBreakthroughFiles(path, playerList):
    for selfPlayGames in FindFiles(path, '*.txt'):
        playerList.append(ProcessBreakthroughFile(path, selfPlayGames))

def ProcessBreakthroughFile(path, selfPlayGames):
    fileName = selfPlayGames[
               len(path):len(selfPlayGames) - len('.txt')]  # trim path & extension
    fileName = fileName.split('_SelfPlayLog')  # BreakthroughN_SelfPlayLog00-> ['BreakthroughN',00]
    serverName = str(fileName[0].strip('\\'))
    selfPlayLog = str(fileName[1]).strip('(').strip(')')
    dateRange = str(selfPlayGames[
                    len(r'G:\TruncatedLogs') + 1:len(path) - len(r'\selfPlayLogsBreakthroughN')])
    gamesList, whiteWins, blackWins = FormatGameList(selfPlayGames, serverName)
    return {'ServerNode': serverName, 'selfPlayLog': selfPlayLog, 'dateRange': dateRange, 'Games': gamesList, 'WhiteWins': whiteWins, 'BlackWins': blackWins}

def WriteToDisk(input, path):
    date = str(path [
                    len(r'G:\TruncatedLogs') + 1:len(path) - len(r'\selfPlayLogsBreakthroughN')])
    outputFile = open(path + r'DataPython.p', 'wb')
    pickle.dump(input, outputFile)

def FindFiles(path, filter):  # recursively find files at path with filter extension; pulled from StackOverflow
    for root, dirs, files in os.walk(path):
        for file in fnmatch.filter(files, filter):
            yield os.path.join(root, file)

def FormatGameList(selfPlayGames, serverName):
    games = []
    blackWin = None
    whiteWin = None
    endRegex = re.compile(r'.* End')
    startRegex = re.compile(r'.* Start')
    moveRegex = re.compile(r'\*play (.*)')
    blackWinRegex = re.compile(r'Black Wins:.*')
    whiteWinRegex = re.compile(r'White Wins:.*')
    numWhiteWins = 0
    numBlackWins = 0
    file = open(selfPlayGames, "r+b")# read in file
    file = mmap.mmap(file.fileno(),length=0, access= mmap.ACCESS_READ)#prot=PROT_READ only in Unix
    #iterate over list of the form:
    #Game N Start
    #...
    #(Black|White) Wins: \d
    #[Game N End]
    moveList = []
    while True:
        line = file.readline().decode('utf-8')#convert to string
        if line=='':break#EOF
        if moveRegex.match(line):#put plays into move list
            moveList.append(moveRegex.search(line).group(1))
        elif blackWinRegex.match(line):
            blackWin = True
            whiteWin = False
        elif whiteWinRegex.match(line):
            whiteWin = True
            blackWin = False
        elif endRegex.match(line):
            #Format move list
            moveList, webVisualizerLink = FormatMoveList(moveList)
            whiteBoardStates = GenerateBoardStatesPolicyNet(moveList, "White", whiteWin)  # generate board states from moveList
            blackBoardStates = GenerateBoardStatesPolicyNet(moveList, "Black", blackWin)#self-play => same states, but win under policy for A=> lose under policy for B
            if whiteWin:
                numWhiteWins += 1
            elif blackWin:
                numBlackWins += 1
            games.append({'Win': whiteWin,
                          'Moves': moveList,
                          'BoardStates': whiteBoardStates,
                          'VisualizationURL': webVisualizerLink})  # append new white game
            games.append({'Win': blackWin,
                          'Moves': moveList,
                          'BoardStates': blackBoardStates,
                          'VisualizationURL': webVisualizerLink})  # append new black game
            moveList = []#reset moveList for next game
            whiteWin = None #not necessary;redundant, but good practice
            blackWin = None
    file.close()
    return games, numWhiteWins, numBlackWins

def GenerateBoardStates(moveList, playerColor, win):
    empty = 'e'
    white = 'w'
    black = 'b'
    if playerColor == 'White':
        isWhite = 1
    else:
        isWhite = 0
        # win/loss 'value' symmetrical
    if win == True:
        win = 1
    elif win == False:
        win = -1
    state = [
        {
        10: -1,  #did White's move achieve this state (-1 for a for initial state, 0 for if black achieved this state)
         9: isWhite,  #is playerColor white
         8: {'a': black, 'b': black, 'c': black, 'd': black, 'e': black, 'f': black, 'g': black, 'h': black},
         7: {'a': black, 'b': black, 'c': black, 'd': black, 'e': black, 'f': black, 'g': black, 'h': black},
         6: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
         5: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
         4: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
         3: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
         2: {'a': white, 'b': white, 'c': white, 'd': white, 'e': white, 'f': white, 'g': white, 'h': white},
         1: {'a': white, 'b': white, 'c': white, 'd': white, 'e': white, 'f': white, 'g': white, 'h': white}
         }, win]
    mirrorState = MirrorBoardState(state)

    #Original start state should not be useful for tree search since it is the root of every game and has no parent.
    #however, may provide useful bias if starting player matters (self-play shows 56% win rate for white, p << 0.001 => first-move advantage)
    boardStates = {'Win': win, 'States': [state], 'MirrorStates': [mirrorState]}# including original start state

    for i in range(0, len(moveList)):
        assert (moveList[i]['#'] == i + 1)
        if isinstance(moveList[i]['White'], dict):  # if string, then == resign or NIL
            state = [MovePiece(state[0], moveList[i]['White']['To'], moveList[i]['White']['From'], whoseMove='White'), win]
            boardStates['States'].append(state)
            mirrorState = MirrorBoardState(state)
            boardStates['MirrorStates'].append(mirrorState)
        if isinstance(moveList[i]['Black'], dict):  # if string, then == resign or NIL
            state= [MovePiece(state[0], moveList[i]['Black']['To'], moveList[i]['Black']['From'], whoseMove='Black'), win]
            boardStates['States'].append(state)
            mirrorState = MirrorBoardState(state)
            boardStates['MirrorStates'].append(mirrorState)
    #for data transformation; inefficient to essentially compute board states twice, but more error-proof
    boardStates = ConvertBoardStatesToArrays(boardStates, playerColor)
    return boardStates

def InitialState(moveList, playerColor, win):
    empty = 'e'
    white = 'w'
    black = 'b'
    if playerColor == 'White':
        isWhite = 1
    else:
        isWhite = 0
    return [
        {
            10: -1,  # did White's move achieve this state (-1 for a for initial state, 0 for if black achieved this state)
            9: isWhite,  # is playerColor white
            8: {'a': black, 'b': black, 'c': black, 'd': black, 'e': black, 'f': black, 'g': black, 'h': black},
            7: {'a': black, 'b': black, 'c': black, 'd': black, 'e': black, 'f': black, 'g': black, 'h': black},
            6: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
            5: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
            4: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
            3: {'a': empty, 'b': empty, 'c': empty, 'd': empty, 'e': empty, 'f': empty, 'g': empty, 'h': empty},
            2: {'a': white, 'b': white, 'c': white, 'd': white, 'e': white, 'f': white, 'g': white, 'h': white},
            1: {'a': white, 'b': white, 'c': white, 'd': white, 'e': white, 'f': white, 'g': white, 'h': white}
        },
        win,
        generateTransitionVector(moveList[0]['White']['To'], moveList[0]['White']['From'], 'White')]#White's opening move

def GenerateBoardStatesPolicyNet(moveList, playerColor, win):
    # probability distribution over the 154 possible (not legal) moves from the POV of the player.
    # Reasoning: six center columns where, if a piece was present, it could move one of three ways.
    # A piece in one of the two side columns can move one of two ways.
    # Since nothing can move in the farthest row, there are only seven rows of possible movement.
    # => (2*2*7) + (6*3*7) = 154
    # ==> instead of a win value, we would have a 154 vector of all 0s sans the 1 for the transition that was actually made.
    # i.e. a1-a2 (if White) && h8-h7 (if Black) =>
    # row 0 (closest row), column 0(farthest left)
    # moves to
    # row +1, column 0
    # <=> transition[0] = 1, transition[0:len(transition)] = 0

    # Notes: if black, reverse move array. i.e. a=h, 8=1 YES. when calling NN, just reverse board state if black and decode output with black's table
    # OR decode transitions differently(i.e. h8-h7 (if Black) = a1-a2 (if White))..
    mirrorMoveList = MirrorMoveList(moveList)
    state = InitialState(moveList,playerColor,win)
    mirrorState = InitialState(mirrorMoveList,playerColor,win)
    boardStates = {'Win': win, 'States': [state], 'MirrorStates': [mirrorState]}

    for i in range(0, len(moveList)):
        assert (moveList[i]['#'] == i + 1)
        if isinstance(moveList[i]['White'], dict):  # if string, then == resign or NIL
            if isinstance(moveList[i]['Black'], dict):  # if string, then == resign or NIL
                blackTransitionVector = generateTransitionVector(moveList[i]['Black']['To'], moveList[i]['Black']['From'], 'Black')
                blackMirrorTransitionVector = generateTransitionVector(mirrorMoveList[i]['Black']['To'], mirrorMoveList[i]['Black']['From'], 'Black')
                #can't put black move block in here as it would execute before white's move
            else:
                blackTransitionVector = [0]*154
                blackMirrorTransitionVector = [0]*154
            state = [MovePiece(state[0], moveList[i]['White']['To'], moveList[i]['White']['From'], whoseMove='White'),
                     win,
                     blackTransitionVector] #Black's response to the generated state
            boardStates['States'].append(state)
            mirrorState = [MovePiece(mirrorState[0], mirrorMoveList[i]['White']['To'], mirrorMoveList[i]['White']['From'], whoseMove='White'),
                     win,
                     blackMirrorTransitionVector]
            boardStates['MirrorStates'].append(mirrorState)
        if isinstance(moveList[i]['Black'], dict):  # if string, then == resign or NIL
            if i+1 == len(moveList):# if no moves left => black won
                whiteTransitionVector = [0]*154 # no white move from the next generated state
                whiteMirrorTransitionVector = [0]*154
            else:
                whiteTransitionVector = generateTransitionVector(moveList[i+1]['White']['To'], moveList[i+1]['White']['From'], 'White')
                whiteMirrorTransitionVector = generateTransitionVector(mirrorMoveList[i+1]['White']['To'], mirrorMoveList[i+1]['White']['From'], 'White')
            state = [MovePiece(state[0], moveList[i]['Black']['To'], moveList[i]['Black']['From'], whoseMove='Black'),
                     win,
                     whiteTransitionVector]  # White's response to the generated state
            boardStates['States'].append(state)
            mirrorState = [MovePiece(mirrorState[0], mirrorMoveList[i]['Black']['To'], mirrorMoveList[i]['Black']['From'], whoseMove='Black'),
                     win,
                     whiteMirrorTransitionVector]  # White's response to the generated state
            boardStates['MirrorStates'].append(mirrorState)
    # for data transformation; inefficient to essentially compute board states twice, but more error-proof
    boardStates = ConvertBoardStatesToArrays(boardStates, playerColor)
    return boardStates

def generateTransitionVector(to, From, playerColor):
    fromColumn = From[0]
    toColumn = to[0]
    fromRow = int(From[1])
    toRow = int(to[1])
    ordA = ord('a')
    ordFrom = ord(fromColumn)
    columnOffset = (ord(fromColumn) - ord('a')) * 3 #ex if white, moves starting from b are [2] or [3] or [4]
    if playerColor == 'Black':
        rowOffset = (toRow - 1) * 22
        assert (rowOffset == (fromRow - 2) * 22)  # double check
        index = 153 - (ord(toColumn) - ord(fromColumn) + columnOffset + rowOffset)#153 reverses the board for black
    else:
        rowOffset = (fromRow - 1) * 22
        assert (rowOffset == (toRow - 2) * 22)  # double check
        index = ord(toColumn) - ord(fromColumn) + columnOffset + rowOffset
    transitionVector = [0] * 154
    transitionVector[index] = 1
    return transitionVector

def MirrorMoveList(moveList):
    mirrorMoveList = []
    for move in moveList:
        mirrorMoveList.append(MirrorMove(move))
    return mirrorMoveList

def MirrorMove(move):
    mirrorMove = copy.deepcopy(move)
    whiteTo = move['White']['To']
    whiteFrom = move['White']['From']
    whiteFromColumn = whiteFrom[0]
    whiteToColumn = whiteTo[0]
    whiteFromRow = int(whiteFrom[1])
    whiteToRow = int(whiteTo[1])
    mirrorMove['White']['To'] = MirrorColumn(whiteToColumn) + str(whiteToRow)
    mirrorMove['White']['From'] = MirrorColumn(whiteFromColumn) + str(whiteFromRow)

    if isinstance(move['Black'], dict):
        blackTo = move['Black']['To']
        blackFrom = move['Black']['From']
        blackFromColumn = blackFrom[0]
        blackToColumn = blackTo[0]
        blackFromRow = int(blackFrom[1])
        blackToRow = int(blackTo[1])
        mirrorMove['Black']['To'] = MirrorColumn(blackToColumn) + str(blackToRow)
        mirrorMove['Black']['From'] = MirrorColumn(blackFromColumn) + str(blackFromRow)

    return mirrorMove


def MirrorColumn(columnChar):
    mirrorDict ={'a': 'h',
                 'b': 'g',
                 'c': 'f',
                 'd': 'e',
                 'e': 'd',
                 'f': 'c',
                 'g': 'b',
                 'h': 'a'
                 }
    return mirrorDict[columnChar]

def MirrorBoardState(state):#since a mirror image has the same strategic value
    mirrorStateWithWin = copy.deepcopy(state)  # edit copy of boardState
    mirrorState = mirrorStateWithWin[0]
    state = state[0] #the board state; state[1] is the win or loss value, state [2] is the transition vector
    isWhiteIndex = 9
    whiteMoveIndex = 10
    for row in sorted(state):
        if row != isWhiteIndex and row != whiteMoveIndex:  #these indexes don't change
            for column in sorted(state[row]):
                if column == 'a':
                    mirrorState[row]['h'] = state[row][column]
                elif column == 'b':
                    mirrorState[row]['g'] = state[row][column]
                elif column == 'c':
                    mirrorState[row]['f'] = state[row][column]
                elif column == 'd':
                    mirrorState[row]['e'] = state[row][column]
                elif column == 'e':
                    mirrorState[row]['d'] = state[row][column]
                elif column == 'f':
                    mirrorState[row]['c'] = state[row][column]
                elif column == 'g':
                    mirrorState[row]['b'] = state[row][column]
                elif column == 'h':
                    mirrorState[row]['a'] = state[row][column]
    return mirrorStateWithWin

def ConvertBoardStatesToArrays(boardStates, playerColor):
    newBoardStates = boardStates
    states = boardStates['States']
    mirrorStates = boardStates['MirrorStates']
    assert len(states) == len(mirrorStates)#vacuous assertion
    newBoardStates['States'] = []
    newBoardStates['MirrorStates'] = []
    for i in range (0, len (states)):
        newBoardStates['States'].append(ConvertBoardTo1DArray(states[i], playerColor))
        newBoardStates['MirrorStates'].append(ConvertBoardTo1DArray(mirrorStates[i], playerColor))
    return newBoardStates

def ConvertBoardTo1DArray(boardState, playerColor):
    state = boardState[0]
    isWhiteIndex = 9
    whiteMoveIndex = 10
    oneDArray = []
    #if player color == white, player and white states are mirrors; else, player and black states are mirrors
    GenerateBinaryPlane(state, arrayToAppend=oneDArray, playerColor=playerColor, whoToFilter='White')#0-63 white
    GenerateBinaryPlane(state, arrayToAppend=oneDArray, playerColor=playerColor, whoToFilter='Black')#64-127 black
    GenerateBinaryPlane(state, arrayToAppend=oneDArray, playerColor=playerColor, whoToFilter='Player')# 128-191 black
    GenerateBinaryPlane(state, arrayToAppend=oneDArray, playerColor=playerColor, whoToFilter='Opponent')# 192-255 black
    GenerateBinaryPlane(state, arrayToAppend=oneDArray, playerColor=playerColor, whoToFilter='Empty')#256-319 empty
    moveFlag = [state[whiteMoveIndex]]*64 #duplicate across 64 features since CNN needs same dimensions
    oneDArray+= moveFlag #320-383 is a flag indicating if the transition came from a white move
    for i in range (0, 64):  #error checking block
        assert (oneDArray[i]^oneDArray[i+64]^oneDArray[i+256])#ensure at most 1 bit is on at each board position for white/black/empty
        assert (oneDArray[i+128] ^ oneDArray[i + 192] ^ oneDArray[i + 256])  # ensure at most 1 bit is on at each board position for player/opponent/empty
        if playerColor == 'White':
            #player == white positions and opponent = black positions;
            assert (oneDArray[i] == oneDArray[i+128] and oneDArray[i+64] == oneDArray[i+192])
        else:
            #player == black positions and opponent = white positions;
            assert (oneDArray[i] == oneDArray[i+192] and oneDArray[i+64] == oneDArray[i+128])
    newBoardState = [oneDArray, boardState[1]]  # [x vector, y scalar]
    return newBoardState

def GenerateBinaryPlane(state, arrayToAppend, playerColor, whoToFilter):
    isWhiteIndex = 9
    whiteMoveIndex = 10
    if whoToFilter == 'White':
        for row in sorted(state):
            if row != isWhiteIndex and row != whiteMoveIndex:  # don't touch the index that shows whose move generated this state
                for column in sorted(state[row]):
                    # needs to be sorted to traverse dictionary in lexicographical order
                    value = -5
                    if state[row][column] == 'e':
                        value = 0
                    elif state[row][column] == 'w':
                        value = 1
                    elif state[row][column] == 'b':
                        value = 0
                    else:
                        print("error in convertBoard")
                        exit(-190)
                    arrayToAppend.append(value)
    elif whoToFilter == 'Black':
        for row in sorted(state):
            if row != isWhiteIndex and row!= whiteMoveIndex:  # don't touch the index that shows whose move generated this state
                for column in sorted(state[row]):
                    # needs to be sorted to traverse dictionary in lexicographical order
                    value = -5
                    if state[row][column] == 'e':
                        value = 0
                    elif state[row][column] == 'w':
                        value = 0
                    elif state[row][column] == 'b':
                        value = 1
                    else:
                        print("error in convertBoard")
                        exit(-190)
                    arrayToAppend.append(value)
    elif whoToFilter == 'Player':
        for row in sorted(state):
            if row != isWhiteIndex and row != whiteMoveIndex:  # don't touch the index that shows whose move generated this state
                for column in sorted(state[row]): # needs to be sorted to traverse dictionary in lexicographical order
                    value = -5
                    if state[row][column] == 'e':
                        value = 0
                    elif state[row][column] == 'w':
                        if playerColor == 'White':
                            value = 1
                        else:
                            value = 0
                    elif state[row][column] == 'b':
                        if playerColor == 'Black':
                            value = 1
                        else:
                            value = 0
                    else:
                        print("error in convertBoard")
                        exit(-190)
                    arrayToAppend.append(value)
    elif whoToFilter == 'Opponent':
        for row in sorted(state):
            if row != isWhiteIndex and row != whiteMoveIndex:  # don't touch the index that shows whose move generated this state
                for column in sorted(state[row]):
                    # needs to be sorted to traverse dictionary in lexicographical order
                    value = -5
                    if state[row][column] == 'e':
                        value = 0
                    elif state[row][column] == 'w':
                        if playerColor == 'White':
                            value = 0
                        else:
                            value = 1
                    elif state[row][column] == 'b':
                        if playerColor == 'Black':
                            value = 0
                        else:
                            value = 1
                    else:
                        print("error in convertBoard")
                        exit(-190)
                    arrayToAppend.append(value)
    elif whoToFilter == 'Empty':
        for row in sorted(state):
            if row != isWhiteIndex and row != whiteMoveIndex:  # don't touch the index that shows whose move generated this state
                for column in sorted(state[row]):
                    # needs to be sorted to traverse dictionary in lexicographical order
                    value = -5
                    if state[row][column] == 'e':
                        value = 1
                    elif state[row][column] == 'w' or state[row][column] == 'b':
                        value = 0
                    else:
                        print("error in convertBoard")
                        exit(-190)
                    arrayToAppend.append(value)
    else:
        print("Error, GenerateBinaryPlane needs a valid argument to filter")

def MovePiece(boardState, To, From, whoseMove):
    empty = 'e'
    whiteMoveIndex = 10
    nextBoardState = copy.deepcopy(boardState)  # edit copy of boardState
    nextBoardState[int(To[1])][To[0]] = nextBoardState[int(From[1])][From[0]]
    nextBoardState[int(From[1])][From[0]] = empty
    if whoseMove == 'White':
        nextBoardState[whiteMoveIndex] = 1
    else:
        nextBoardState[whiteMoveIndex] = 0
    return nextBoardState

def FormatMoveList(moveListString):
    moveRegex = re.compile(r"[W|B]\s([a-h]\d.[a-h]\d)",
                           re.IGNORECASE)
    webVisualizerLink = r'http://www.trmph.com/breakthrough/board#8,'
    moveList = list(map(lambda a: moveRegex.search(a).group(1), moveListString))
    moveNum = 0
    newMoveList=[]
    move = [None] * 3
    for i in range(0, len(moveList)):
        moveNum += 1
        move[0] = math.ceil(moveNum/2)
        From = str(moveList[i][0:2]).lower()
        to = str(moveList[i][3:5]).lower()
        if i % 2 == 0:#white move
            assert(moveList[i][1] < moveList[i][4])#white should go forward
            move[1] = {'From': From, 'To': to}  # set White's moves
            webVisualizerLink = webVisualizerLink + From + to
            if i==len(moveList)-1:#white makes last move of game; black lost
                move[2] = "NIL"
                newMoveList.append({'#': move[0], 'White': move[1], 'Black': move[2]})
        else:#black move
            assert (moveList[i][1] > moveList[i][4])#black should go backward
            move[2] = {'From': From, 'To': to}# set Black's moves
            webVisualizerLink = webVisualizerLink + From + to
            newMoveList.append({'#': move[0], 'White': move[1], 'Black': move[2]})
    return newMoveList, webVisualizerLink

def Driver(path):
    playerList = []
    ProcessDirectoryOfBreakthroughFiles(path, playerList)
    #WriteToDisk(playerList, path)
