from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import employees

app = FastAPI(title="MIT Mobile Billing", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)


@app.on_event("startup")
def on_startup():
    # Dev convenience only. Once the schema stabilizes, switch to Alembic
    # migrations (`alembic upgrade head`) instead of create_all, so schema
    # changes are tracked and reversible rather than silently applied.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}