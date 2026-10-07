from fastapi import FastAPI
from app.routes import shipments
app = FastAPI(title= "Sentiment Analysis API", description= "API for sentiment analysis of text data", version= "1.0.0")
app.include_router(shipments.router)
@app.get("/root")
def root():
    return {"status" : "API is running succesfully"}



