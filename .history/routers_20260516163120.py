"""
routers.py — 全部 API 路由（15个功能模块 + AI + 统计）
"""

from __future__ import annotations

import json
import random
import string
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import schemas
from ai_service import (
    analyze_drug_interaction,
    chat_with_ai,
    interpret_report_data,
    summarize_patient_history,
)
from auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from database import get_db
from models import (
    Admission,
    AdmissionFeeItem,
    AiSession,
    Bed,
    BedStatus,
    ChargeItem,
    Department,
    Doctor,
    Drug,
    DrugTransaction,
    MedicalOrder,
    OrderStatus,
    Patient,
    PaymentStatus,
    PharmacyInventory,
    Prescription,
    PrescriptionItem,
    Registration,
    SpecialCharge,
    User,
    WarehouseInventory,
)


def _gen_no(prefix: str, length: int = 8) -> str:
    """生成业务编号。"""
    suffix = "".join(random.choices(string.digits, k=length))
    return f"{prefix}{datetime.now().strftime('%Y%m%d')}{suffix}"


# ══════════════════════════════════════════════════════════════
# 认证路由
# ══════════════════════════════════════════════════════════════

auth_router = APIRouter(prefix="/api/auth", tags=["认证"])


@auth_router.post("/login", response_model=schemas.Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")

    user.last_login = datetime.now()
    await db.commit()

    return schemas.Token(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token(user.id),
    )


@auth_router.get("/me", response_model=schemas.UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# ══════════════════════════════════════════════════════════════
# 模块 1: 门诊挂号管理
# ══════════════════════════════════════════════════════════════

reg_router = APIRouter(prefix="/api/registrations", tags=["挂号管理"])

FEE_MAP = {
    "普通": Decimal("5"),
    "专家": Decimal("20"),
    "急诊": Decimal("15"),
    "专科": Decimal("10"),
}


@reg_router.post("", response_model=schemas.RegistrationOut)
async def create_registration(
    body: schemas.RegistrationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "cashier")),
):
    reg = Registration(
        reg_no=_gen_no("REG"),
        patient_id=body.patient_id,
        doctor_id=body.doctor_id,
        reg_type=body.reg_type,
        reg_fee=FEE_MAP.get(body.reg_type, Decimal("5")),
        visit_date=body.visit_date,
        remark=body.remark,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(reg)
    await db.commit()
    await db.refresh(reg)
    return reg


@reg_router.get("", response_model=List[schemas.RegistrationOut])
async def list_registrations(
    patient_id: Optional[int] = Query(None),
    visit_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Registration)
    if patient_id:
        q = q.where(Registration.patient_id == patient_id)
    if visit_date:
        q = q.where(func.date(Registration.visit_date) == visit_date)
    result = await db.execute(q.order_by(Registration.reg_date.desc()).limit(200))
    return result.scalars().all()


@reg_router.patch("/{reg_id}/pay", response_model=schemas.RegistrationOut)
async def pay_registration(
    reg_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "cashier")),
):
    result = await db.execute(select(Registration).where(Registration.id == reg_id))
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(404, "挂号记录不存在")
    reg.payment_status = PaymentStatus.PAID
    await db.commit()
    await db.refresh(reg)
    return reg


# ══════════════════════════════════════════════════════════════
# 患者管理
# ══════════════════════════════════════════════════════════════
patient_router = APIRouter(prefix="/api/patients", tags=["患者管理"])


@patient_router.get("", response_model=dict)
async def list_patients(
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Patient)

    if q:
        query = query.where(
            Patient.name.ilike(f"%{q}%")
            | Patient.patient_no.ilike(f"%{q}%")
            | Patient.id_card.ilike(f"%{q}%")
        )

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    patients = result.scalars().all()

    return {"items": patients, "total": total, "page": page, "page_size": page_size}


@patient_router.get("/{patient_id}", response_model=schemas.PatientOut)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "患者不存在")
    return patient


@patient_router.post("", response_model=schemas.PatientOut)
async def create_patient(
    body: schemas.PatientCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    patient = Patient(patient_no=_gen_no("P"), **body.dict())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@patient_router.put("/{patient_id}", response_model=schemas.PatientOut)
async def update_patient(
    patient_id: int,
    body: schemas.PatientCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "患者不存在")

    for key, value in body.dict().items():
        setattr(patient, key, value)

    await db.commit()
    await db.refresh(patient)
    return patient


@patient_router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "患者不存在")

    await db.delete(patient)
    await db.commit()
    return {"message": "删除成功"}


