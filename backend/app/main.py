from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import dialog_mobile_employees, dialog_mobile_bills, mobitel_employees, mobitel_bills, dialog_data_employees, dialog_data_bills, slt_team_package_bills, slt_general_bills

app = FastAPI(title="MIT Billing", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "https://mit-billing-frontend-production.up.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dialog_mobile_employees.router)
app.include_router(dialog_mobile_bills.router)
app.include_router(mobitel_employees.router)
app.include_router(mobitel_bills.router)
app.include_router(dialog_data_employees.router)
app.include_router(dialog_data_bills.router)
app.include_router(slt_team_package_bills.router)
app.include_router(slt_general_bills.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}