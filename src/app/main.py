from fastapi import FastAPI
from mangum import Mangum

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
    print(name)

    return {"item_id": item_id,
            "name": name}

@app.post("/start")
def start_func() :
    data = request.get_json()
    print(data)
    return "ok"

@app.post("/move")
def start_func() :
    data = request.get_json()


    return {"move": "left"}


handler = Mangum(app, lifespan="off")
