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

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import schemas
from ai_service import (
    analyze_drug_interaction,
    asr_transcribe,
    chat_with_ai,
    chat_with_safety,
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
from database import AsyncSessionLocal, get_db
from privacy import mask_patient_dict, mask_pii
from models import (
    Admission,
    AdmissionFeeItem,
    AiSession,
    AuditLog,
    Bed,
    BedStatus,
    ChargeItem,
    Department,
    Doctor,
    Drug,
    DrugTransaction,
    KnowledgeChunk,
    KnowledgeDocument,
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
    VitalSign,
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


@patient_router.post("", response_model=schemas.PatientOut)
async def create_patient(
    body: schemas.PatientCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    patient = Patient(**body.model_dump(), patient_no=_gen_no("P", 6))
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@patient_router.get("", response_model=List[schemas.PatientOut])
async def search_patients(
    q: str = Query(""),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Patient)
    if q:
        stmt = stmt.where(
            Patient.name.contains(q)
            | Patient.patient_no.contains(q)
            | Patient.phone.contains(q)
            | Patient.ic_card_no.contains(q)
        )
    result = await db.execute(stmt.limit(50))
    return result.scalars().all()


@patient_router.get("/{patient_id}", response_model=schemas.PatientOut)
async def get_patient(
    patient_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "患者不存在")
    return p


# 只添加这两个新接口，完全不修改上面的现有代码
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

    for key, value in body.model_dump().items():
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
    patient_no: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # 始终 JOIN Registration → Patient，以便返回患者信息及支持按患者过滤
    # 分别构建计数查询（无 eager load）和数据查询（带 eager load）
    need_join = bool(payment_status or patient_name or patient_no or patient_id)
    base = select(Prescription)
    if need_join:
        base = base.join(
            Registration, Prescription.registration_id == Registration.id, isouter=True
        )
        base = base.join(Patient, Registration.patient_id == Patient.id, isouter=True)

    count_query = base
    if payment_status:
        count_query = count_query.where(Prescription.payment_status == payment_status)
    if patient_name:
        count_query = count_query.where(Patient.name.ilike(f"%{patient_name}%"))
    if patient_no:
        count_query = count_query.where(Patient.patient_no.ilike(f"%{patient_no}%"))
    if patient_id:
        count_query = count_query.where(Registration.patient_id == patient_id)

    total = await db.scalar(select(func.count()).select_from(count_query.subquery()))

    data_query = (
        select(Prescription)
        .options(
            selectinload(Prescription.items),
            selectinload(Prescription.registration).selectinload(Registration.patient),
        )
        .join(Registration, Prescription.registration_id == Registration.id, isouter=True)
        .join(Patient, Registration.patient_id == Patient.id, isouter=True)
    )
    if payment_status:
        data_query = data_query.where(Prescription.payment_status == payment_status)
    if patient_name:
        data_query = data_query.where(Patient.name.ilike(f"%{patient_name}%"))
    if patient_no:
        data_query = data_query.where(Patient.patient_no.ilike(f"%{patient_no}%"))
    if patient_id:
        data_query = data_query.where(Registration.patient_id == patient_id)

    query = data_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    prescriptions = result.scalars().all()

    def _fmt_pres(pres: Prescription) -> dict:
        patient: Optional[Patient] = (
            pres.registration.patient if pres.registration and pres.registration.patient else None
        )
        return {
            "id": pres.id,
            "pres_no": pres.pres_no,
            "registration_id": pres.registration_id,
            "pres_type": pres.pres_type,
            "diagnosis": pres.diagnosis,
            "total_amount": float(pres.total_amount or 0),
            "payment_status": pres.payment_status,
            "dispensed": pres.dispensed,
            "created_at": pres.created_at.isoformat() if pres.created_at else None,
            "updated_at": getattr(pres, "updated_at", None),
            "paid_at": getattr(pres, "paid_at", None),
            # 患者信息（供收费模块展示）
            "patient": (
                {
                    "id": patient.id if patient else None,
                    "name": patient.name if patient else None,
                    "patient_no": patient.patient_no if patient else None,
                    "gender": patient.gender if patient else None,
                    "age": None,
                }
                if patient
                else None
            ),
            # 顶层快捷字段（与 patient 对象冗余，方便前端直接取用）
            "patient_name": patient.name if patient else None,
            "patient_no": patient.patient_no if patient else None,
            "gender": patient.gender if patient else None,
            "age": None,
        }

    return {
        "items": [_fmt_pres(p) for p in prescriptions],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


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


@pres_router.get("/pending-dispense")
async def pending_dispense(
    db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "pharmacist"))
):
    """模块5: 药房发药窗口 — 获取已付款待发药处方列表（含患者信息）。"""
    result = await db.execute(
        select(Prescription)
        .options(
            selectinload(Prescription.items).selectinload(PrescriptionItem.drug),
            selectinload(Prescription.registration).selectinload(Registration.patient),
        )
        .where(Prescription.payment_status == PaymentStatus.PAID, Prescription.dispensed == False)
        .order_by(Prescription.created_at)
    )
    prescriptions = result.scalars().all()
    return [
        {
            "id": p.id,
            "pres_no": p.pres_no,
            "pres_type": p.pres_type,
            "diagnosis": p.diagnosis,
            "total_amount": float(p.total_amount or 0),
            "payment_status": p.payment_status,
            "dispensed": p.dispensed,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "type": "prescription",
            # 患者信息
            "patient_name": (
                p.registration.patient.name if p.registration and p.registration.patient else None
            ),
            "patient_no": (
                p.registration.patient.patient_no
                if p.registration and p.registration.patient
                else None
            ),
            "gender": (
                p.registration.patient.gender if p.registration and p.registration.patient else None
            ),
            # 药品明细
            "drug_items": [
                {
                    "drug_name": item.drug.name if item.drug else f"药品#{item.drug_id}",
                    "specification": item.drug.specification if item.drug else "",
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "unit_price": float(item.unit_price),
                    "amount": float(item.amount),
                }
                for item in (p.items or [])
            ],
        }
        for p in prescriptions
    ]


@pres_router.patch("/{pres_id}/dispense")
async def dispense_prescription(
    pres_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pharmacist")),
):
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.items))
        .where(Prescription.id == pres_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        raise HTTPException(404, "处方不存在")
    if pres.dispensed:
        raise HTTPException(400, "处方已发药，不可重复发药")

    # 库存校验与扣减
    for item in pres.items:
        inv = await db.execute(
            select(PharmacyInventory).where(PharmacyInventory.drug_id == item.drug_id)
        )
        inv_obj = inv.scalar_one_or_none()
        if not inv_obj or inv_obj.stock_qty < item.quantity:
            drug_name = item.drug.name if item.drug else f"药品#{item.drug_id}"
            current_stock = float(inv_obj.stock_qty) if inv_obj else 0
            raise HTTPException(
                400,
                f"「{drug_name}」药房库存不足（当前: {current_stock}，需要: {item.quantity}），请先调拨补货",
            )
    # 全部校验通过后统一扣减
    for item in pres.items:
        inv = await db.execute(
            select(PharmacyInventory).where(PharmacyInventory.drug_id == item.drug_id)
        )
        inv_obj = inv.scalar_one_or_none()
        if inv_obj:
            inv_obj.stock_qty -= item.quantity
        db.add(
            DrugTransaction(
                drug_id=item.drug_id,
                trans_type="发药出库",
                quantity=-item.quantity,
                source="处方发药",
                source_id=pres.id,
                operator_id=current_user.id,
            )
        )

    pres.dispensed = True
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
            "drug_id": r.drug_id,
            "drug": {
                "id": r.drug.id if r.drug else None,
                "name": r.drug.name if r.drug else "未知",
                "drug_code": r.drug.drug_code if r.drug else "",
                "drug_type": r.drug.drug_type if r.drug else "",
                "specification": r.drug.specification if r.drug else "",
                "unit": r.drug.unit if r.drug else "",
                "retail_price": float(r.drug.retail_price) if r.drug and r.drug.retail_price else 0,
                "purchase_price": (
                    float(r.drug.purchase_price) if r.drug and r.drug.purchase_price else 0
                ),
                "manufacturer": r.drug.manufacturer if r.drug else "",
            },
            "stock_qty": r.stock_qty,
            "warehouse_type": r.warehouse_type,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
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


@warehouse_router.post("/transfer")
async def transfer_to_pharmacy(
    drug_id: int,
    quantity: Decimal,
    warehouse_type: str,
    pharmacy_type: str = "门诊",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pharmacist")),
):
    """药库 → 药房调拨：扣除药库库存，增加药房库存，记录双方流水。"""
    if quantity <= 0:
        raise HTTPException(400, "调拨数量必须大于0")

    # 校验药库库存
    wh_result = await db.execute(
        select(WarehouseInventory).where(
            WarehouseInventory.drug_id == drug_id,
            WarehouseInventory.warehouse_type == warehouse_type,
        )
    )
    wh_inv = wh_result.scalar_one_or_none()
    if not wh_inv or wh_inv.stock_qty < quantity:
        raise HTTPException(
            400,
            f"药库库存不足（当前: {float(wh_inv.stock_qty) if wh_inv else 0}，需要: {quantity}）",
        )

    # 校验药品存在
    drug_result = await db.execute(select(Drug).where(Drug.id == drug_id))
    drug = drug_result.scalar_one_or_none()
    if not drug:
        raise HTTPException(404, "药品不存在")

    # 扣除药库库存
    wh_inv.stock_qty -= quantity

    # 增加药房库存
    ph_result = await db.execute(
        select(PharmacyInventory).where(PharmacyInventory.drug_id == drug_id)
    )
    ph_inv = ph_result.scalar_one_or_none()
    if ph_inv:
        ph_inv.stock_qty += quantity
    else:
        db.add(
            PharmacyInventory(
                drug_id=drug_id,
                stock_qty=quantity,
                pharmacy_type=pharmacy_type,
            )
        )

    # 记录两条流水
    db.add(
        DrugTransaction(
            drug_id=drug_id,
            trans_type="调拨出库",
            quantity=-quantity,
            source="药库→药房",
            source_id=wh_inv.id,
            operator_id=current_user.id,
        )
    )
    db.add(
        DrugTransaction(
            drug_id=drug_id,
            trans_type="调拨入库",
            quantity=quantity,
            source="药库→药房",
            operator_id=current_user.id,
        )
    )

    await db.commit()
    return {
        "message": f"调拨成功：{drug.name} × {quantity} 从 {warehouse_type} 调拨至 {pharmacy_type}"
    }


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
# 公共接口（科室列表等）
# ══════════════════════════════════════════════════════════════

kiosk_router = APIRouter(prefix="/api/kiosk", tags=["公共接口"])


@kiosk_router.get("/departments")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取科室列表（含医生信息）。"""
    result = await db.execute(select(Department).options(selectinload(Department.doctors)))
    departments = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "doctors": [
                {"id": doc.id, "name": doc.name, "title": doc.title} for doc in (d.doctors or [])
            ],
        }
        for d in departments
    ]


# ══════════════════════════════════════════════════════════════
# 模块 7: 出入院管理
# ══════════════════════════════════════════════════════════════

admission_router = APIRouter(prefix="/api/admissions", tags=["出入院管理"])


@admission_router.get("", response_model=dict)
async def list_admissions(
    q: Optional[str] = Query(None),
    settled: Optional[bool] = Query(None),
    patient_name: Optional[str] = Query(None),
    patient_no: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取入院记录列表。
    settled=False 返回在院未结算；settled=True 返回已出院结算。
    支持按住院号/患者姓名/患者编号模糊搜索。
    """
    # 分别构建计数查询（无 eager load）和数据查询（带 eager load）
    count_query = select(Admission).join(Patient, Admission.patient_id == Patient.id, isouter=True)

    if q:
        count_query = count_query.where(Admission.admission_no.ilike(f"%{q}%"))
    if settled is not None:
        count_query = count_query.where(Admission.settled == settled)
    if patient_name:
        count_query = count_query.where(Patient.name.ilike(f"%{patient_name}%"))
    if patient_no:
        count_query = count_query.where(Patient.patient_no.ilike(f"%{patient_no}%"))
    if patient_id:
        count_query = count_query.where(Admission.patient_id == patient_id)

    total = await db.scalar(select(func.count()).select_from(count_query.subquery()))

    data_query = (
        select(Admission)
        .options(selectinload(Admission.patient))
        .join(Patient, Admission.patient_id == Patient.id, isouter=True)
    )

    if q:
        data_query = data_query.where(Admission.admission_no.ilike(f"%{q}%"))
    if settled is not None:
        data_query = data_query.where(Admission.settled == settled)
    if patient_name:
        data_query = data_query.where(Patient.name.ilike(f"%{patient_name}%"))
    if patient_no:
        data_query = data_query.where(Patient.patient_no.ilike(f"%{patient_no}%"))
    if patient_id:
        data_query = data_query.where(Admission.patient_id == patient_id)

    data_query = data_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(data_query)
    admissions = result.scalars().all()

    def _fmt_adm(adm: Admission) -> dict:
        patient: Optional[Patient] = getattr(adm, "patient", None)
        return {
            "id": adm.id,
            "admission_no": adm.admission_no,
            "patient_id": adm.patient_id,
            "bed_id": adm.bed_id,
            "department_id": adm.department_id,
            "deposit": float(adm.deposit or 0),
            "total_fee": float(getattr(adm, "total_fee", None) or 0),
            "diagnosis": adm.diagnosis,
            "admit_date": adm.admit_date,
            "discharge_date": adm.discharge_date,
            "settled": adm.settled,
            # 嵌套患者对象（前端 row.patient.xxx）
            "patient": (
                {
                    "id": patient.id if patient else None,
                    "name": patient.name if patient else None,
                    "patient_no": patient.patient_no if patient else None,
                    "gender": patient.gender if patient else None,
                    "age": None,
                }
                if patient
                else None
            ),
            # 顶层快捷字段（前端 row.patient_name 等直接取用）
            "patient_name": patient.name if patient else None,
            "patient_no": patient.patient_no if patient else None,
            "gender": patient.gender if patient else None,
            "age": None,
        }

    return {
        "items": [_fmt_adm(a) for a in admissions],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


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


@nurse_router.get("/beds")
async def list_beds(
    department_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """床位列表，占用床位附带患者姓名和住院号。"""
    q = select(Bed)
    if department_id:
        q = q.where(Bed.department_id == department_id)
    if status:
        q = q.where(Bed.status == status)
    result = await db.execute(q)
    beds = result.scalars().all()

    # 对占用床位补充患者信息
    occupied_bed_ids = [b.id for b in beds if b.status == BedStatus.OCCUPIED]
    bed_patient_map = {}
    if occupied_bed_ids:
        adm_result = await db.execute(
            select(Admission.bed_id, Patient.name, Admission.admission_no)
            .join(Patient, Admission.patient_id == Patient.id)
            .where(
                Admission.bed_id.in_(occupied_bed_ids),
                Admission.settled == False,
            )
        )
        for row in adm_result:
            bed_patient_map[row.bed_id] = {
                "patient_name": row.name,
                "admission_no": row.admission_no,
            }

    return [
        {
            "id": b.id,
            "bed_no": b.bed_no,
            "ward": b.ward,
            "room_no": b.ward,
            "department_id": b.department_id,
            "status": b.status,
            **bed_patient_map.get(b.id, {}),
        }
        for b in beds
    ]


# ──────────────────────────────────────────────────────────────
# 护士工作站 — 医嘱列表（供 Nurse.vue /api/nurse/orders 调用）
# ──────────────────────────────────────────────────────────────


@nurse_router.get("/inpatients", response_model=dict)
async def nurse_list_inpatients(
    department_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """护士工作站 — 在院患者列表（JOIN 患者表返回姓名/性别/年龄）。"""
    query = (
        select(Admission)
        .options(selectinload(Admission.patient), selectinload(Admission.bed))
        .join(Patient, Admission.patient_id == Patient.id, isouter=True)
        .where(Admission.settled == False)
    )
    if department_id:
        query = query.where(Admission.department_id == department_id)
    if q:
        query = query.where(Patient.name.ilike(f"%{q}%") | Admission.admission_no.ilike(f"%{q}%"))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    admissions = result.scalars().all()

    items = []
    for adm in admissions:
        p: Optional[Patient] = getattr(adm, "patient", None)
        bed = getattr(adm, "bed", None)
        items.append(
            {
                "id": adm.id,
                "admission_no": adm.admission_no,
                "patient_id": adm.patient_id,
                "name": p.name if p else None,
                "gender": p.gender if p else None,
                "age": None,
                "bed_no": bed.bed_no if bed else None,
                "department_id": adm.department_id,
                "admit_date": adm.admit_date,
                "diagnosis": adm.diagnosis,
            }
        )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@nurse_router.get("/orders", response_model=dict)
async def nurse_list_orders(
    patient_id: Optional[int] = Query(None),
    order_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """护士工作站 — 医嘱列表，支持按患者、类型、状态过滤。"""
    query = select(MedicalOrder).options(
        selectinload(MedicalOrder.doctor),
        selectinload(MedicalOrder.nurse),
        selectinload(MedicalOrder.admission).selectinload(Admission.patient),
    )
    if patient_id:
        # MedicalOrder → Admission → Patient
        query = query.join(
            Admission, MedicalOrder.admission_id == Admission.id, isouter=True
        ).where(Admission.patient_id == patient_id)
    if order_type:
        query = query.where(MedicalOrder.order_type == order_type)
    if status:
        query = query.where(MedicalOrder.status == status)

    query = query.order_by(MedicalOrder.created_at.desc())
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    orders = result.scalars().all()

    def _fmt_order(o: MedicalOrder) -> dict:
        adm = o.admission
        p: Optional[Patient] = adm.patient if adm else None
        return {
            "id": o.id,
            "patient_id": adm.patient_id if adm else None,
            "admission_id": o.admission_id,
            "order_type": o.order_type,
            "content": o.content,
            "dosage": getattr(o, "dosage", None),
            "frequency": getattr(o, "frequency", None),
            "route": getattr(o, "route", None),
            "status": o.status,
            "doctor_name": o.doctor.name if o.doctor else None,
            "nurse_name": o.nurse.name if o.nurse else None,
            "created_at": o.created_at,
            "executed_at": getattr(o, "executed_at", None),
        }

    return {
        "items": [_fmt_order(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# 医嘱状态流转合法路径：
#   pending → dispensing（护士执行）
#   dispensing → dispensed（药房/护士确认发药）
#   dispensed → completed（护士确认用药完成）
#   pending/dispensing/dispensed → cancelled（取消）
# 替换原来的 _NURSE_ORDER_TRANSITIONS 和 _NURSE_CANCELLABLE
_NURSE_ORDER_TRANSITIONS: dict[str, tuple[OrderStatus, OrderStatus]] = {
    "execute": (OrderStatus.PENDING_DISPENSE, OrderStatus.ACTIVE),
    "dispense": (OrderStatus.ACTIVE, OrderStatus.DISPENSED),
    "complete": (OrderStatus.DISPENSED, OrderStatus.COMPLETED),
}
# 允许取消的状态：待发药、执行中、已发药
_NURSE_CANCELLABLE = {OrderStatus.PENDING_DISPENSE, OrderStatus.ACTIVE, OrderStatus.DISPENSED}


async def _nurse_get_order(order_id: int, db: AsyncSession) -> MedicalOrder:
    result = await db.execute(select(MedicalOrder).where(MedicalOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "医嘱不存在")
    return order


async def _nurse_transition(
    order_id: int, action: str, db: AsyncSession, current_user: User
) -> dict:
    order = await _nurse_get_order(order_id, db)

    if action == "cancel":
        if order.status not in {s.value for s in _NURSE_CANCELLABLE}:
            raise HTTPException(400, f"当前状态「{order.status}」不允许取消")
        order.status = OrderStatus.CANCELLED.value
        await db.commit()
        return {"message": "医嘱已取消", "status": order.status}

    if action not in _NURSE_ORDER_TRANSITIONS:
        raise HTTPException(400, f"未知操作：{action}")

    required_enum, target_enum = _NURSE_ORDER_TRANSITIONS[action]
    # 数据库里存的是枚举的value（字符串），所以比较时用.value
    if order.status != required_enum.value:
        raise HTTPException(
            400,
            f"当前状态「{order.status}」不允许执行「{action}」（需要状态「{required_enum.value}」）",
        )
    order.status = target_enum.value
    if action == "execute":
        order.executed_at = datetime.now()
        order.nurse_id = current_user.id
    await db.commit()
    labels = {
        "execute": "医嘱已执行，进入执行中状态",
        "dispense": "发药确认成功，状态更新为已发药",
        "complete": "医嘱已完成",
    }
    return {"message": labels[action], "status": order.status}


@nurse_router.patch("/orders/{order_id}/execute")
async def nurse_execute_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "nurse", "pharmacist")),
):
    """pending → dispensing：护士执行医嘱，进入发药流程。"""
    return await _nurse_transition(order_id, "execute", db, current_user)


@nurse_router.patch("/orders/{order_id}/dispense")
async def nurse_dispense_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "nurse", "pharmacist")),
):
    """dispensing → dispensed：确认发药完成。"""
    return await _nurse_transition(order_id, "dispense", db, current_user)


@nurse_router.patch("/orders/{order_id}/complete")
async def nurse_complete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "nurse")),
):
    """dispensed → completed：护士确认患者已用药，医嘱完成。"""
    return await _nurse_transition(order_id, "complete", db, current_user)


