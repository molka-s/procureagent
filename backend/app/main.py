from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="ProcureAgent")
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"ok": True}
