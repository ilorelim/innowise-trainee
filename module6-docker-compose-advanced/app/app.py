from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello, World!"}


@app.get("/hello")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}