@nurse_router.patch("/orders/{order_id}/cancel")
async def nurse_cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "nurse", "pharmacist")),
):
    """pending/dispensing/dispensed → cancelled：取消医嘱。"""
    return await _nurse_transition(order_id, "cancel", db, current_user)


# ──────────────────────────────────────────────────────────────
# 护士工作站 — 生命体征记录
# ──────────────────────────────────────────────────────────────


@nurse_router.get("/vitals", response_model=dict)
async def nurse_list_vitals(
    patient_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """获取生命体征记录列表。"""
    query = select(VitalSign).options(selectinload(VitalSign.recorder))
    if patient_id:
        query = query.where(VitalSign.patient_id == patient_id)
    query = query.order_by(VitalSign.record_time.desc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    vitals = result.scalars().all()

    return {
        "items": [
            {
                "id": v.id,
                "patient_id": v.patient_id,
                "temperature": float(v.temperature) if v.temperature else None,
                "pulse": v.pulse,
                "respiration": v.respiration,
                "systolic_bp": v.systolic_bp,
                "diastolic_bp": v.diastolic_bp,
                "record_time": v.record_time.isoformat() if v.record_time else None,
                "recorder_name": v.recorder.real_name if v.recorder else None,
            }
            for v in vitals
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@nurse_router.post("/vitals")
async def nurse_create_vital(
    body: schemas.VitalSignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "nurse")),
):
    """录入生命体征。"""
    record_time = datetime.now()
    if body.record_time:
        try:
            record_time = datetime.strptime(body.record_time, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            pass

    vital = VitalSign(
        patient_id=body.patient_id,
        temperature=body.temperature,
        pulse=body.pulse,
        respiration=body.respiration,
        systolic_bp=body.systolic_bp,
        diastolic_bp=body.diastolic_bp,
        record_time=record_time,
        recorder_id=current_user.id,
    )
    db.add(vital)
    await db.commit()
    await db.refresh(vital)
    return {"message": "生命体征录入成功", "id": vital.id}


# ══════════════════════════════════════════════════════════════
# 医嘱管理（模块 8/10/11/12/13）
# ══════════════════════════════════════════════════════════════

order_router = APIRouter(prefix="/api/orders", tags=["医嘱管理"])


@order_router.get("", response_model=dict)
async def list_orders(
    q: Optional[str] = None,
    patient_name: Optional[str] = None,
    admission_no: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # 先构建基础 query（不 join，eager load 用 selectinload 独立查询）
    query = select(MedicalOrder).options(
        selectinload(MedicalOrder.admission).selectinload(Admission.patient),
        selectinload(MedicalOrder.admission).selectinload(Admission.bed),
        selectinload(MedicalOrder.admission).selectinload(Admission.department),
        selectinload(MedicalOrder.doctor),
        selectinload(MedicalOrder.nurse),
    )

    # 收集哪些条件需要 join Admission / Patient
    need_join_admission = bool(q or admission_no or patient_name)
    need_join_patient = bool(patient_name)

    if need_join_admission:
        query = query.join(Admission, MedicalOrder.admission_id == Admission.id, isouter=True)
    if need_join_patient:
        query = query.join(Patient, Admission.patient_id == Patient.id, isouter=True)

    # 按条件过滤
    if q:
        query = query.where(Admission.admission_no.ilike(f"%{q}%"))
    if admission_no:
        query = query.where(Admission.admission_no.ilike(f"%{admission_no}%"))
    if patient_name:
        query = query.where(Patient.name.ilike(f"%{patient_name}%"))
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
    """旧版兼容接口：执行医嘱（待发药 → 执行中）。
    新代码请优先使用 /api/nurse/orders/{id}/execute 系列接口。
    """
    result = await db.execute(select(MedicalOrder).where(MedicalOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "医嘱不存在")
    # 只允许从「待发药」状态执行
    if order.status != OrderStatus.PENDING_DISPENSE.value:
        raise HTTPException(400, f"当前状态「{order.status}」不允许执行此操作")
    # 更新为「执行中」状态
    order.status = OrderStatus.ACTIVE.value
    order.executed_at = datetime.now()
    order.nurse_id = current_user.id
    await db.commit()
    return {"message": "医嘱已执行，进入执行中状态"}


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


@director_router.get("/department-stats")
async def department_stats(
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """科室挂号量统计，按日期范围筛选，默认最近30天。"""
    if not start_date:
        from datetime import timedelta

        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    result = await db.execute(
        select(
            Department.id,
            Department.name,
            func.count(Registration.id).label("reg_count"),
            func.sum(Registration.reg_fee).label("total_fee"),
        )
        .select_from(Department)
        .outerjoin(Doctor, Doctor.department_id == Department.id)
        .outerjoin(Registration, Registration.doctor_id == Doctor.id)
        .where(
            func.date(Registration.reg_date).between(start_date, end_date),
            Registration.payment_status == PaymentStatus.PAID,
        )
        .group_by(Department.id, Department.name)
        .order_by(func.count(Registration.id).desc())
    )
    return [
        {"dept_name": r.name, "reg_count": r.reg_count, "total_fee": float(r.total_fee or 0)}
        for r in result
    ]


# ══════════════════════════════════════════════════════════════
# AI 助手路由
# ══════════════════════════════════════════════════════════════

ai_router = APIRouter(prefix="/api/ai", tags=["AI助手"])


# ── 后台任务：AI 生成会话标题 ──────────────────────────────


async def background_generate_title(session_id: int, user_message: str) -> None:
    """在返回响应后异步生成会话标题，不阻塞用户。"""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AiSession).where(AiSession.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                return

            title_text = await chat_with_ai(
                f"用2到5个字概括以下用户问题的核心主题，只输出概括、不要解释、不要标点：\n{user_message}",
                context_type="general",
            )
            title = title_text.strip().strip("\"'`（）()[]【】").replace("\n", " ").strip()[:25]
            if title:
                session.title = title
            await db.commit()
    except Exception:
        logger.exception("AI 生成标题失败")


@ai_router.post("/chat", response_model=schemas.AiChatResponse)
async def ai_chat(
    body: schemas.AiChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── 加载或创建会话 ──
    if body.session_id:
        result = await db.execute(
            select(AiSession).where(
                AiSession.id == body.session_id,
                AiSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(404, "会话不存在")
        history = json.loads(session.messages) if session.messages else []
        is_new_session = False
    else:
        session = AiSession(
            user_id=current_user.id,
            context_type=body.context_type,
            context_id=body.context_id,
            messages=json.dumps(body.history or [], ensure_ascii=False),
        )
        db.add(session)
        history = body.history or []
        is_new_session = True

    # ── 调用 AI ──
    reply, rejected = await chat_with_safety(
        user_message=body.message,
        history=history,
        context_type=body.context_type,
        current_user={
            "id": current_user.id,
            "role": current_user.role,
            "name": current_user.real_name,
        },
    )
    reply = mask_pii(reply, current_user.role)

    # ── 更新消息（带时间戳） ──
    now_iso = datetime.now().isoformat()
    current_messages = json.loads(session.messages) if session.messages else []
    current_messages.append({"role": "user", "content": body.message, "time": now_iso})
    current_messages.append({"role": "assistant", "content": reply, "time": now_iso})
    session.messages = json.dumps(current_messages, ensure_ascii=False)

    # ── 标题（异步生成，不拖慢响应） ──
    if is_new_session and not session.title:
        session.title = body.message[:20]  # 先临时占位
        background_tasks.add_task(background_generate_title, session.id, body.message)

    session.updated_at = datetime.now()

    # ── 审计日志 ──
    db.add(
        AuditLog(
            user_id=current_user.id,
            action_type="ai_chat",
            target_type=body.context_type,
            target_id=body.context_id,
            detail=json.dumps(
                {"session_id": session.id, "message_len": len(body.message), "rejected": rejected},
                ensure_ascii=False,
            ),
        )
    )

    await db.commit()
    return schemas.AiChatResponse(
        reply=reply,
        model=settings.DASHSCOPE_MODEL,
        rejected=rejected,
        session_id=session.id,
    )


# ── 会话管理 ─────────────────────────────────────────────────


@ai_router.get("/sessions", response_model=List[schemas.AiSessionOut])
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户的所有会话（按更新时间倒序，分页）"""
    # 总数
    count_q = (
        select(func.count()).select_from(AiSession).where(AiSession.user_id == current_user.id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    # 分页查询
    result = await db.execute(
        select(AiSession)
        .where(AiSession.user_id == current_user.id)
        .order_by(AiSession.updated_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        msg_list = json.loads(s.messages) if s.messages else []
        out.append(
            {
                "id": s.id,
                "title": s.title,
                "context_type": s.context_type,
                "message_count": len(msg_list),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
        )
    return out


@ai_router.get("/sessions/{session_id}", response_model=schemas.AiSessionDetailOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定会话的完整消息"""
    result = await db.execute(
        select(AiSession).where(
            AiSession.id == session_id,
            AiSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "会话不存在")

    messages_list = json.loads(session.messages) if session.messages else []
    return {
        "id": session.id,
        "title": session.title,
        "messages": messages_list,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@ai_router.put("/sessions/{session_id}")
async def rename_session(
    session_id: int,
    body: schemas.SessionRenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重命名会话标题"""
    result = await db.execute(
        select(AiSession).where(
            AiSession.id == session_id,
            AiSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "会话不存在")
    session.title = body.title
    session.updated_at = datetime.now()
    await db.commit()
    return {"message": "ok"}


@ai_router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除单个会话"""
    result = await db.execute(
        select(AiSession).where(
            AiSession.id == session_id,
            AiSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "会话不存在")
    await db.delete(session)
    await db.commit()
    return {"message": "ok"}


@ai_router.post("/sessions/batch-delete")
async def batch_delete_sessions(
    body: schemas.BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除会话"""
    if not body.ids:
        raise HTTPException(400, "ids 不能为空")
    result = await db.execute(
        select(AiSession).where(
            AiSession.id.in_(body.ids),
            AiSession.user_id == current_user.id,
        )
    )
    sessions = result.scalars().all()
    for s in sessions:
        await db.delete(s)
    await db.commit()
    return {"message": f"已删除 {len(sessions)} 个会话"}


@ai_router.post("/summarize-patient/{patient_id}")
async def summarize_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "doctor")),
):
    p = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = p.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "患者不存在")

    raw_data = {
        "姓名": patient.name,
        "性别": patient.gender,
        "出生日期": str(patient.birth_date),
        "联系电话": patient.phone,
    }
    masked_data = mask_patient_dict(raw_data, current_user.role)

    # 记录审计日志
    db.add(
        AuditLog(
            user_id=current_user.id,
            action_type="patient_query",
            target_type="patient",
            target_id=patient_id,
            detail=json.dumps({"action": "summarize_patient"}, ensure_ascii=False),
        )
    )

    summary = await summarize_patient_history(masked_data)
    return {"summary": summary}


@ai_router.post("/drug-interaction")
async def drug_interaction(
    drug_names: List[str],
    _: User = Depends(require_role("admin", "doctor", "pharmacist")),
):
    # 尝试缓存
    from redis_cache import get_cache

    cache = get_cache()
    cache_key_val = ",".join(sorted(drug_names))
    cached = await cache.get_drug_interaction_cache(cache_key_val)
    if cached:
        return {"analysis": cached, "cached": True}

    result = await analyze_drug_interaction(drug_names)
    await cache.set_drug_interaction_cache(cache_key_val, result)
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


@ai_router.post("/triage")
async def ai_triage(
    body: schemas.AiTriageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 智能分诊：根据症状推荐科室、号别、医生"""
    # 获取科室+医生数据
    result = await db.execute(select(Department).options(selectinload(Department.doctors)))
    departments = result.scalars().all()

    dept_info = []
    for d in departments:
        doctors = [
            {"name": doc.name, "title": doc.title} for doc in (d.doctors or []) if doc.is_active
        ]
        dept_info.append({"name": d.name, "doctors": doctors})

    prompt = (
        "你是一个医院智能分诊助手。根据患者症状描述，从以下科室中选择最合适的科室和医生。\n\n"
        f"科室列表：\n{json.dumps(dept_info, ensure_ascii=False, indent=2)}\n\n"
        "挂号类型可选：普通(¥5)、专家(¥20)、急诊(¥15)、专科(¥10)\n\n"
        f"患者症状：{body.symptoms}\n\n"
        "请以JSON格式返回，只输出JSON不要其他文字：\n"
        '{"department":"科室名称","reg_type":"挂号类型","doctor":"医生姓名(职称)或null","reason":"推荐理由"}'
    )

    reply = await chat_with_ai(prompt, context_type="general")
    try:
        # 尝试提取 JSON
        result_json = reply.strip()
        if "```json" in result_json:
            result_json = result_json.split("```json")[1].split("```")[0].strip()
        elif "```" in result_json:
            result_json = result_json.split("```")[1].split("```")[0].strip()
        return json.loads(result_json)
    except (json.JSONDecodeError, ValueError):
        return {"department": None, "reg_type": None, "doctor": None, "reason": reply}


@ai_router.post("/director-query")
async def director_query(
    body: schemas.DirectorQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """自然语言院长查询：用中文问数据"""
    today = date.today()
    from datetime import timedelta

    # ── 1. 收集所有可用的统计数据 ──
    # 今日概况
    regs = (
        await db.execute(
            select(func.count(Registration.id)).where(func.date(Registration.reg_date) == today)
        )
    ).scalar() or 0
    revenue = (
        await db.execute(
            select(func.coalesce(func.sum(Registration.reg_fee), 0)).where(
                func.date(Registration.reg_date) == today,
                Registration.payment_status == PaymentStatus.PAID,
            )
        )
    ).scalar() or 0
    inpatients = (
        await db.execute(select(func.count(Admission.id)).where(Admission.settled == False))
    ).scalar() or 0
    avail_beds = (
        await db.execute(select(func.count(Bed.id)).where(Bed.status == BedStatus.AVAILABLE))
    ).scalar() or 0
    low_stock = (
        await db.execute(
            select(func.count(PharmacyInventory.id)).where(
                PharmacyInventory.stock_qty <= PharmacyInventory.alert_qty
            )
        )
    ).scalar() or 0
    pending = (
        await db.execute(select(func.count(MedicalOrder.id)).where(MedicalOrder.status == "执行中"))
    ).scalar() or 0

    # 近7天收入趋势
    week_ago = today - timedelta(days=6)
    rev_rows = (
        await db.execute(
            select(
                func.date(Registration.reg_date).label("day"),
                func.sum(Registration.reg_fee).label("revenue"),
            )
            .where(
                func.date(Registration.reg_date).between(week_ago, today),
                Registration.payment_status == PaymentStatus.PAID,
            )
            .group_by(func.date(Registration.reg_date))
            .order_by(func.date(Registration.reg_date))
        )
    ).all()
    revenue_trend = [{"date": str(r.day), "revenue": float(r.revenue or 0)} for r in rev_rows]

    # 科室挂号量（近30天）
    month_ago = today - timedelta(days=30)
    dept_rows = (
        await db.execute(
            select(
                Department.name,
                func.count(Registration.id).label("reg_count"),
                func.sum(Registration.reg_fee).label("total_fee"),
            )
            .select_from(Department)
            .outerjoin(Doctor, Doctor.department_id == Department.id)
            .outerjoin(Registration, Registration.doctor_id == Doctor.id)
            .where(
                func.date(Registration.reg_date).between(month_ago, today),
                Registration.payment_status == PaymentStatus.PAID,
            )
            .group_by(Department.name)
            .order_by(func.count(Registration.id).desc())
        )
    ).all()
    dept_stats = [
        {"dept_name": r.name, "reg_count": r.reg_count, "total_fee": float(r.total_fee or 0)}
        for r in dept_rows
    ]

    # ── 2. 组装上下文 ──
    context = {
        "今日概况": {
            "挂号数": regs,
            "收入(元)": float(revenue),
            "在院人数": inpatients,
            "可用床位": avail_beds,
            "库存预警药品数": low_stock,
            "待执行医嘱": pending,
        },
        "近7天收入趋势(元)": revenue_trend,
        "近30天科室挂号量统计": dept_stats,
    }

    # ── 3. AI 分析 ──
    prompt = (
        "你是一位医院管理数据分析助手。根据以下当前数据和用户问题，给出分析回答。\n\n"
        f"【当前运营数据】\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        f"【用户问题】{body.question}\n\n"
        "回答要求：\n"
        "- 以数据为依据，引用具体数值\n"
        "- 简洁专业，用中文\n"
        "- 如果数据不足以回答，如实说明\n"
        "- 可以提出管理建议"
    )
    answer = await chat_with_ai(prompt, context_type="report")

    return {"answer": answer}


@ai_router.post("/check-prescription")
async def check_prescription(
    body: schemas.PrescriptionCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "doctor")),
):
    """AI 处方审核：检查药物相互作用、剂量、重复用药"""
    drugs_detail = []
    for item in body.items:
        result = await db.execute(select(Drug).where(Drug.id == item.drug_id))
        drug = result.scalar_one_or_none()
        if drug:
            drugs_detail.append(
                {
                    "name": drug.name,
                    "specification": drug.specification,
                    "quantity": float(item.quantity),
                    "unit": item.unit or drug.unit,
                }
            )

    if not drugs_detail:
        return {"safe": True, "warnings": [], "summary": "无药品可审核"}

    prompt = (
        "你是一个医院处方审核助手。请审核以下处方是否存在问题。\n\n"
        f"药品明细：\n{json.dumps(drugs_detail, ensure_ascii=False, indent=2)}\n\n"
        "请检查：\n"
        "1. 药物相互作用（药物之间是否有禁忌）\n"
        "2. 剂量是否合理（是否超常规剂量）\n"
        "3. 是否存在重复用药（相同或类似成分的药品）\n"
        "4. 是否有常见禁忌症注意事项\n\n"
        "以JSON格式返回，只输出JSON：\n"
        "{\n"
        '  "safe": true,\n'
        '  "warnings": [{"type":"相互作用|剂量|重复用药|禁忌","severity":"high|medium|low","message":"描述"}],\n'
        '  "summary": "总体评价（一句话）"\n'
        "}"
    )
    reply = await chat_with_ai(prompt, context_type="drug")
    try:
        result_json = reply.strip()
        if "```json" in result_json:
            result_json = result_json.split("```json")[1].split("```")[0].strip()
        elif "```" in result_json:
            result_json = result_json.split("```")[1].split("```")[0].strip()
        parsed = json.loads(result_json)
        return {
            "safe": parsed.get("safe", True),
            "warnings": parsed.get("warnings", []),
            "summary": parsed.get("summary", ""),
        }
    except (json.JSONDecodeError, ValueError):
        return {"safe": True, "warnings": [], "summary": "AI审核暂时无法完成，请手动检查"}


# ── 语音识别 (ASR) ─────────────────────────────────────────────


@ai_router.post("/asr", response_model=schemas.AsrResponse)
async def ai_asr(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """语音识别：接收音频文件，返回识别文本。任意登录用户可用。"""
    print("\n" + "=" * 50)
    print("✅ ASR路由被调用了")
    print(f"✅ 文件名: {file.filename}, 文件大小: {file.size}")

    audio_bytes = await file.read()
    result = await asr_transcribe(audio_bytes, file.filename or "audio.webm")

    print(f"✅ asr_transcribe返回结果: {result}")
    print("=" * 50 + "\n")

    return schemas.AsrResponse(**result)


# ══════════════════════════════════════════════════════════════
# 审计日志路由
# ══════════════════════════════════════════════════════════════

audit_router = APIRouter(prefix="/api/audit-logs", tags=["审计日志"])


@audit_router.get("", response_model=List[schemas.AuditLogOut])
async def list_audit_logs(
    user_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    q = select(AuditLog)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if action_type:
        q = q.where(AuditLog.action_type == action_type)
    if start_date:
        q = q.where(func.date(AuditLog.created_at) >= start_date)
    if end_date:
        q = q.where(func.date(AuditLog.created_at) <= end_date)
    result = await db.execute(
        q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all()


# ══════════════════════════════════════════════════════════════
# 知识库路由
# ══════════════════════════════════════════════════════════════

kb_router = APIRouter(prefix="/api/kb", tags=["知识库"])


@kb_router.post("/upload")
async def kb_upload(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """上传医疗知识文档（管理员专用）"""
    if file.content_type and file.content_type not in (
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        raise HTTPException(400, "仅支持 PDF / TXT / DOCX 格式")

    content_bytes = await file.read()
    if len(content_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件最大 10MB")

    # 延迟导入 rag_service（避免循环导入）
    from rag_service import get_rag_service

    rag = get_rag_service(db)
    doc_id = await rag.upload_document(content_bytes, file.filename, current_user.id)

    # 审计日志
    db.add(
        AuditLog(
            user_id=current_user.id,
            action_type="kb_upload",
            target_type="knowledge_base",
            target_id=doc_id,
            detail=json.dumps({"filename": file.filename}, ensure_ascii=False),
        )
    )
    await db.commit()

    return {"id": doc_id, "filename": file.filename, "message": "文档上传成功，正在后台解析入库"}


@kb_router.get("/search")
async def kb_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """语义检索知识库"""
    from rag_service import get_rag_service

    rag = get_rag_service(db)
    results = await rag.search(q, top_k)

    # 审计日志
    db.add(
        AuditLog(
            user_id=current_user.id,
            action_type="kb_search",
            target_type="knowledge_base",
            detail=json.dumps({"query": q, "result_count": len(results)}, ensure_ascii=False),
        )
    )
    await db.commit()

    return {"results": results}


@kb_router.get("/documents", response_model=List[schemas.KnowledgeDocumentOut])
async def kb_list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(KnowledgeDocument)
        .where(KnowledgeDocument.is_active == True)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    result = await db.execute(q)
    return result.scalars().all()


@kb_router.delete("/documents/{doc_id}")
async def kb_delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    doc.is_active = False
    # 软删除关联块
    await db.execute(
        update(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id).values(content="")
    )
    await db.commit()
    return {"message": "文档已删除"}


@kb_router.post("/cleanup")
async def kb_cleanup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """清理重复和过时内容"""
    from rag_service import get_rag_service

    rag = get_rag_service(db)
    removed = await rag.cleanup_stale()
    return {"removed_count": removed}


# ── 从 config 补充导入 ────────────────────────────────────────
from config import settings  # noqa: E402 (已在顶部 config 使用)
