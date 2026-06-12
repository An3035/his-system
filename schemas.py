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
    patient_id: Optional[int] = None  # 患者角色用户关联的 Patient ID


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


# ── 患者自助注册 ──────────────────────────────────────────────────


class PatientRegisterRequest(BaseModel):
    """患者自助注册请求"""
    name: str
    gender: str = "男"
    phone: str
    id_card: Optional[str] = None
    password: str  # 登录密码
    birth_date: Optional[date] = None


class PatientSelfOut(BaseModel):
    """患者端个人信息输出"""
    id: int
    patient_no: str
    name: str
    gender: str
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    id_card: Optional[str] = None
    created_at: Optional[datetime] = None


class PatientRegSelfOut(BaseModel):
    """患者端挂号记录输出"""
    id: int
    reg_no: str
    reg_type: str
    reg_fee: str
    payment_status: str
    reg_date: Optional[datetime] = None
    visit_date: Optional[date] = None
    department_name: str = ""
    doctor_name: str = ""


class PatientPresSelfOut(BaseModel):
    """患者端处方输出"""
    id: int
    pres_no: str
    pres_type: str
    total_amount: str
    payment_status: str
    dispensed: bool
    created_at: Optional[datetime] = None
    diagnosis: Optional[str] = None
    items: list = []  # [{drug_name, quantity, unit, amount}]


class PatientBillSelfOut(BaseModel):
    """患者端账单输出"""
    id: int
    bill_no: str
    charge_type: str
    ref_no: str = ""
    total_amount: str
    paid_amount: str
    charge_time: Optional[datetime] = None
    status: str


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


# ── 生命体征 ──────────────────────────────────


class VitalSignCreate(BaseModel):
    patient_id: int
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    respiration: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    record_time: Optional[str] = None  # "YYYY-MM-DD HH:mm:ss"


class VitalSignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    respiration: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    record_time: Optional[datetime] = None
    recorder_name: Optional[str] = None


# ── AI ───────────────────────────────────────────────────────
from pydantic import BaseModel, Field
from typing import List, Optional


class AiChatRequest(BaseModel):
    message: str
    context_type: str = "general"
    context_id: Optional[int] = None
    history: List[dict] = Field(default_factory=list)
    session_id: Optional[int] = None  # 续已有会话时传入


class AiChatResponse(BaseModel):
    reply: str
    model: str
    rejected: bool = False
    session_id: int = 0  # 当前消息所属的会话ID


class AiSessionOut(BaseModel):
    """会话列表项"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: Optional[str] = None
    context_type: str = "general"
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class AiSessionDetailOut(BaseModel):
    """会话详情（含解析后的消息）"""
    id: int
    title: Optional[str] = None
    messages: list = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SessionRenameRequest(BaseModel):
    title: str


class BatchDeleteRequest(BaseModel):
    ids: List[int]


class AiTriageRequest(BaseModel):
    symptoms: str


class DirectorQueryRequest(BaseModel):
    question: str


class PrescriptionCheckItem(BaseModel):
    drug_id: int
    quantity: Decimal
    unit: str = ""


class PrescriptionCheckRequest(BaseModel):
    patient_id: Optional[int] = None
    items: List[PrescriptionCheckItem]


# ── 语音识别 (ASR) ────────────────────────────────────────────────


class AsrResponse(BaseModel):
    text: str
    duration: Optional[float] = None
    error: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ── 统计报表 ─────────────────────────────────────────────────


class DashboardStats(BaseModel):
    today_registrations: int
    today_revenue: Decimal
    today_reg_revenue: Decimal = Decimal("0")    # 挂号费收入
    today_pres_revenue: Decimal = Decimal("0")   # 处方费收入
    today_adm_revenue: Decimal = Decimal("0")    # 住院结算收入
    inpatients: int
    available_beds: int
    low_stock_drugs: int
    pending_orders: int


# ── 统一收费主表 ─────────────────────────────────────────────────


class BillingRecordOut(BaseModel):
    """收费历史记录输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    bill_no: str
    charge_type: str  # 挂号收费 / 门诊处方 / 住院结算
    source_id: int
    patient_id: int
    patient_name: Optional[str] = None
    patient_no: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    total_amount: Decimal
    paid_amount: Decimal
    operator_name: Optional[str] = None
    charge_time: datetime
    status: str
    remark: Optional[str] = None
    ref_no: Optional[str] = None  # 业务单号（reg_no / pres_no / admission_no）


class PendingChargeOut(BaseModel):
    """待收费项目输出（统一格式，兼容前端 ChargeItem）"""
    id: int
    type: str  # registration / prescription / admission
    charge_type_label: str  # 挂号收费 / 门诊处方 / 住院结算
    no: str  # 业务单号
    patient_id: int
    patient_no: str = ""
    patient_name: str = ""
    gender: Optional[str] = None
    age: Optional[int] = None
    total_amount: Decimal
    pay_amount: Decimal
    deposit: Decimal = Decimal("0")
    created_at: Optional[datetime] = None


class ReconciliationResult(BaseModel):
    """智能对账结果"""
    date: str
    dashboard_total: Decimal
    billing_total: Decimal
    difference: Decimal
    matched: bool
    details: list = Field(default_factory=list)  # 差异明细


class BillingSummary(BaseModel):
    """收费汇总"""
    total_amount: Decimal = Decimal("0")
    count: int = 0
    by_type: dict = Field(default_factory=dict)  # {"挂号收费": amount, ...}


# ── 审计日志 ─────────────────────────────────────────────────


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


# ── 知识库 ───────────────────────────────────────────────────


class KnowledgeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    title: str
    doc_type: str
    uploaded_by: int
    chunk_count: int
    is_active: bool
    created_at: datetime


class KBSearchResult(BaseModel):
    content: str
    document_title: str
    score: float
