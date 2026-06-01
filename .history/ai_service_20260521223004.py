from __future__ import annotations

import json
from typing import List

import dashscope
from dashscope import Generation
from loguru import logger

from config import settings

dashscope.api_key = settings.DASHSCOPE_API_KEY

HIS_SYSTEM_PROMPT = """你是一位专业的医院信息系统（HIS）AI助手，服务于医院医护人员。
你的职责：
1. 协助医生快速查询药品信息、配伍禁忌、用法用量
2. 根据症状描述提供初步诊断参考（仅供参考，最终由医生决定）
3. 帮助护士整理医嘱、生成护理记录摘要
4. 协助管理员分析财务报表和药品库存趋势
5. 解答医院信息系统操作问题

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
) -> str:
    """
    调用 Dashscope 模型进行对话。

    Args:
        user_message: 用户当前消息
        history: 历史对话 [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]
        context_type: 上下文类型 patient/drug/report/general
        context_data: 额外上下文数据（如患者信息）
    """
    messages = [{"role": "system", "content": HIS_SYSTEM_PROMPT}]

    # 注入上下文
    if context_data and context_type != "general":
        ctx_text = f"【当前操作上下文 - {context_type}】\n{json.dumps(context_data, ensure_ascii=False, indent=2)}"
        messages.append({"role": "system", "content": ctx_text})

    # 历史对话（最多保留最近10轮）
    if history:
        messages.extend(history[-20:])

    messages.append({"role": "user", "content": user_message})

    try:
        response = Generation.call(
            model=settings.DASHSCOPE_MODEL,
            messages=messages,
            result_format="message",
            max_tokens=1000,
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


async def summarize_patient_history(patient_data: dict) -> str:
    """生成患者病历摘要。"""
    prompt = f"""请为以下患者数据生成一份简洁的病历摘要（200字以内）：
{json.dumps(patient_data, ensure_ascii=False, indent=2)}

摘要应包含：基本信息、主要诊断、用药情况、注意事项。"""
    return await chat_with_ai(prompt, context_type="patient", context_data=patient_data)


async def analyze_drug_interaction(drug_names: List[str]) -> str:
    """分析药物相互作用。"""
    prompt = f"请分析以下药物联合使用时的相互作用和注意事项：{', '.join(drug_names)}"
    return await chat_with_ai(prompt, context_type="drug")


async def interpret_report_data(report_type: str, data: dict) -> str:
    """解读报表数据，为院长提供决策支持。"""
    prompt = f"""请解读以下{report_type}数据，并提供3条管理建议：
{json.dumps(data, ensure_ascii=False, indent=2)}"""
    return await chat_with_ai(prompt, context_type="report", context_data=data)
