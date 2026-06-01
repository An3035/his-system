"""
privacy.py — 患者隐私脱敏工具
"""

from __future__ import annotations

import re
from typing import List

# ── PII 识别模式 ─────────────────────────────────────────────────
_CHINESE_NAME_RE = re.compile(r"(?:患者|病人|姓名)[：:]*\s*([一-龥]{2,4})")
_PHONE_RE = re.compile(r"(?:电话|手机|联系电话|联系方式)[：:]*\s*(1[3-9]\d{9})")
_ID_CARD_RE = re.compile(r"(?:身份证|证件号|身份证号)[：:]*\s*(\d{17}[\dXx])")
_ADDRESS_RE = re.compile(
    r"(?:地址|住址|家庭住址|现住址)[：:]*\s*"
    r"([一-龥]{2,10}(?:省|自治区|市|区|县|镇|乡|路|街|巷|号|栋|单元|楼|层|室).{0,30})"
)

# 直接匹配模式（不带标签前缀）
_RAW_PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
_RAW_ID_CARD_RE = re.compile(r"(?<!\d)(\d{17}[\dXx])(?!\d)")

# 允许查看完整信息的角色
FULL_ACCESS_ROLES = {"admin", "doctor"}


def mask_name(text: str) -> str:
    """脱敏中文姓名：张三 → 张*"""
    return _CHINESE_NAME_RE.sub(
        lambda m: m.group(0).replace(
            m.group(1),
            m.group(1)[0] + "*" + m.group(1)[2:] if len(m.group(1)) > 2 else m.group(1)[0] + "*",
        ),
        text,
    )


def mask_phone(text: str) -> str:
    """脱敏电话号码：13812345678 → 138****5678"""
    text = _PHONE_RE.sub(
        lambda m: m.group(0).replace(m.group(1), m.group(1)[:3] + "****" + m.group(1)[7:]),
        text,
    )
    # 无标签前缀的裸号码
    text = _RAW_PHONE_RE.sub(
        lambda m: m.group(1)[:3] + "****" + m.group(1)[7:],
        text,
    )
    return text


def mask_id_card(text: str) -> str:
    """脱敏身份证号：440101199001011234 → 440***********1234"""
    text = _ID_CARD_RE.sub(
        lambda m: m.group(0).replace(
            m.group(1),
            m.group(1)[:3] + "***********" + m.group(1)[-4:],
        ),
        text,
    )
    text = _RAW_ID_CARD_RE.sub(
        lambda m: m.group(1)[:3] + "***********" + m.group(1)[-4:],
        text,
    )
    return text


def mask_address(text: str) -> str:
    """脱敏地址：保留省市区，隐藏详细地址"""
    return _ADDRESS_RE.sub(
        lambda m: m.group(0).replace(
            m.group(1),
            m.group(1)[:6] + "***" if len(m.group(1)) > 6 else "***",
        ),
        text,
    )


def mask_pii(text: str, role: str) -> str:
    """
    根据角色对文本进行脱敏。
    admin/doctor — 完整信息
    nurse/pharmacist — 隐藏手机和身份证
    cashier — 隐藏所有PII
    """
    if role in FULL_ACCESS_ROLES:
        return text

    if role == "nurse":
        text = mask_phone(text)
        text = mask_id_card(text)
        return text

    # cashier / pharmacist / 其他
    text = mask_name(text)
    text = mask_phone(text)
    text = mask_id_card(text)
    text = mask_address(text)
    return text


def mask_patient_dict(data: dict, role: str) -> dict:
    """对患者信息字典进行脱敏。"""
    masked = dict(data)
    if role in FULL_ACCESS_ROLES:
        return masked
    if "phone" in masked and masked["phone"]:
        masked["phone"] = masked["phone"][:3] + "****" + masked["phone"][7:]
    if "id_card" in masked and masked["id_card"]:
        masked["id_card"] = masked["id_card"][:3] + "***********" + masked["id_card"][-4:]
    if "address" in masked and masked["address"] and role != "nurse":
        masked["address"] = masked["address"][:6] + "***"
    if "name" in masked and masked["name"] and role not in ("doctor", "nurse"):
        masked["name"] = masked["name"][0] + "*"
    return masked