# ══════════════════════════════════════════════════════════════
# 模块 2+3: 处方划价 & 门诊收费
# ══════════════════════════════════════════════════════════════

pres_router = APIRouter(prefix="/api/prescriptions", tags=["处方管理"])


@pres_router.get("", response_model=dict)
async def list_prescriptions(
    payment_status: Optional[str] = Query(None),
    patient_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Prescription).options(
        selectinload(Prescription.patient), selectinload(Prescription.items)
    )

    if payment_status:
        query = query.where(Prescription.payment_status == payment_status)

    if patient_name:
        query = query.join(Patient).where(Patient.name.ilike(f"%{patient_name}%"))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    prescriptions = result.scalars().all()

    return {"items": prescriptions, "total": total, "page": page, "page_size": page_size}


@pres_router.post("", response_model=schemas.PrescriptionOut)
async def create_prescription(
    body: schemas.PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "doctor")),
):
    # 划价：查询药品单价，计算总金额
    total = Decimal("0")
    items_data = []
    for item in body.items:
        drug_result = await db.execute(select(Drug).where(Drug.id == item.drug_id))
        drug = drug_result.scalar_one_or_none()
        if not drug:
            raise HTTPException(404, f"药品 {item.drug_id} 不存在")
        amount = drug.retail_price * item.quantity
        total += amount
        items_data.append((item, drug.retail_price, amount))

    pres = Prescription(
        pres_no=_gen_no("RX"),
        registration_id=body.registration_id,
        pres_type=body.pres_type,
        diagnosis=body.diagnosis,
        total_amount=total,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(pres)
    await db.flush()

    for item, unit_price, amount in items_data:
        db.add(
            PrescriptionItem(
                prescription_id=pres.id,
                drug_id=item.drug_id,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=unit_price,
                amount=amount,
                usage_instruction=item.usage_instruction,
            )
        )

    await db.commit()
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.id == pres.id)
    )
    return result.scalar_one()


@pres_router.patch("/{pres_id}/pay", response_model=schemas.PrescriptionOut)
async def pay_prescription(
    pres_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "cashier")),
):
    """门诊收费 — 支付处方，自动推送至药房发药窗口（模块5）。"""
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.id == pres_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        raise HTTPException(404, "处方不存在")
    pres.payment_status = PaymentStatus.PAID
    # 模块5: 划价收费后处方自动传到药房发药窗口（标记待发药）
    # 实际生产中可通过 WebSocket / Redis Pub-Sub 推送
    await db.commit()
    await db.refresh(pres)
    return pres


@pres_router.get("/pending-dispense", response_model=List[schemas.PrescriptionOut])
async def pending_dispense(
    db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "pharmacist"))
):
    """模块5: 药房发药窗口 — 获取已付款待发药处方列表。"""
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.payment_status == PaymentStatus.PAID, Prescription.dispensed == False)
        .order_by(Prescription.created_at)
    )
    return result.scalars().all()


@pres_router.patch("/{pres_id}/dispense")
async def dispense_prescription(
    pres_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "pharmacist")),
):
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.id == pres_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        raise HTTPException(404, "处方不存在")
    pres.dispensed = True
    # 扣减库存
    for item in pres.items:
        inv = await db.execute(
            select(PharmacyInventory).where(PharmacyInventory.drug_id == item.drug_id)
        )
        inv_obj = inv.scalar_one_or_none()
        if inv_obj:
            inv_obj.stock_qty = max(Decimal("0"), inv_obj.stock_qty - item.quantity)
    await db.commit()
    return {"message": "发药完成"}


# ══════════════════════════════════════════════════════════════
# 模块 4: 药房系统（库存 / 盘点 / 退药 / 销量统计）
# ══════════════════════════════════════════════════════════════

pharm_router = APIRouter(prefix="/api/pharmacy", tags=["药房系统"])


