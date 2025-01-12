from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/output", StaticFiles(directory="./output"), name="output")
