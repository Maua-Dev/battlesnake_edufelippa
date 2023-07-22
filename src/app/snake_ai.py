import random

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