@pharm_router.get("/inventory", response_model=List[schemas.InventoryOut])
async def list_inventory(
    low_stock: bool = Query(False),
    pharmacy_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(PharmacyInventory).options(selectinload(PharmacyInventory.drug))
    if low_stock:
        q = q.where(PharmacyInventory.stock_qty <= PharmacyInventory.alert_qty)
    if pharmacy_type:
        q = q.where(PharmacyInventory.pharmacy_type == pharmacy_type)
    result = await db.execute(q)
    return result.scalars().all()


@pharm_router.post("/return-drug")
async def return_drug(
    drug_id: int,
    quantity: Decimal,
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pharmacist")),
):
    """退药：增加库存并记录流水。"""
    inv = await db.execute(select(PharmacyInventory).where(PharmacyInventory.drug_id == drug_id))
    inv_obj = inv.scalar_one_or_none()
    if inv_obj:
        inv_obj.stock_qty += quantity
    db.add(
        DrugTransaction(
            drug_id=drug_id,
            trans_type="退药",
            quantity=quantity,
            source="处方",
            source_id=prescription_id,
            operator_id=current_user.id,
        )
    )
    await db.commit()
    return {"message": "退药成功"}


@pharm_router.get("/sales-stats")
async def sales_stats(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "pharmacist")),
):
    """销量统计报表。"""
    result = await db.execute(
        select(
            Drug.name,
            func.sum(PrescriptionItem.quantity).label("total_qty"),
            func.sum(PrescriptionItem.amount).label("total_amount"),
        )
        .join(PrescriptionItem, PrescriptionItem.drug_id == Drug.id)
        .join(Prescription, Prescription.id == PrescriptionItem.prescription_id)
        .where(
            Prescription.payment_status == PaymentStatus.PAID,
            func.date(Prescription.created_at).between(start_date, end_date),
        )
        .group_by(Drug.id)
        .order_by(func.sum(PrescriptionItem.amount).desc())
        .limit(50)
    )
    return [
        {"drug_name": r.name, "total_qty": r.total_qty, "total_amount": r.total_amount}
        for r in result
    ]


# ══════════════════════════════════════════════════════════════
# 模块 4+6: 药库管理系统
# ══════════════════════════════════════════════════════════════

warehouse_router = APIRouter(prefix="/api/warehouse", tags=["药库管理"])


@warehouse_router.get("/inventory")
async def warehouse_inventory(
    warehouse_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(WarehouseInventory).options(selectinload(WarehouseInventory.drug))
    if warehouse_type:
        q = q.where(WarehouseInventory.warehouse_type == warehouse_type)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "drug": r.drug.name,
            "stock_qty": r.stock_qty,
            "warehouse_type": r.warehouse_type,
        }
        for r in rows
    ]


@warehouse_router.post("/stock-in")
async def stock_in(
    drug_id: int,
    quantity: Decimal,
    warehouse_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pharmacist")),
):
    """入库。"""
    inv = await db.execute(
        select(WarehouseInventory).where(
            WarehouseInventory.drug_id == drug_id,
            WarehouseInventory.warehouse_type == warehouse_type,
        )
    )
    inv_obj = inv.scalar_one_or_none()
    if inv_obj:
        inv_obj.stock_qty += quantity
    else:
        db.add(
            WarehouseInventory(drug_id=drug_id, stock_qty=quantity, warehouse_type=warehouse_type)
        )
    db.add(
        DrugTransaction(
            drug_id=drug_id,
            trans_type="入库",
            quantity=quantity,
            source="药库",
            operator_id=current_user.id,
        )
    )
    await db.commit()
    return {"message": "入库成功"}


# ══════════════════════════════════════════════════════════════
# 药品主档
# ══════════════════════════════════════════════════════════════

drug_router = APIRouter(prefix="/api/drugs", tags=["药品管理"])


