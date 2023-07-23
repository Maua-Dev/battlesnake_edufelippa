from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
import random
import copy

class body(BaseModel):
    game    : dict
    turn    : int
    board   : dict
    you     : dict

app = FastAPI()

myLastMove = ""
mySnakeID = ""

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
    return "ok"

@app.post("/end")
def end_func() :
    return "ok"
    

@app.post("/move")
def move_func(request : body) :

    possibleTiles, possibleTilesPrediction = predictPossibleSnakes(request.you, request.board)
    move, deuRuim = randomMove(possibleTilesPrediction)
    if deuRuim == True:
        move, deuRuim = randomMove(possibleTiles)

    global myLastMove
    myLastMove = move
    print("Move: ", move)
    print("deuRuim: ",deuRuim)

    return {"move" : move,
            "shout": "F"}
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

def avoidEdges(me : dict, board : dict) :
    possibleTiles = getMyNextTiles(me)
    lastX = board["width"] - 1
    lastY = board["height"] - 1
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
    possibleTiles = avoidEdges(me,board)
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
    print("possible:", possibleTiles)
    return possibleTiles

def predictPossibleSnakes(me : dict, board : dict):
    possibleTiles = avoidAllSnakes(me,board)
    possibleTilesCpy = copy.deepcopy(possibleTiles)
    for move in possibleTilesCpy:
        if move in possibleTiles.keys():
            for snake in board["snakes"]:
                if snake["id"] != mySnakeID:
                    snakeAdjacentTiles = getAdjacentTiles(snake["head"])
                    for direction in ["up","down","left","right"]:
                        if snakeAdjacentTiles[direction] == possibleTiles[move]:
                            del possibleTiles[move]
    return possibleTilesCpy, possibleTiles

def checkLastMove(snake : dict):
    if snake["head"]["x"] > snake["body"][1]["x"]:
        return "right"
    elif snake["head"]["x"] < snake["body"][1]["x"]:
        return "left"
    elif snake["head"]["y"] > snake["body"][1]["y"]:
        return "up"
    
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
