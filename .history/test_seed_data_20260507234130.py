# test_seed_data.py
from __future__ import annotations
import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from seed import SessionLocal, Department, Doctor, Bed, Drug, User, ChargeItem


async def check_data_uniformity():
    async with SessionLocal() as db:
        # 1. 检查科室-医生关联
        doctors = await db.scalars(Doctor.__select__().join(Department, isouter=True))
        for doctor in doctors:
            if not doctor.department_id:
                print(f"❌ 医生 {doctor.name} 无科室关联")
            elif not await db.get(Department, doctor.department_id):
                print(f"❌ 医生 {doctor.name} 的科室ID {doctor.department_id} 不存在")

        # 2. 检查药品价格格式（两位小数）
        drugs = await db.scalars(Drug.__select__())
        for drug in drugs:
            if (
                str(drug.retail_price).split(".")[-1] != 2
                or str(drug.purchase_price).split(".")[-1] != 2
            ):
                print(f"❌ 药品 {drug.name} 价格小数位不统一")

        # 3. 检查床位状态枚举（仅 AVAILABLE/OCUPIED 等）
        beds = await db.scalars(Bed.__select__())
        valid_status = ["AVAILABLE", "OCCUPIED", "MAINTENANCE"]  # 对应 BedStatus 枚举
        for bed in beds:
            if bed.status not in valid_status:
                print(f"❌ 床位 {bed.bed_no} 状态 {bed.status} 不合法")

        # 4. 检查用户密码哈希长度（hash_password 生成的长度应统一）
        users = await db.scalars(User.__select__())
        hash_length = len(users[0].hashed_password) if users else 0
        for user in users:
            if len(user.hashed_password) != hash_length:
                print(f"❌ 用户 {user.username} 密码哈希长度不一致")

        print("✅ 数据统一性检查完成（无报错则符合预期）")


if __name__ == "__main__":
    asyncio.run(check_data_uniformity())