@drug_router.post("", response_model=schemas.DrugOut)
async def create_drug(
    body: schemas.DrugCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    drug = Drug(**body.model_dump())
    db.add(drug)
    await db.commit()
    await db.refresh(drug)
    return drug


@drug_router.get("", response_model=List[schemas.DrugOut])
async def list_drugs(
    q: str = Query(""),
    drug_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Drug).where(Drug.is_active == True)
    if q:
        stmt = stmt.where(Drug.name.contains(q) | Drug.drug_code.contains(q))
    if drug_type:
        stmt = stmt.where(Drug.drug_type == drug_type)
    result = await db.execute(stmt.limit(100))
    return result.scalars().all()


# ══════════════════════════════════════════════════════════════
# 模块 7: 出入院管理
# ══════════════════════════════════════════════════════════════

admission_router = APIRouter(prefix="/api/admissions", tags=["出入院管理"])


# 然后在所有接口的最上面添加这个列表接口
@admission_router.get("", response_model=dict)
async def list_admissions(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取入院记录列表，支持按住院号/患者ID搜索和分页。"""
    query = select(Admission)

    # 搜索条件
    if q:
        query = query.where(
            (Admission.admission_no.ilike(f"%{q}%")) | (Admission.patient_id.ilike(f"%{q}%"))
        )

    # 计算总数
    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    # 分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    admissions = result.scalars().all()

    return {"items": admissions, "total": total, "page": page, "page_size": page_size}


@admission_router.post("", response_model=schemas.AdmissionOut)
async def admit_patient(
    body: schemas.AdmissionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "nurse")),
):
    # 标记床位为占用
    bed_result = await db.execute(select(Bed).where(Bed.id == body.bed_id))
    bed = bed_result.scalar_one_or_none()
    if not bed or bed.status != BedStatus.AVAILABLE:
        raise HTTPException(400, "床位不可用")
    bed.status = BedStatus.OCCUPIED

    admission = Admission(
        admission_no=_gen_no("ADM"),
        patient_id=body.patient_id,
        bed_id=body.bed_id,
        department_id=body.department_id,
        deposit=body.deposit,
        diagnosis=body.diagnosis,
    )
    db.add(admission)
    await db.commit()
    await db.refresh(admission)
    return admission


@admission_router.patch("/{adm_id}/discharge")
async def discharge_patient(
    adm_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "cashier")),
):
    """出院结算。"""
    result = await db.execute(
        select(Admission).options(selectinload(Admission.fee_items)).where(Admission.id == adm_id)
    )
    adm = result.scalar_one_or_none()
    if not adm:
        raise HTTPException(404, "住院记录不存在")
    total = sum(item.amount for item in adm.fee_items)
    adm.total_fee = total
    adm.discharge_date = datetime.now()
    adm.settled = True
    # 释放床位
    bed_result = await db.execute(select(Bed).where(Bed.id == adm.bed_id))
    bed = bed_result.scalar_one_or_none()
    if bed:
        bed.status = BedStatus.AVAILABLE
    await db.commit()
    return {
        "message": "出院结算完成",
        "total_fee": total,
        "deposit": adm.deposit,
        "balance": adm.deposit - total,
    }


@admission_router.get("/{adm_id}/daily-bill")
async def daily_bill(
    adm_id: int,
    bill_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """模块8: 一日清单查询。"""
    q = select(AdmissionFeeItem).where(AdmissionFeeItem.admission_id == adm_id)
    if bill_date:
        q = q.where(AdmissionFeeItem.fee_date == bill_date)
    result = await db.execute(q)
    items = result.scalars().all()
    total = sum(i.amount for i in items)
    return {
        "items": [
            {
                "category": i.category,
                "item_name": i.item_name,
                "quantity": i.quantity,
                "amount": i.amount,
            }
            for i in items
        ],
        "total": total,
    }


# ══════════════════════════════════════════════════════════════
# 模块 8: 护士工作站 / 床位管理
# ══════════════════════════════════════════════════════════════

nurse_router = APIRouter(prefix="/api/nurse", tags=["护士工作站"])


@nurse_router.get("/beds", response_model=List[schemas.BedOut])
async def list_beds(
    department_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Bed)
    if department_id:
        q = q.where(Bed.department_id == department_id)
    if status:
        q = q.where(Bed.status == status)
    result = await db.execute(q)
    return result.scalars().all()


# ══════════════════════════════════════════════════════════════
# 医嘱管理（模块 8/10/11/12/13）
# ══════════════════════════════════════════════════════════════

order_router = APIRouter(prefix="/api/orders", tags=["医嘱管理"])


@order_router.get("", response_model=dict)
async def list_orders(
    q: Optional[str] = None,
    patient_name: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(MedicalOrder).options(
        selectinload(MedicalOrder.admission).selectinload(Admission.patient),
        selectinload(MedicalOrder.admission).selectinload(Admission.bed),
        selectinload(MedicalOrder.admission).selectinload(Admission.department),
        selectinload(MedicalOrder.doctor),
        selectinload(MedicalOrder.nurse),
    )

    if q:
        query = query.where(MedicalOrder.id.ilike(f"%{q}%"))

    if patient_name:
        query = query.join(Admission).join(Patient).where(Patient.name.ilike(f"%{patient_name}%"))

    if status:
        query = query.where(MedicalOrder.status == status)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    # 转换为前端需要的字段格式
    formatted_orders = []
    for order in orders:
        formatted_orders.append(
            {
                "order_id": str(order.id),
                "admission_no": order.admission.admission_no if order.admission else "",
                "patient_name": (
                    order.admission.patient.name
                    if order.admission is not None and order.admission.patient is not None
                    else ""
                ),
                "ward_name": (
                    order.admission.department.name
                    if order.admission and order.admission.department
                    else "未知"
                ),
                "bed_no": (
                    order.admission.bed.bed_no if order.admission and order.admission.bed else ""
                ),
                "doctor_name": order.doctor.name if order.doctor else "",
                "order_time": order.created_at.isoformat() if order.created_at else "",
                "dispense_time": order.executed_at.isoformat() if order.executed_at else "",
                "dispenser_name": order.nurse.name if order.nurse else "",
                "drug_count": 1,  # 简化处理
                "status": order.status,
                "drug_items": [
                    {
                        "drug_name": order.content,
                        "drug_spec": "通用",
                        "dosage": "1",
                        "dosage_unit": "片",
                        "usage": "口服",
                        "frequency": "每日三次",
                        "quantity": 3,
                    }
                ],
            }
        )

    return {"items": formatted_orders, "total": total, "page": page, "page_size": page_size}


@order_router.get("/{order_id}", response_model=dict)
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = (
        select(MedicalOrder)
        .options(
            selectinload(MedicalOrder.admission).selectinload(Admission.patient),
            selectinload(MedicalOrder.admission).selectinload(Admission.bed),
            selectinload(MedicalOrder.admission).selectinload(Admission.department),
            selectinload(MedicalOrder.doctor),
            selectinload(MedicalOrder.nurse),
        )
        .where(MedicalOrder.id == order_id)
    )

    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "医嘱不存在")

    return {
        "order_id": str(order.id),
        "admission_no": order.admission.admission_no if order.admission else "",
        "patient_name": (
            order.admission.patient.name if order.admission and order.admission.patient else ""
        ),
        "ward_name": (
            order.admission.department.name
            if order.admission and order.admission.department
            else "未知"
        ),
        "bed_no": order.admission.bed.bed_no if order.admission and order.admission.bed else "",
        "doctor_name": order.doctor.name if order.doctor else "",
        "order_time": order.created_at.isoformat() if order.created_at else "",
        "dispense_time": order.executed_at.isoformat() if order.executed_at else "",
        "dispenser_name": order.nurse.name if order.nurse else "",
        "drug_count": 1,
        "status": order.status,
        "drug_items": [
            {
                "drug_name": order.content,
                "drug_spec": "通用",
                "dosage": "1",
                "dosage_unit": "片",
                "usage": "口服",
                "frequency": "每日三次",
                "quantity": 3,
            }
        ],
    }


@order_router.post("", response_model=schemas.MedicalOrderOut)
async def create_order(
    body: schemas.MedicalOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "doctor")),
):
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == current_user.id))
    doctor = doctor_result.scalar_one_or_none()
    doctor_id = doctor.id if doctor else 1

    order = MedicalOrder(
        admission_id=body.admission_id,
        order_type=body.order_type,
        content=body.content,
        doctor_id=doctor_id,
        status=OrderStatus.PENDING_DISPENSE,  # 修改默认状态为"待发药"
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@order_router.patch("/{order_id}/execute")
async def execute_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "nurse", "pharmacist")),
):
    result = await db.execute(select(MedicalOrder).where(MedicalOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "医嘱不存在")
    order.status = OrderStatus.DISPENSED  # 修改状态为"已发药"
    order.executed_at = datetime.now()
    order.nurse_id = current_user.id
    await db.commit()
    return {"message": "发药成功"}


# ══════════════════════════════════════════════════════════════
# 模块 10-12: 检验/手术/功能科室收费
# ══════════════════════════════════════════════════════════════

charge_router = APIRouter(prefix="/api/charges", tags=["特殊科室收费"])


@charge_router.get("/items")
async def list_charge_items(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(ChargeItem).where(ChargeItem.is_active == True)
    if category:
        q = q.where(ChargeItem.category == category)
    result = await db.execute(q)
    return result.scalars().all()


@charge_router.post("/create")
async def create_special_charge(
    order_id: int,
    charge_item_id: int,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "cashier")),
):
    item_result = await db.execute(select(ChargeItem).where(ChargeItem.id == charge_item_id))
    charge_item = item_result.scalar_one_or_none()
    if not charge_item:
        raise HTTPException(404, "收费项目不存在")
    charge = SpecialCharge(
        order_id=order_id,
        charge_item_id=charge_item_id,
        quantity=quantity,
        amount=charge_item.unit_price * quantity,
    )
    db.add(charge)
    await db.commit()
    return {"message": "收费记录已创建", "amount": charge.amount}


# ══════════════════════════════════════════════════════════════
# 模块 14: 院长查询系统
# ══════════════════════════════════════════════════════════════

director_router = APIRouter(prefix="/api/director", tags=["院长查询"])


@director_router.get("/dashboard", response_model=schemas.DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    today = date.today()
    today_regs = await db.execute(
        select(func.count(Registration.id)).where(func.date(Registration.reg_date) == today)
    )
    today_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Registration.reg_fee), 0)).where(
            func.date(Registration.reg_date) == today,
            Registration.payment_status == PaymentStatus.PAID,
        )
    )
    inpatients = await db.execute(
        select(func.count(Admission.id)).where(Admission.settled == False)
    )
    avail_beds = await db.execute(
        select(func.count(Bed.id)).where(Bed.status == BedStatus.AVAILABLE)
    )
    low_stock = await db.execute(
        select(func.count(PharmacyInventory.id)).where(
            PharmacyInventory.stock_qty <= PharmacyInventory.alert_qty
        )
    )
    pending_orders = await db.execute(
        select(func.count(MedicalOrder.id)).where(MedicalOrder.status == "执行中")
    )
    return schemas.DashboardStats(
        today_registrations=today_regs.scalar() or 0,
        today_revenue=today_revenue_result.scalar() or Decimal("0"),
        inpatients=inpatients.scalar() or 0,
        available_beds=avail_beds.scalar() or 0,
        low_stock_drugs=low_stock.scalar() or 0,
        pending_orders=pending_orders.scalar() or 0,
    )


@director_router.get("/revenue-report")
async def revenue_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(
            func.date(Registration.reg_date).label("day"),
            func.count(Registration.id).label("count"),
            func.sum(Registration.reg_fee).label("revenue"),
        )
        .where(
            func.date(Registration.reg_date).between(start_date, end_date),
            Registration.payment_status == PaymentStatus.PAID,
        )
        .group_by(func.date(Registration.reg_date))
        .order_by(func.date(Registration.reg_date))
    )
    return [{"date": str(r.day), "registrations": r.count, "revenue": r.revenue} for r in result]


# ══════════════════════════════════════════════════════════════
# 模块 15: 触摸屏多媒体导诊（IC卡查询 / 药价公开 / 科室介绍）
# ══════════════════════════════════════════════════════════════

kiosk_router = APIRouter(prefix="/api/kiosk", tags=["触摸屏导诊"])


@kiosk_router.get("/query-by-ic")
async def query_by_ic(ic_card: str, db: AsyncSession = Depends(get_db)):
    """IC卡查询患者信息及当日就诊记录。"""
    result = await db.execute(select(Patient).where(Patient.ic_card_no == ic_card))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "未找到该IC卡关联的患者")
    today_regs = await db.execute(
        select(Registration).where(
            Registration.patient_id == patient.id,
            func.date(Registration.visit_date) == date.today(),
        )
    )
    return {
        "patient": {"name": patient.name, "patient_no": patient.patient_no},
        "today_registrations": [
            {"reg_no": r.reg_no, "reg_type": r.reg_type} for r in today_regs.scalars()
        ],
    }


@kiosk_router.get("/drug-prices")
async def drug_prices(q: str = Query(""), db: AsyncSession = Depends(get_db)):
    """药价公开查询（无需登录）。"""
    stmt = select(
        Drug.name, Drug.specification, Drug.unit, Drug.retail_price, Drug.manufacturer
    ).where(Drug.is_active == True)
    if q:
        stmt = stmt.where(Drug.name.contains(q))
    result = await db.execute(stmt.limit(50))
    return [
        {
            "name": r.name,
            "spec": r.specification,
            "unit": r.unit,
            "price": r.retail_price,
            "manufacturer": r.manufacturer,
        }
        for r in result
    ]


@kiosk_router.get("/departments")
async def kiosk_departments(db: AsyncSession = Depends(get_db)):
    """科室介绍（含医生列表）。"""
    result = await db.execute(
        select(Department)
        .options(selectinload(Department.doctors))
        .where(Department.is_active == True)
    )
    departments = result.scalars().all()
    return [
        {
            "name": d.name,
            "description": d.description,
            "doctors": [
                {
                    "name": doc.name,
                    "title": doc.title,
                    "photo": doc.photo_url,
                    "intro": doc.introduction,
                }
                for doc in d.doctors
                if doc.is_active
            ],
        }
        for d in departments
    ]


@kiosk_router.get("/inpatient-daily-bill")
async def inpatient_daily_bill(admission_no: str, db: AsyncSession = Depends(get_db)):
    """住院患者一日清单（触摸屏自助查询）。"""
    result = await db.execute(select(Admission).where(Admission.admission_no == admission_no))
    adm = result.scalar_one_or_none()
    if not adm:
        raise HTTPException(404, "住院记录不存在")
    items_result = await db.execute(
        select(AdmissionFeeItem).where(
            AdmissionFeeItem.admission_id == adm.id, AdmissionFeeItem.fee_date == date.today()
        )
    )
    items = items_result.scalars().all()
    return {
        "admission_no": admission_no,
        "date": str(date.today()),
        "items": [
            {"category": i.category, "item_name": i.item_name, "amount": i.amount} for i in items
        ],
        "total": sum(i.amount for i in items),
    }


# ══════════════════════════════════════════════════════════════
# AI 助手路由
# ══════════════════════════════════════════════════════════════

ai_router = APIRouter(prefix="/api/ai", tags=["AI助手"])


@ai_router.post("/chat", response_model=schemas.AiChatResponse)
async def ai_chat(
    body: schemas.AiChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reply = await chat_with_ai(
        user_message=body.message,
        history=body.history,
        context_type=body.context_type,
    )
    # 保存会话
    session = AiSession(
        user_id=current_user.id,
        context_type=body.context_type,
        context_id=body.context_id,
        messages=json.dumps(
            [
                *body.history,
                {"role": "user", "content": body.message},
                {"role": "assistant", "content": reply},
            ],
            ensure_ascii=False,
        ),
    )
    db.add(session)
    await db.commit()
    return schemas.AiChatResponse(reply=reply, model=settings.DASHSCOPE_MODEL)


@ai_router.post("/summarize-patient/{patient_id}")
async def summarize_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "doctor")),
):
    p = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = p.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "患者不存在")
    summary = await summarize_patient_history(
        {
            "姓名": patient.name,
            "性别": patient.gender,
            "出生日期": str(patient.birth_date),
            "联系电话": patient.phone,
        }
    )
    return {"summary": summary}


@ai_router.post("/drug-interaction")
async def drug_interaction(
    drug_names: List[str],
    _: User = Depends(require_role("admin", "doctor", "pharmacist")),
):
    result = await analyze_drug_interaction(drug_names)
    return {"analysis": result}


@ai_router.get("/director-insight")
async def director_insight(
    report_type: str = Query("收入报表"),
    _: User = Depends(require_role("admin")),
):
    insight = await interpret_report_data(
        report_type, {"note": "请先获取具体报表数据后再调用此接口"}
    )
    return {"insight": insight}


# ── 从 config 补充导入 ────────────────────────────────────────
from config import settings  # noqa: E402 (已在顶部 config 使用)
