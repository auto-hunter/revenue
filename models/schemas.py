from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionRecord(BaseModel):
    """One extracted weight row from a transaction statement."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    product_spec: str | None = Field(None, alias="품명 및 규격")
    gross_weight: float | None = Field(None, alias="총중량")
    bobbin_weight: float | None = Field(None, alias="보빈중량")
    net_weight: float | None = Field(None, alias="실중량")
    subtotal: float | None = Field(None, alias="소계")
    bobbin_spec: str | None = Field(None, alias="보빈명세 규격")
    bobbin_quantity: int | None = Field(None, alias="보빈명세 수량")
    customer: str | None = Field(None, alias="거래처")
    corporate_entity: Literal["태일전선", "태일소재"] | None = Field(None, alias="거래법인")
    transaction_date: date | None = Field(None, alias="날짜")
    source_file: str
    page_number: int

    @field_validator("gross_weight", "bobbin_weight", "net_weight", "subtotal", mode="before")
    @classmethod
    def normalize_number(cls, value):
        if isinstance(value, str):
            value = value.replace(",", "").replace("kg", "").strip()
        return None if value in (None, "") else value

    @field_validator("corporate_entity", mode="before")
    @classmethod
    def normalize_corporate_entity(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class PageError(BaseModel):
    source_file: str
    page_number: int | None
    message: str


class PageAnalysis(BaseModel):
    records: list[TransactionRecord] = Field(default_factory=list)
    error: PageError | None = None
