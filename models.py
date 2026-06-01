"""
models.py — SQLAlchemy ORM 模型
覆盖 HIS 全部 15 个功能模块的数据库表定义。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ── Base ─────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


def now() -> datetime:
    return datetime.now()


# ── Enums ────────────────────────────────────────────────────────────────────


class RegistrationType(str, PyEnum):
    NORMAL = "普通"
    EXPERT = "专家"
    EMERGENCY = "急诊"
    SPECIAL = "专科"


class PrescriptionType(str, PyEnum):
    CHINESE = "中药"
    WESTERN = "西药"


class GenderType(str, PyEnum):
    MALE = "男"
    FEMALE = "女"
    OTHER = "其他"


class BedStatus(str, PyEnum):
    AVAILABLE = "空闲"
    OCCUPIED = "占用"
    RESERVED = "预留"
    MAINTENANCE = "维修"


class OrderStatus(str, PyEnum):
    ACTIVE = "执行中"
    PENDING_DISPENSE = "待发药"
    DISPENSED = "已发药"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


class PaymentStatus(str, PyEnum):
    PENDING = "待付"
    PAID = "已付"
    REFUNDED = "已退"


# ═══════════════════════════════════════════════════════════════════════
# 1. 用户 & 员工
# ═══════════════════════════════════════════════════════════════════════


class Department(Base):
    """科室"""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    doctors: Mapped[List["Doctor"]] = relationship(back_populates="department")


class Doctor(Base):
    """医生"""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(50))  # 职称
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    introduction: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    department: Mapped["Department"] = relationship(back_populates="doctors")
    registrations: Mapped[List["Registration"]] = relationship(back_populates="doctor")


class User(Base):
    """系统用户（员工账号）"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(30))  # admin/doctor/nurse/pharmacist/cashier
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)


# ═══════════════════════════════════════════════════════════════════════
# 2. 患者
# ═══════════════════════════════════════════════════════════════════════


class Patient(Base):
    """患者基本信息"""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[GenderType] = mapped_column(Enum(GenderType))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    id_card: Mapped[Optional[str]] = mapped_column(String(18), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    ic_card_no: Mapped[Optional[str]] = mapped_column(String(30), unique=True)  # IC卡
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    registrations: Mapped[List["Registration"]] = relationship(back_populates="patient")
    admissions: Mapped[List["Admission"]] = relationship(back_populates="patient")


# ═══════════════════════════════════════════════════════════════════════
# 模块 1: 门诊挂号管理
# ═══════════════════════════════════════════════════════════════════════


class Registration(Base):
    """挂号记录"""

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reg_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    reg_type: Mapped[RegistrationType] = mapped_column(
        Enum(RegistrationType), default=RegistrationType.NORMAL
    )
    reg_fee: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )
    reg_date: Mapped[datetime] = mapped_column(DateTime, default=now)
    visit_date: Mapped[Optional[date]] = mapped_column(Date)
    remark: Mapped[Optional[str]] = mapped_column(Text)

    patient: Mapped["Patient"] = relationship(back_populates="registrations")
    doctor: Mapped["Doctor"] = relationship(back_populates="registrations")
    prescriptions: Mapped[List["Prescription"]] = relationship(back_populates="registration")


# ═══════════════════════════════════════════════════════════════════════
# 模块 2+3: 处方 / 划价 / 收费
# ═══════════════════════════════════════════════════════════════════════


class Prescription(Base):
    """处方"""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pres_no: Mapped[str] = mapped_column(String(20), unique=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id"))
    pres_type: Mapped[PrescriptionType] = mapped_column(Enum(PrescriptionType))
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )
    dispensed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)

    registration: Mapped["Registration"] = relationship(back_populates="prescriptions")
    items: Mapped[List["PrescriptionItem"]] = relationship(
        back_populates="prescription", cascade="all, delete-orphan"
    )


class PrescriptionItem(Base):
    """处方明细"""

    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"))
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 3))
    unit: Mapped[str] = mapped_column(String(20))
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    usage_instruction: Mapped[Optional[str]] = mapped_column(String(200))

    prescription: Mapped["Prescription"] = relationship(back_populates="items")
    drug: Mapped["Drug"] = relationship()


# ═══════════════════════════════════════════════════════════════════════
# 模块 4+6: 药品 / 药房 / 药库
# ═══════════════════════════════════════════════════════════════════════


class Drug(Base):
    """药品主档"""

    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    generic_name: Mapped[Optional[str]] = mapped_column(String(100))
    drug_type: Mapped[PrescriptionType] = mapped_column(Enum(PrescriptionType))
    specification: Mapped[Optional[str]] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20))
    retail_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    purchase_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PharmacyInventory(Base):
    """药房库存（门诊/中心药房）"""

    __tablename__ = "pharmacy_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), unique=True)
    stock_qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 3), default=0)
    alert_qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 3), default=10)
    pharmacy_type: Mapped[str] = mapped_column(String(20), default="门诊")  # 门诊/中心/中药/西药
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    drug: Mapped["Drug"] = relationship()


class WarehouseInventory(Base):
    """药库库存"""

    __tablename__ = "warehouse_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), unique=True)
    stock_qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 3), default=0)
    warehouse_type: Mapped[str] = mapped_column(String(20))  # 中药库/西药库
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    drug: Mapped["Drug"] = relationship()


