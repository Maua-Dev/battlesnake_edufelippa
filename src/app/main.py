from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
from random import choice
from copy import deepcopy
from queue import Queue

class body(BaseModel):
    game    : dict
    turn    : int
    board   : dict
    you     : dict

app = FastAPI()

mySnakeID = ""
boardWidth = 40
boardHeight = 40

@app.get("/")
def read_root():
    return {
        "apiversion": "1",
        "author": "eduSnake",
        "color": "#00ffff",
        "head": "replit-mark",
        "tail": "mouse",
    }


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/create_item")
def create_item(request: dict):
    item_id = request.get("item_id")
    name = request.get("name")
    print(request)

    return {"item_id": item_id,
            "name": name}

@app.post("/start")
def start_func(request: body) :
    #gameID = request.game["id"]
    global mySnakeID
    mySnakeID = request.you["id"]
    #print("Game ID: ", gameID)
    print("mySnakeID: ", mySnakeID)
    global boardWidth
    boardWidth = request.board["width"]
    global boardHeight
    boardHeight = request.board["height"]

    return "ok"

@app.post("/end")
def end_func() :
    return "ok"
    

@app.post("/move")
def move_func(request : body) :

    me = request.you
    board = request.board


    possibleTiles = avoidEdges(me)
    if len(possibleTiles) > 1:
        possibleTiles = avoidAllSnakes(me, board, possibleTiles)
    if len(possibleTiles) > 1:
        possibleTiles, smallAreaSizes = predictClosedAreas(me, board, possibleTiles)
    if len(possibleTiles) > 1:
        possibleTiles, killerMoves = predictPossibleSnakes(me, board, possibleTiles)

    possibleTiles = chooseBiggestArea(me, board, possibleTiles, smallAreaSizes) # Sempre retorna ao menos 1 move
    possibleTiles = bestMoveForKillAndFood(me, board, possibleTiles, killerMoves) # Sempre retorna ao menos 1 move

    move = randomMove(possibleTiles)

    print("Move: ", move)

    return {"move" : move}

def getAdjacentTiles(pos : dict):
    xPos = pos["x"]
    yPos = pos["y"]
    adjacentTiles = {"up" : {"x":xPos, "y":yPos+1},
                     "down" : {"x":xPos, "y":yPos-1},
                     "left" : {"x":xPos-1, "y":yPos},
                     "right" : {"x":xPos+1, "y":yPos}}
    return adjacentTiles

def getMyNextTiles(me : dict) :
    myHead = me["head"]
    nextTiles = getAdjacentTiles(myHead)
    return nextTiles

""" def avoidBackwards(me : dict) : # JA VERIFICADO PELO AVOID ALL SNAKES
    possibleTiles = getNextTiles(me)
    myBack = me["body"][1]
    for k in ["up","down","left","right"]:
        if possibleTiles[k] == myBack:
            del possibleTiles[k]
            return possibleTiles
    return possibleTiles """

def avoidEdges(me : dict) :
    possibleTiles = getMyNextTiles(me)
    lastX = boardWidth - 1
    lastY = boardHeight - 1
    if me["head"]["x"] == 0:
        del possibleTiles["left"]
    elif me["head"]["x"] == lastX:
        del possibleTiles["right"]

    if me["head"]["y"] == 0:
        del possibleTiles["down"]
    elif me["head"]["y"] == lastY:
        del possibleTiles["up"]

    return possibleTiles

def avoidAllSnakes(me : dict, board : dict, possibleTiles : dict) :
    possibleTilesCpy = deepcopy(possibleTiles)
    for move in possibleTilesCpy:
        if move in possibleTiles.keys():
            for snake in board["snakes"]:
                index = 0
                snakeLen = snake["length"]
                for bodyPartPos in snake["body"]:
                    if index == snakeLen - 1:
                        if not hasSnakeEaten(snake):
                            index += 1
                            continue
                    if move in possibleTiles.keys():
                        if bodyPartPos == possibleTiles[move]:
                            del possibleTiles[move]
                    index += 1
    return possibleTiles

