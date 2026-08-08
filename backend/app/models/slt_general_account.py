import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func

from app.database import Base
from app.types import GUID


class SltGeneralAccount(Base):
    """
    One row per known "general" SLT account — confirmed fixed/recurring
    every month: 4 accounts (001 614 8516, 004 921 8178, 005 039 721X,
    005 065 530X), none of which get split among employees, unlike the
    team package account. Auto-created on first import if not already
    known, using the account number found in the PDF; the label can be
    renamed afterward to something more readable (e.g. "Enterprise
    Broadband + Static IP") from the Employees-style management page.
    """

    __tablename__ = "slt_general_accounts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    account_no = Column(String, unique=True, nullable=False, index=True)
    label = Column(String, nullable=False)   # defaults to account_no, user-editable

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())