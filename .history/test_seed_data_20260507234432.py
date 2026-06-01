from __future__ import annotations
import asyncio
from decimal import Decimal

# 补充 SQLAlchemy 必要导入
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 确保 SessionLocal 和模型导入路径正确
from seed import SessionLocal, Department, Doctor, Bed, Drug, User, ChargeItem

# 导入 BedStatus 枚举（seed.py 中用到的床位状态）
from models import BedStatus


async def check_data_uniformity():
    async with SessionLocal() as db:
        # 1. 检查科室-医生关联（修正查询方式）
        stmt = select(Doctor).join(Department, Doctor.department_id == Department.id, isouter=True)
        doctors = await db.scalars(stmt)
        doctors_list = doctors.all()  # 转为列表方便遍历
        if not doctors_list:
            print("⚠️  未查询到医生数据")
        else:
            for doctor in doctors_list:
                if not doctor.department_id:
                    print(f"❌ 医生 {doctor.name} 无科室关联")
                else:
                    # 检查科室ID是否存在
                    dept = await db.get(Department, doctor.department_id)
                    if not dept:
                        print(f"❌ 医生 {doctor.name} 的科室ID {doctor.department_id} 不存在")

        # 2. 检查药品价格格式（两位小数，修正判断逻辑）
        drugs_stmt = select(Drug)
        drugs = await db.scalars(drugs_stmt)
        drugs_list = drugs.all()
        if not drugs_list:
            print("⚠️  未查询到药品数据")
        else:
            for drug in drugs_list:
                # 处理整数位（如 25.00 会显示为 25，需统一转为两位小数）
                retail_str = f"{drug.retail_price:.2f}"
                purchase_str = f"{drug.purchase_price:.2f}"
                # 验证原始值是否等于两位小数格式（避免手动输入 12.5 而非 12.50）
                if (
                    Decimal(retail_str) != drug.retail_price
                    or Decimal(purchase_str) != drug.purchase_price
                ):
                    print(
                        f"❌ 药品 {drug.name} 价格小数位不统一（零售：{drug.retail_price}，采购：{drug.purchase_price}）"
                    )

        # 3. 检查床位状态枚举（关联 BedStatus 枚举类，避免硬编码）
        beds_stmt = select(Bed)
        beds = await db.scalars(beds_stmt)
        beds_list = beds.all()
        if not beds_list:
            print("⚠️  未查询到床位数据")
        else:
            valid_status = [status.value for status in BedStatus]  # 从枚举取有效值
            for bed in beds_list:
                if bed.status not in valid_status:
                    print(
                        f"❌ 床位 {bed.bed_no} 状态 {bed.status} 不合法（仅支持：{valid_status}）"
                    )

        # 4. 检查用户密码哈希长度（处理空列表情况）
        users_stmt = select(User)
        users = await db.scalars(users_stmt)
        users_list = users.all()
        if not users_list:
            print("⚠️  未查询到用户数据")
        else:
            # 取第一个用户的哈希长度作为基准
            base_hash_length = len(users_list[0].hashed_password)
            for user in users_list:
                current_length = len(user.hashed_password)
                if current_length != base_hash_length:
                    print(
                        f"❌ 用户 {user.username} 密码哈希长度不一致（基准：{base_hash_length}，当前：{current_length}）"
                    )

        print("\n✅ 数据统一性检查完成（无报错则符合预期）")


if __name__ == "__main__":
    asyncio.run(check_data_uniformity())
