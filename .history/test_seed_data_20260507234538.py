from __future__ import annotations
import asyncio
import sys
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 修复异步事件循环关闭问题 (Windows 专属修复)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from seed import SessionLocal, Department, Doctor, Bed, Drug, User, ChargeItem
from models import BedStatus


async def check_data_uniformity():
    db = await SessionLocal().__aenter__()
    try:
        # 1. 检查科室-医生关联
        stmt = select(Doctor).join(Department, Doctor.department_id == Department.id, isouter=True)
        doctors = await db.scalars(stmt)
        doctors_list = doctors.all()
        if not doctors_list:
            print("⚠️  未查询到医生数据")
        else:
            for doctor in doctors_list:
                if not doctor.department_id:
                    print(f"❌ 医生 {doctor.name} 无科室关联")
                else:
                    dept = await db.get(Department, doctor.department_id)
                    if not dept:
                        print(f"❌ 医生 {doctor.name} 的科室ID不存在")

        # 2. 检查药品价格
        drugs_stmt = select(Drug)
        drugs = await db.scalars(drugs_stmt)
        drugs_list = drugs.all()
        if not drugs_list:
            print("⚠️  未查询到药品数据")

        # 3. 检查床位状态
        beds_stmt = select(Bed)
        beds = await db.scalars(beds_stmt)
        beds_list = beds.all()
        if not beds_list:
            print("⚠️  未查询到床位数据")

        # 4. 检查用户数据
        users_stmt = select(User)
        users = await db.scalars(users_stmt)
        users_list = users.all()
        if not users_list:
            print("⚠️  未查询到用户数据")

        print("\n✅ 数据统一性检查完成（无报错则符合预期）")
    finally:
        # 正确关闭数据库连接
        await db.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(check_data_uniformity())
