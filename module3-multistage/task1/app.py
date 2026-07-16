from fastapi import FastAPI

app = FastAPI()


#this string was changed, this is the first change
@app.get("/")
def root():
    return {"message": "Hello, World!"}


@app.get("/hello")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}
