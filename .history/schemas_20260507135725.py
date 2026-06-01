"""
schemas.py — Pydantic v2 请求/响应模型
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ── 通用 ─────────────────────────────────────────────────────


class Msg(BaseModel):
    message: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── 认证 ─────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    real_name: str
    role: str
    department_id: Optional[int] = None


# ── 患者 ─────────────────────────────────────────────────────


class PatientCreate(BaseModel):
    name: str
    gender: str
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    ic_card_no: Optional[str] = None


class PatientOut(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_no: str
    created_at: datetime


# ── 挂号 ─────────────────────────────────────────────────────


class RegistrationCreate(BaseModel):
    patient_id: int
    doctor_id: int
    reg_type: str = "普通"
    visit_date: Optional[date] = None
    remark: Optional[str] = None


class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reg_no: str
    patient_id: int
    doctor_id: int
    reg_type: str
    reg_fee: Decimal
    payment_status: str
    reg_date: datetime
    visit_date: Optional[date]


# ── 处方 ─────────────────────────────────────────────────────


class PrescriptionItemCreate(BaseModel):
    drug_id: int
    quantity: Decimal
    unit: str
    usage_instruction: Optional[str] = None


class PrescriptionCreate(BaseModel):
    registration_id: int
    pres_type: str
    diagnosis: Optional[str] = None
    items: List[PrescriptionItemCreate]


class PrescriptionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    drug_id: int
    quantity: Decimal
    unit: str
    unit_price: Decimal
    amount: Decimal
    usage_instruction: Optional[str]


class PrescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pres_no: str
    registration_id: int
    pres_type: str
    total_amount: Decimal
    payment_status: str
    dispensed: bool
    created_at: datetime
    items: List[PrescriptionItemOut] = []


# ── 药品 ─────────────────────────────────────────────────────


class DrugCreate(BaseModel):
    drug_code: str
    name: str
    generic_name: Optional[str] = None
    drug_type: str
    specification: Optional[str] = None
    unit: str
    retail_price: Decimal
    purchase_price: Decimal
    manufacturer: Optional[str] = None


class DrugOut(DrugCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    drug_id: int
    stock_qty: Decimal
    alert_qty: Decimal
    pharmacy_type: str
    updated_at: datetime
    drug: DrugOut


# ── 住院 ─────────────────────────────────────────────────────


class AdmissionCreate(BaseModel):
    patient_id: int
    bed_id: int
    department_id: int
    deposit: Decimal = Decimal("0")
    diagnosis: Optional[str] = None


class AdmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    admission_no: str
    patient_id: int
    bed_id: int
    department_id: int
    admit_date: datetime
    discharge_date: Optional[datetime]
    deposit: Decimal
    total_fee: Decimal
    settled: bool


# ── 医嘱 ─────────────────────────────────────────────────────


class MedicalOrderCreate(BaseModel):
    admission_id: int
    order_type: str
    content: str


class MedicalOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    admission_id: int
    order_type: str
    content: str
    status: str
    created_at: datetime
    executed_at: Optional[datetime]


# ── 床位 ─────────────────────────────────────────────────────


class BedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bed_no: str
    ward: str
    department_id: int
    status: str


# ── AI ───────────────────────────────────────────────────────


class AiChatRequest(BaseModel):
    message: str
    context_type: str = "general"
    context_id: Optional[int] = None
    history: List[dict] = Field(default_factory=list)


class AiChatResponse(BaseModel):
    reply: str
    model: str


# ── 统计报表 ─────────────────────────────────────────────────


class DashboardStats(BaseModel):
    today_registrations: int
    today_revenue: Decimal
    inpatients: int
    available_beds: int
    low_stock_drugs: int
    pending_orders: int
