"""
tools.py — HIS 数据查询工具集（供 LangGraph Agent 调用）

封装 4 个 HIS 数据查询工具：
  1. today_registrations   — 今日挂号统计
  2. drug_inventory        — 药品库存查询（药房+药库）
  3. patient_info          — 患者信息查询（按姓名或病历号）
  4. prescription_info     — 处方信息查询（按处方编号）

所有工具自动校验 admin 权限，结果格式化为自然语言。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from loguru import logger
from sqlalchemy import func, select, or_

from database import AsyncSessionLocal
from models import (
    Drug,
    Patient,
    PharmacyInventory,
    Prescription,
    PrescriptionItem,
    Registration,
    WarehouseInventory,
)


def _fmt_user(user_info: Optional[dict]) -> str:
    """格式化用户信息用于日志。"""
    if not user_info:
        return "anonymous"
    return f"{user_info.get('name', '?')}({user_info.get('role', '?')})"


async def _is_admin(user_info: Optional[dict]) -> bool:
    """检查当前用户是否为 admin 角色。"""
    return bool(user_info and user_info.get("role") == "admin")


# ── Tool 1: 今日挂号统计 ──────────────────────────────────────


async def today_registrations(
    user_info: Optional[dict] = None, **kwargs
) -> str:
    """查询今日挂号患者数量（按挂号类型分类统计）。"""
    logger.info(f"🔧 today_registrations by {_fmt_user(user_info)}")
    if not await _is_admin(user_info):
        return "⚠️ 权限不足：仅管理员可查询今日挂号数据，请联系管理员。"

    async with AsyncSessionLocal() as db:
        today = date.today()

        # 总数
        result = await db.execute(
            select(func.count(Registration.id)).where(
                func.date(Registration.reg_date) == today
            )
        )
        total = result.scalar() or 0

        # 按挂号类型分组
        result = await db.execute(
            select(Registration.reg_type, func.count(Registration.id))
            .where(func.date(Registration.reg_date) == today)
            .group_by(Registration.reg_type)
        )
        by_type = {row[0]: row[1] for row in result.all()}

        # 按支付状态分组
        result = await db.execute(
            select(Registration.payment_status, func.count(Registration.id))
            .where(func.date(Registration.reg_date) == today)
            .group_by(Registration.payment_status)
        )
        by_payment = {row[0]: row[1] for row in result.all()}

    detail = (
        "、".join(f"{t}: {c}人" for t, c in by_type.items())
        if by_type
        else "暂无数据"
    )
    pay_detail = (
        "、".join(f"{s}: {c}人" for s, c in by_payment.items())
        if by_payment
        else "暂无数据"
    )

    return (
        f"📊 今日挂号统计（{today.isoformat()}）\n"
        f"总挂号数：{total} 人\n"
        f"挂号类型分布：{detail}\n"
        f"支付状态分布：{pay_detail}"
    )


# ── Tool 2: 药品库存查询 ──────────────────────────────────────


async def drug_inventory(
    drug_name: str, user_info: Optional[dict] = None, **kwargs
) -> str:
    """根据药品名称查询药房和药库库存。"""
    logger.info(f"🔧 drug_inventory({drug_name}) by {_fmt_user(user_info)}")
    if not await _is_admin(user_info):
        return "⚠️ 权限不足：仅管理员可查询药品库存，请联系管理员。"

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Drug).where(
                or_(
                    Drug.name.ilike(f"%{drug_name}%"),
                    Drug.generic_name.ilike(f"%{drug_name}%"),
                )
            )
        )
        drugs = result.scalars().all()

        if not drugs:
            return f"未找到与「{drug_name}」相关的药品记录。"

        lines = []
        for drug in drugs[:5]:  # 最多返回 5 种药品
            # 药房库存
            result = await db.execute(
                select(PharmacyInventory).where(
                    PharmacyInventory.drug_id == drug.id
                )
            )
            ph_inv = result.scalar_one_or_none()

            # 药库库存
            result = await db.execute(
                select(WarehouseInventory).where(
                    WarehouseInventory.drug_id == drug.id
                )
            )
            wh_inv = result.scalar_one_or_none()

            ph_stock = (
                f"{ph_inv.stock_qty} {drug.unit}" if ph_inv else "无记录"
            )
            wh_stock = (
                f"{wh_inv.stock_qty} {drug.unit}" if wh_inv else "无记录"
            )
            ph_type = ph_inv.pharmacy_type if ph_inv else "-"

            lines.append(
                f"【{drug.name}】{drug.specification or ''}\n"
                f"  类型：{drug.drug_type}  |  零售价：¥{drug.retail_price}/{drug.unit}\n"
                f"  生产商：{drug.manufacturer or '-'}\n"
                f"  药房库存（{ph_type}）：{ph_stock}\n"
                f"  药库库存：{wh_stock}"
            )

    return "📦 药品库存查询结果：\n" + "\n\n".join(lines)


# ── Tool 3: 患者信息查询 ──────────────────────────────────────


async def patient_info(
    query: str, user_info: Optional[dict] = None, **kwargs
) -> str:
    """根据患者姓名或病历号查询患者基本信息。"""
    logger.info(f"🔧 patient_info({query}) by {_fmt_user(user_info)}")
    if not await _is_admin(user_info):
        return "⚠️ 权限不足：仅管理员可查询患者信息，请联系管理员。"

    async with AsyncSessionLocal() as db:
        # 判断是病历号还是姓名
        is_by_no = query.isdigit() and len(query) >= 6
        if is_by_no:
            result = await db.execute(
                select(Patient).where(Patient.patient_no == query)
            )
        else:
            result = await db.execute(
                select(Patient).where(Patient.name.ilike(f"%{query}%"))
            )
        patients = result.scalars().all()

        if not patients:
            return f"未找到与「{query}」匹配的患者记录。"

        # 匹配过多时提示精确搜索
        if len(patients) > 5:
            names = "、".join(p.name for p in patients[:5])
            return (
                f"找到 {len(patients)} 位匹配患者，请提供更精确的姓名或病历号。\n"
                f"部分结果：{names}..."
            )

        lines = []
        for p in patients:
            age = ""
            if p.birth_date:
                age = f"{datetime.now().year - p.birth_date.year} 岁"
            lines.append(
                f"【患者】{p.name} | {p.gender} | {age}\n"
                f"  病历号：{p.patient_no}  |  IC 卡号：{p.ic_card_no or '-'}\n"
                f"  电话：{p.phone or '-'}  |  地址：{p.address or '-'}"
            )

    return "👤 患者信息查询结果：\n" + "\n\n".join(lines)


# ── Tool 4: 处方信息查询 ──────────────────────────────────────


async def prescription_info(
    prescription_id: str, user_info: Optional[dict] = None, **kwargs
) -> str:
    """根据处方编号查询处方详细信息（含药品明细）。"""
    logger.info(
        f"🔧 prescription_info({prescription_id}) by {_fmt_user(user_info)}"
    )
    if not await _is_admin(user_info):
        return "⚠️ 权限不足：仅管理员可查询处方信息，请联系管理员。"

    async with AsyncSessionLocal() as db:
        int_id = int(prescription_id) if prescription_id.isdigit() else -1
        result = await db.execute(
            select(Prescription).where(
                or_(
                    Prescription.pres_no == prescription_id,
                    Prescription.id == int_id,
                )
            )
        )
        pres = result.scalar_one_or_none()
        if not pres:
            return f"未找到编号为「{prescription_id}」的处方。"

        # 患者信息
        reg = await db.get(Registration, pres.registration_id)
        patient = await db.get(Patient, reg.patient_id) if reg else None

        # 处方明细
        result = await db.execute(
            select(PrescriptionItem).where(
                PrescriptionItem.prescription_id == pres.id
            )
        )
        items = result.scalars().all()

        item_lines = []
        for item in items:
            drug = await db.get(Drug, item.drug_id)
            dn = drug.name if drug else f"药品#{item.drug_id}"
            item_lines.append(
                f"  · {dn} × {item.quantity}{item.unit}  "
                f"¥{item.amount}（单价 ¥{item.unit_price}/{item.unit}）"
            )

        items_text = "\n".join(item_lines) if item_lines else "  （无明细）"

        return (
            f"📋 处方信息 — {pres.pres_no}\n"
            f"患者：{patient.name if patient else '-'}\n"
            f"类型：{pres.pres_type}  |  总金额：¥{pres.total_amount}\n"
            f"发药状态：{'✅ 已发药' if pres.dispensed else '⏳ 未发药'}\n"
            f"支付状态：{pres.payment_status}\n"
            f"诊断：{pres.diagnosis or '-'}\n"
            f"药品明细：\n{items_text}"
        )


# ── 统一工具定义（含元数据） ──────────────────────────────────
#
# 每个工具的元数据包含：
#   fn          — 异步函数，接受 (user_info, **params) 返回 str
#   description — 给 LLM 看的工具描述
#   params      — 参数说明 {参数名: 说明}
#   category    — 分类（用于界面分组）
#

TOOL_DEFINITIONS = {
    "today_registrations": {
        "fn": today_registrations,
        "description": "查询今日挂号患者数量（按挂号类型分类统计，含支付状态）",
        "params": {},
        "category": "统计查询",
    },
    "drug_inventory": {
        "fn": drug_inventory,
        "description": "根据药品名称查询药房和药库库存信息",
        "params": {"drug_name": "药品名称（支持模糊匹配）"},
        "category": "药品管理",
    },
    "patient_info": {
        "fn": patient_info,
        "description": "根据患者姓名或病历号查询患者基本信息（含联系方式）",
        "params": {"query": "患者姓名或病历号"},
        "category": "患者管理",
    },
    "prescription_info": {
        "fn": prescription_info,
        "description": "根据处方编号查询处方详细信息（含药品明细和患者信息）",
        "params": {"prescription_id": "处方编号"},
        "category": "处方管理",
    },
}
