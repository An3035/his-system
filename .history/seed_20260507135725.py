"""
seed.py — 初始化基础数据（科室、用户、药品、收费项目、床位）
运行: python seed.py
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from models import Base, Bed, BedStatus, ChargeItem, Department, Doctor, Drug, User
from auth import hash_password

engine = create_async_engine(
    settings.DATABASE_URL.replace("pymysql", "aiomysql"),
    echo=False,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # ── 科室 ──────────────────────────────────────────────
        departments = [
            Department(name="内科", code="NK", description="内科诊室，提供普通内科及专科诊疗"),
            Department(name="外科", code="WK", description="外科手术及门诊"),
            Department(name="儿科", code="EK", description="儿童专科诊疗"),
            Department(name="妇产科", code="FCK", description="妇科及产科"),
            Department(name="中医科", code="ZYK", description="中医诊疗及针灸推拿"),
            Department(name="检验科", code="JYK", description="临床检验"),
            Department(name="放射科", code="FSK", description="X光、CT、MRI"),
            Department(name="手术室", code="SSS", description="外科手术"),
        ]
        db.add_all(departments)
        await db.flush()

        # ── 医生 ──────────────────────────────────────────────
        doctors = [
            Doctor(
                name="张伟",
                title="主任医师",
                department_id=departments[0].id,
                introduction="从事内科临床工作30年",
            ),
            Doctor(name="李芳", title="副主任医师", department_id=departments[0].id),
            Doctor(name="王磊", title="主治医师", department_id=departments[1].id),
            Doctor(
                name="赵敏",
                title="主任医师",
                department_id=departments[4].id,
                introduction="中医世家，擅长针灸",
            ),
        ]
        db.add_all(doctors)

        # ── 系统用户 ──────────────────────────────────────────
        users = [
            User(
                username="admin",
                hashed_password=hash_password("Admin@123"),
                real_name="系统管理员",
                role="admin",
            ),
            User(
                username="doctor1",
                hashed_password=hash_password("Doctor@123"),
                real_name="张伟",
                role="doctor",
                department_id=departments[0].id,
            ),
            User(
                username="nurse1",
                hashed_password=hash_password("Nurse@123"),
                real_name="陈护士",
                role="nurse",
                department_id=departments[0].id,
            ),
            User(
                username="cashier1",
                hashed_password=hash_password("Cashier@123"),
                real_name="刘收费",
                role="cashier",
            ),
            User(
                username="pharmacist1",
                hashed_password=hash_password("Pharma@123"),
                real_name="孙药师",
                role="pharmacist",
            ),
        ]
        db.add_all(users)

        # ── 药品 ──────────────────────────────────────────────
        drugs = [
            Drug(
                drug_code="W001",
                name="阿莫西林胶囊",
                generic_name="阿莫西林",
                drug_type="西药",
                specification="0.25g×24粒",
                unit="盒",
                retail_price=Decimal("12.50"),
                purchase_price=Decimal("8.00"),
                manufacturer="华北制药",
            ),
            Drug(
                drug_code="W002",
                name="布洛芬缓释胶囊",
                generic_name="布洛芬",
                drug_type="西药",
                specification="0.3g×20粒",
                unit="盒",
                retail_price=Decimal("15.80"),
                purchase_price=Decimal("10.00"),
                manufacturer="中美史克",
            ),
            Drug(
                drug_code="W003",
                name="氯化钠注射液",
                generic_name="氯化钠",
                drug_type="西药",
                specification="500ml",
                unit="瓶",
                retail_price=Decimal("5.50"),
                purchase_price=Decimal("3.00"),
                manufacturer="科伦药业",
            ),
            Drug(
                drug_code="W004",
                name="葡萄糖注射液",
                generic_name="葡萄糖",
                drug_type="西药",
                specification="250ml/5%",
                unit="瓶",
                retail_price=Decimal("6.00"),
                purchase_price=Decimal("3.50"),
                manufacturer="科伦药业",
            ),
            Drug(
                drug_code="W005",
                name="头孢克洛干混悬剂",
                generic_name="头孢克洛",
                drug_type="西药",
                specification="125mg×12袋",
                unit="盒",
                retail_price=Decimal("38.00"),
                purchase_price=Decimal("25.00"),
                manufacturer="礼来制药",
            ),
            Drug(
                drug_code="Z001",
                name="黄芪",
                drug_type="中药",
                specification="饮片",
                unit="克",
                retail_price=Decimal("0.08"),
                purchase_price=Decimal("0.05"),
                manufacturer="同仁堂",
            ),
            Drug(
                drug_code="Z002",
                name="当归",
                drug_type="中药",
                specification="饮片",
                unit="克",
                retail_price=Decimal("0.15"),
                purchase_price=Decimal("0.10"),
                manufacturer="同仁堂",
            ),
            Drug(
                drug_code="Z003",
                name="六味地黄丸",
                drug_type="中药",
                specification="9g×10丸",
                unit="盒",
                retail_price=Decimal("25.00"),
                purchase_price=Decimal("16.00"),
                manufacturer="宛西制药",
            ),
        ]
        db.add_all(drugs)

        # ── 收费项目 ──────────────────────────────────────────
        charge_items = [
            ChargeItem(
                item_code="JY001", name="血常规", category="检验", unit_price=Decimal("25.00")
            ),
            ChargeItem(
                item_code="JY002", name="尿常规", category="检验", unit_price=Decimal("15.00")
            ),
            ChargeItem(
                item_code="JY003", name="肝功能检查", category="检验", unit_price=Decimal("80.00")
            ),
            ChargeItem(
                item_code="JY004", name="血糖检测", category="检验", unit_price=Decimal("20.00")
            ),
            ChargeItem(
                item_code="SS001", name="阑尾切除术", category="手术", unit_price=Decimal("3500.00")
            ),
            ChargeItem(
                item_code="SS002", name="疝气修补术", category="手术", unit_price=Decimal("4200.00")
            ),
            ChargeItem(
                item_code="BS001", name="腹部B超", category="B超", unit_price=Decimal("120.00")
            ),
            ChargeItem(
                item_code="BS002", name="心脏彩超", category="B超", unit_price=Decimal("180.00")
            ),
            ChargeItem(
                item_code="WJ001", name="胃镜检查", category="胃镜", unit_price=Decimal("350.00")
            ),
            ChargeItem(
                item_code="FS001", name="胸部X光", category="放射", unit_price=Decimal("80.00")
            ),
            ChargeItem(
                item_code="FS002",
                name="CT平扫（胸部）",
                category="放射",
                unit_price=Decimal("450.00"),
            ),
        ]
        db.add_all(charge_items)

        # ── 床位 ──────────────────────────────────────────────
        beds = []
        for ward_num in range(1, 4):
            for bed_num in range(1, 9):
                beds.append(
                    Bed(
                        bed_no=f"{ward_num:02d}-{bed_num:02d}",
                        ward=f"{ward_num}病区",
                        department_id=departments[ward_num - 1].id,
                        status=BedStatus.AVAILABLE,
                    )
                )
        db.add_all(beds)

        await db.commit()
        print("✅ 初始数据导入完成")
        print("   默认账号:")
        print("   admin/Admin@123       - 管理员")
        print("   doctor1/Doctor@123    - 医生")
        print("   nurse1/Nurse@123      - 护士")
        print("   cashier1/Cashier@123  - 收费员")
        print("   pharmacist1/Pharma@123 - 药师")


if __name__ == "__main__":
    asyncio.run(seed())
