from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
import random
import copy
from queue import Queue
import time

class body(BaseModel):
    game    : dict
    turn    : int
    board   : dict
    you     : dict

app = FastAPI()

mySnakeID = ""
boardWidth = 40
boardHeight = 40
excedeuTempo = False

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
    print("Excedeu tempo: ", excedeuTempo)
    return "ok"
    

@app.post("/move")
def move_func(request : body) :

    startTime = time.time()
    possibleTiles, possibleTilesPrediction = predictPossibleSnakes(request.you, request.board)
    print("pTiles", possibleTiles)
    print("pTilesPred", possibleTilesPrediction)
    move, deuRuim = randomMove(possibleTilesPrediction)
    if deuRuim == True:
        move, deuRuim = randomMove(possibleTiles)

    print("Move: ", move)
    print("deuRuim: ",deuRuim)

    if time.time() - startTime > 0.1 :
        global excedeuTempo
        excedeuTempo = True
    print("time elapsed: ",)
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

def avoidAllSnakes(me : dict, board : dict) :
    possibleTiles = avoidEdges(me)
    possibleTilesCpy = copy.deepcopy(possibleTiles)
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

def predictClosedAreas(me: dict, board : dict):
    nextTiles = avoidAllSnakes(me, board)
    resultingTiles = {}
    fillSize = (boardWidth*boardHeight - howManySnakeTiles(board["snakes"]))/4 # número arbitrário de uma area grande o suficiente CALCULAR A PARTIR DA AREA DO MAPA - AREA OCUPADA
    for move in nextTiles:              # Adicionar logica para, em ultimo caso, ignorar o predictClosedAreas
        queue = Queue()
        queue.put(nextTiles[move])
        filledPositions = []
        while not queue.empty():
            pos = queue.get()
            if pos["x"] < 0 or pos["y"] < 0 or pos["x"] >= boardWidth or pos["y"] >= boardHeight or \
             isPosSnake(pos, board["snakes"]) or pos in filledPositions:
                continue
            else:
                filledPositions.append(pos)
                if(len(filledPositions) >= fillSize): 
                    print("filled: ", filledPositions)
                    resultingTiles[move] = nextTiles[move]
                    break
                adjTiles = getAdjacentTiles(pos)
                queue.put(adjTiles["up"])
                queue.put(adjTiles["down"])
                queue.put(adjTiles["left"])
                queue.put(adjTiles["right"])
    print("afterArea: ",resultingTiles)
    return resultingTiles

def predictPossibleSnakes(me : dict, board : dict):
    possibleTiles = predictClosedAreas(me,board)
    if len(possibleTiles) == 0:
        possibleTiles = avoidAllSnakes(me, board)
    possibleTilesCpy = copy.deepcopy(possibleTiles)
    killingMoves = []

    for move in possibleTilesCpy:
        if move in possibleTiles.keys():
            for snake in board["snakes"]:
                if snake["id"] != mySnakeID:
                    snakeAdjacentTiles = getAdjacentTiles(snake["head"])
                    for direction in ["up","down","left","right"]:
                        if move in possibleTiles.keys():
                            if snakeAdjacentTiles[direction] == possibleTiles[move]:
                                if isMySizeBigger(me,snake):
                                    if move not in killingMoves:
                                        killingMoves.append(move)
                                else:
                                    del possibleTiles[move]
    return possibleTilesCpy, possibleTiles # RETORNAR KILLING MOVES TB E USAR NA DECISAO FINAL


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
    if(me["length"] > snake["length"]):
        return True
    else:
        return False

def hasSnakeEaten(snake : dict):
    if(snake["health"] == 100):
        return True
# Se a vida estiver em 100, o rabo não vai andar

def randomMove(possibleTiles : dict) :
    if len(list(possibleTiles.keys())) <= 0:
        return "down", True
    move = random.choice(list(possibleTiles.keys()))
    return move, False


handler = Mangum(app, lifespan="off")