def predictClosedAreas(me: dict, board : dict, previousNextTiles : dict):
    resultingTiles = {}
    smallAreaSizes = {}
    nSnakes = len(board["snakes"])
    if nSnakes == 1:
        nSnakes = 2
    fillSize = (boardWidth*boardHeight - howManySnakeTiles(board["snakes"]))/nSnakes # Area desocupada / numero de cobras
    for move in previousNextTiles:
        queue = Queue()
        queue.put(previousNextTiles[move])
        filledPositions = []
        foundBigArea = False
        while not queue.empty():
            pos = queue.get()
            if pos["x"] < 0 or pos["y"] < 0 or pos["x"] >= boardWidth or pos["y"] >= boardHeight or \
             isPosSnake(pos, board["snakes"]) or pos in filledPositions:
                continue
            else:
                filledPositions.append(pos)
                if len(filledPositions) >= fillSize:
                    foundBigArea = True
                    resultingTiles[move] = previousNextTiles[move]
                    break
                adjTiles = getAdjacentTiles(pos)
                queue.put(adjTiles["up"])
                queue.put(adjTiles["down"])
                queue.put(adjTiles["left"])
                queue.put(adjTiles["right"])
        if not foundBigArea:
            smallAreaSizes[move] = len(filledPositions)

    if not resultingTiles:
        return previousNextTiles, smallAreaSizes
    return resultingTiles, smallAreaSizes

def predictPossibleSnakes(me : dict, board : dict, possibleTiles : dict):
    possibleTilesCpy = deepcopy(possibleTiles)
    killerMoves = []

    for move in possibleTilesCpy:
        if move in possibleTiles.keys():
            for snake in board["snakes"]:
                if snake["id"] != mySnakeID:
                    snakeAdjacentTiles = getAdjacentTiles(snake["head"])
                    for direction in ["up","down","left","right"]:
                        if move in possibleTiles.keys():
                            if snakeAdjacentTiles[direction] == possibleTiles[move]:
                                if isMySizeBigger(me,snake):
                                    if move not in killerMoves:
                                        killerMoves.append(move)
                                else:
                                    del possibleTiles[move]
    if len(possibleTiles) > 0:
        return possibleTiles, killerMoves
    else:
        return possibleTilesCpy, killerMoves

def chooseBiggestArea(me, board, possibleTiles, smallAreaSizes): # Apenas se so sobraram areas pequenas

    if not smallAreaSizes:
        return possibleTiles

    maxAreaSize = -1
    biggestAreaMove = ""

    for move in possibleTiles:
        if move not in smallAreaSizes.keys():
            return possibleTiles
        if smallAreaSizes[move] > maxAreaSize:
            maxAreaSize = smallAreaSizes[move]
            biggestAreaMove = move
    return {biggestAreaMove : possibleTiles[biggestAreaMove]}

def bestMoveForKillAndFood(me, board, possibleTiles, killerMoves):
    remainingMoves = len(possibleTiles)
    
    killerMovesDict = {}
    areThereKillerMoves = False
    for move in possibleTiles:
        if move in killerMoves:
            areThereKillerMoves = True
            killerMovesDict[move] = possibleTiles[move]

    if areThereKillerMoves:
        return killerMovesDict

    if remainingMoves < 2:
        return possibleTiles

    myHead = me["head"]
    closestFood = findClosestPointFromMyPos(myHead, board["food"])
    badMoves = []
    if closestFood["x"] > myHead["x"]:
        badMoves.append("left")
    elif closestFood["x"] != myHead["x"]:
        badMoves.append("right")
    if closestFood["y"] > myHead["y"]:
        badMoves.append("down")
    elif closestFood["y"] != myHead["y"]:
        badMoves.append("up")


    for move in badMoves:
        if move in possibleTiles:
            del possibleTiles[move]
            remainingMoves -= 1
            if remainingMoves < 2:
                return possibleTiles

    return possibleTiles

def findClosestPointFromMyPos(myPos : dict, points : dict):
    minDist = -1
    closestPos = {}
    for pos in points:
        dist = abs(pos["x"] - myPos["x"]) + abs(pos["y"] - myPos["y"])
        if dist < minDist or minDist == -1 :
            minDist = dist
            closestPos = pos
    return closestPos

def howManySnakeTiles(snakes : dict):
    sum = 0
    for snake in snakes:
        sum += snake["length"]
    return sum

def isPosSnake(pos : dict, snakes : dict):
    for snake in snakes:
        index = 0
        snakeLen = snake["length"]
        for bodyPartPos in snake["body"]:
            if index == snakeLen - 1:
                if not hasSnakeEaten(snake):
                    index += 1
                    continue
                if bodyPartPos == pos:
                    return True
            if bodyPartPos == pos:
                return True
            index += 1
    return False

def isMySizeBigger(me : dict, snake : dict):
    if me["length"] > snake["length"]:
        return True
    else:
        return False

def hasSnakeEaten(snake : dict):
    if snake["health"] == 100:
        return True
# Se a vida estiver em 100, o rabo não vai andar

def randomMove(possibleTiles : dict) :
    if len(list(possibleTiles.keys())) <= 0:
        return "down" # Nunca devera ser chamado
    move = choice(list(possibleTiles.keys()))
    return move


handler = Mangum(app, lifespan="off")
