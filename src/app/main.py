from fastapi import FastAPI
from mangum import Mangum
import random


app = FastAPI()

# TODO: Implement my logic here to handle the requests from Battlesnake

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
def start_func(request: dict) :
    data = request["game"]["id"]
    print(data)
    return "ok"

@app.post("/move")
def move_func(game : dict, turn : int, board : dict, me : dict) :

    possibleTiles = avoidEdges(me, board)

    return randomMove(possibleTiles)

def getNextTiles(me : dict) :
    myHead = me["head"]
    headX = myHead["x"]
    headY = myHead["y"]

    adjacentTiles = {"up" : {"x":headX, "y":headY+1},
                         "down" : {"x":headX, "y":headY-1},
                         "left" : {"x":headX-1, "y":headY},
                         "right" : {"x":headX+1, "y":headY}}

    return adjacentTiles

def avoidBackwards(me : dict) :
    possibleTiles = getNextTiles(me)
    myBack = me["body"][1]
    for k in ["up","down","left","right"]:
        if possibleTiles[k] == myBack:
            del possibleTiles[k]
            return possibleTiles
    return possibleTiles

def avoidEdges(me : dict, board : dict) :
    possibleTiles = avoidBackwards(me)
    lastX = board["width"] - 1
    lastY = board["height"] - 1
    if me["head"]["x"] == 0:
        del possibleTiles["left"]
    elif me["head"]["y"] == 0:
        del possibleTiles["down"]
    elif me["head"]["x"] == lastX:
        del possibleTiles["right"]
    elif me["head"]["y"] == lastY:
        del possibleTiles["up"]
    return possibleTiles

def randomMove(possibleTiles : dict) :
    possibleDirections = list(possibleTiles.keys())
    return random.choice(possibleDirections)


handler = Mangum(app, lifespan="off")