class DrugTransaction(Base):
    """药品出入库流水"""

    __tablename__ = "drug_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"))
    trans_type: Mapped[str] = mapped_column(String(20))  # 入库/出库/退药/盘点
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(12, 3))
    source: Mapped[str] = mapped_column(String(50))  # 来源模块
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    remark: Mapped[Optional[str]] = mapped_column(String(200))

    drug: Mapped["Drug"] = relationship()


# ═══════════════════════════════════════════════════════════════════════
# 模块 7: 出入院管理
# ═══════════════════════════════════════════════════════════════════════


class Bed(Base):
    """床位"""

    __tablename__ = "beds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bed_no: Mapped[str] = mapped_column(String(20), unique=True)
    ward: Mapped[str] = mapped_column(String(50))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    status: Mapped[BedStatus] = mapped_column(Enum(BedStatus), default=BedStatus.AVAILABLE)


class Admission(Base):
    """住院记录"""

    __tablename__ = "admissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admission_no: Mapped[str] = mapped_column(String(20), unique=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    admit_date: Mapped[datetime] = mapped_column(DateTime, default=now)
    discharge_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deposit: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0)
    total_fee: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0)
    settled: Mapped[bool] = mapped_column(Boolean, default=False)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)

    patient: Mapped["Patient"] = relationship(back_populates="admissions")
    bed: Mapped["Bed"] = relationship()
    department: Mapped["Department"] = relationship()
    medical_orders: Mapped[List["MedicalOrder"]] = relationship(back_populates="admission")
    fee_items: Mapped[List["AdmissionFeeItem"]] = relationship(back_populates="admission")


class AdmissionFeeItem(Base):
    """住院费用明细"""

    __tablename__ = "admission_fee_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("admissions.id"))
    fee_date: Mapped[date] = mapped_column(Date, default=date.today)
    category: Mapped[str] = mapped_column(String(50))  # 药品/检查/手术/护理
    item_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 3))
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))

    admission: Mapped["Admission"] = relationship(back_populates="fee_items")


# ═══════════════════════════════════════════════════════════════════════
# 模块 8: 护士工作站 / 医嘱
# ═══════════════════════════════════════════════════════════════════════


class MedicalOrder(Base):
    """医嘱"""

    __tablename__ = "medical_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("admissions.id"))
    order_type: Mapped[str] = mapped_column(String(30))  # 药品/检验/手术/功能检查/中医
    content: Mapped[str] = mapped_column(Text)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    nurse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    admission: Mapped["Admission"] = relationship(back_populates="medical_orders")
    doctor: Mapped["Doctor"] = relationship()
    nurse: Mapped["User"] = relationship()


class VitalSign(Base):
    """生命体征记录（护士工作站）"""

    __tablename__ = "vital_signs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    temperature: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 1))  # 体温 °C
    pulse: Mapped[Optional[int]] = mapped_column(Integer)                # 脉搏 次/分
    respiration: Mapped[Optional[int]] = mapped_column(Integer)          # 呼吸 次/分
    systolic_bp: Mapped[Optional[int]] = mapped_column(Integer)           # 收缩压 mmHg
    diastolic_bp: Mapped[Optional[int]] = mapped_column(Integer)          # 舒张压 mmHg
    record_time: Mapped[datetime] = mapped_column(DateTime, default=now)
    recorder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    patient: Mapped["Patient"] = relationship()
    recorder: Mapped["User"] = relationship()


# ═══════════════════════════════════════════════════════════════════════
# 模块 10-12: 检验/手术/功能科室收费
# ═══════════════════════════════════════════════════════════════════════


class ChargeItem(Base):
    """收费项目主档（检验/手术/功能科室）"""

    __tablename__ = "charge_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(30))  # 检验/手术/B超/胃镜/放射
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SpecialCharge(Base):
    """特殊科室收费记录（检验/手术/功能）"""

    __tablename__ = "special_charges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("medical_orders.id"))
    charge_item_id: Mapped[int] = mapped_column(ForeignKey("charge_items.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    order: Mapped["MedicalOrder"] = relationship()
    charge_item: Mapped["ChargeItem"] = relationship()


# ═══════════════════════════════════════════════════════════════════════
# AI 会话记录
# ═══════════════════════════════════════════════════════════════════════


class AiSession(Base):
    """AI 助手会话历史"""

    __tablename__ = "ai_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[Optional[str]] = mapped_column(String(200))  # 自动从首条消息生成
    context_type: Mapped[str] = mapped_column(String(30))  # patient/drug/report/general
    context_id: Mapped[Optional[int]] = mapped_column(Integer)
    messages: Mapped[str] = mapped_column(Text)  # JSON array of all messages
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)


# ═══════════════════════════════════════════════════════════════════════
# 审计日志
# ═══════════════════════════════════════════════════════════════════════


class AuditLog(Base):
    """操作审计日志"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(50))  # ai_chat / patient_query / kb_search / drug_check
    target_type: Mapped[Optional[str]] = mapped_column(String(50))  # patient / drug / knowledge_base
    target_id: Mapped[Optional[int]] = mapped_column(Integer)
    detail: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


# ═══════════════════════════════════════════════════════════════════════
# RAG 知识库
# ═══════════════════════════════════════════════════════════════════════


class KnowledgeDocument(Base):
    """知识库文档"""

    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    doc_type: Mapped[str] = mapped_column(String(20))  # pdf / docx / txt
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class KnowledgeChunk(Base):
    """知识库文档分块"""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[str]] = mapped_column(Text)  # JSON float array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
