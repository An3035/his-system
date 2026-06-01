from __future__ import annotations

import json
from typing import List
import os
import uuid
from pathlib import Path
import asyncio

import dashscope
from dashscope import Generation, File
from loguru import logger

from config import settings

dashscope.api_key = settings.DASHSCOPE_API_KEY

# 临时文件目录（自动创建）
TEMP_FILE_DIR = Path("./temp_files")
TEMP_FILE_DIR.mkdir(exist_ok=True, parents=True)

HIS_SYSTEM_PROMPT = """你是一位专业的医院信息系统（HIS）AI助手，服务于医院医护人员。
你的职责：
1. 协助医生快速查询药品信息、配伍禁忌、用法用量
2. 根据症状描述提供初步诊断参考（仅供参考，最终由医生决定）
3. 帮助护士整理医嘱、生成护理记录摘要
4. 协助管理员分析财务报表和药品库存趋势
5. 解答医院信息系统操作问题
6. 分析上传的医疗文档、病历、检验报告、PDF文件等

注意：
- 所有医疗建议仅供参考，不替代专业医师判断
- 患者隐私保护优先
- 回答简洁专业，使用中文
"""


async def chat_with_ai(
    user_message: str,
    history: List[dict] | None = None,
    context_type: str = "general",
    context_data: dict | None = None,
    file_ids: List[str] | None = None,  # 新增：阿里云百炼文件ID列表
) -> str:
    """
    调用 Dashscope 模型进行对话，支持文件分析。
    完全兼容原有纯文本调用方式。
    """
    messages = [{"role": "system", "content": HIS_SYSTEM_PROMPT}]

    # 注入上下文（原有逻辑不变）
    if context_data and context_type != "general":
        ctx_text = f"【当前操作上下文 - {context_type}】\n{json.dumps(context_data, ensure_ascii=False, indent=2)}"
        messages.append({"role": "system", "content": ctx_text})

    # 历史对话（原有逻辑不变）
    if history:
        messages.extend(history[-20:])

    # 构建用户消息（核心修改：支持文件+文本混合）
    user_content = []
    if file_ids and len(file_ids) > 0:
        for file_id in file_ids:
            user_content.append({"type": "file", "file": {"file_id": file_id}})
    user_content.append({"type": "text", "text": user_message})

    messages.append({"role": "user", "content": user_content})

    try:
        # 异步调用避免阻塞事件循环
        response = await asyncio.to_thread(
            Generation.call,
            model=settings.DASHSCOPE_MODEL,
            messages=messages,
            result_format="message",
            max_tokens=2000,
            temperature=0.7,
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            logger.error(f"Dashscope error: {response.code} - {response.message}")
            return f"AI服务暂时不可用（{response.code}），请稍后重试。"
    except Exception as e:
        logger.exception(f"AI调用异常: {e}")
        return "AI服务异常，请联系管理员。"


async def upload_file_to_dashscope(file_path: str, file_name: str) -> str:
    """
    异步上传文件到阿里云百炼，返回文件ID。
    支持：PDF/Word/Excel/PPT/TXT/CSV等20+格式，自动OCR扫描件PDF
    """
    try:
        response = await asyncio.to_thread(
            File.upload, file_path=file_path, purpose="file-extract", display_name=file_name
        )
        if response.status_code == 200:
            return response.output.id
        else:
            logger.error(f"文件上传失败: {response.code} - {response.message}")
            raise Exception(f"文件上传失败: {response.message}")
    except Exception as e:
        logger.exception(f"文件上传异常: {e}")
        raise


async def delete_temp_file(file_path: str):
    """异步删除临时文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"临时文件删除失败: {e}")


# 以下原有函数完全不变
async def summarize_patient_history(patient_data: dict) -> str:
    prompt = f"""请为以下患者数据生成一份简洁的病历摘要（200字以内）：
{json.dumps(patient_data, ensure_ascii=False, indent=2)}

摘要应包含：基本信息、主要诊断、用药情况、注意事项。"""
    return await chat_with_ai(prompt, context_type="patient", context_data=patient_data)


async def analyze_drug_interaction(drug_names: List[str]) -> str:
    prompt = f"请分析以下药物联合使用时的相互作用和注意事项：{', '.join(drug_names)}"
    return await chat_with_ai(prompt, context_type="drug")


async def interpret_report_data(report_type: str, data: dict) -> str:
    prompt = f"""请解读以下{report_type}数据，并提供3条管理建议：
{json.dumps(data, ensure_ascii=False, indent=2)}"""
    return await chat_with_ai(prompt, context_type="report", context_data=data)
