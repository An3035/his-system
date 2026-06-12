"""
ai_service.py — AI 服务层（对外接口不变，内部使用 LangGraph 多智能体）

对外保持与原有版本完全兼容的 5 个函数：
  chat_with_ai()              → str          （内部走 LangGraph Agent）
  chat_with_safety()          → Tuple[str, bool]
  summarize_patient_history() → str
  analyze_drug_interaction()  → str
  interpret_report_data()     → str

内部升级：
  - LangGraph StateGraph 多智能体编排
  - Router → Consultant / Medical / Science / Tool 四条路径
  - Dashscope 调用方式不变，不依赖 langchain-community 的 ChatModel 封装
"""

from __future__ import annotations
import os
import uuid
import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from dashscope import Generation, MultiModalConversation
from dashscope.audio.asr import Recognition, RecognitionCallback
from loguru import logger

from config import settings
from content_filter import filter_ai_output, filter_user_input

# Dashscope 初始化
import dashscope

dashscope.api_key = settings.DASHSCOPE_API_KEY
dashscope.region = "cn-hangzhou"  # ✅ 强制设置为杭州区域，和模型部署区域一致
# ── HIS 系统提示词 ──────────────────────────────────────────

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


# ── 底层 LLM 调用（与原有相同） ────────────────────────────


async def _call_llm(
    messages: List[dict],
    system_prompt: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> str:
    """Dashscope API 调用。"""
    full = []
    if system_prompt:
        full.append({"role": "system", "content": system_prompt})
    full.extend(messages)
    try:
        response = Generation.call(
            model=settings.DASHSCOPE_MODEL,
            messages=full,
            result_format="message",
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        logger.error(f"Dashscope error: {response.code} - {response.message}")
        return f"AI服务暂时不可用（{response.code}），请稍后重试。"
    except Exception as e:
        logger.exception(f"AI调用异常: {e}")
        return "AI服务异常，请联系管理员。"


# ── 对外接口（签名完全不变） ───────────────────────────────


async def chat_with_ai(
    user_message: str,
    history: List[dict] | None = None,
    context_type: str = "general",
    context_data: dict | None = None,
    current_user: dict | None = None,
) -> str:
    """
    与 AI 对话。内部使用 LangGraph 多智能体路由。

    Args:
        user_message: 用户当前消息
        history: 历史对话 [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]
        context_type: 上下文类型 patient/drug/report/general
        context_data: 额外上下文数据
        current_user: 当前用户信息 {"id": int, "role": str, "name": str}，用于工具权限校验

    Returns:
        回复文本
    """
    try:
        from ai_engine.graph import get_agent_executor, make_initial_state

        executor = get_agent_executor()
        initial = make_initial_state(
            user_message=user_message,
            history=history,
            context_type=context_type,
            context_data=context_data,
            current_user=current_user,
        )
        result = await executor.ainvoke(initial)
        return result.get("final_response", "")
    except Exception as e:
        logger.exception(f"LangGraph 执行异常，回退到直接调用: {e}")
        # 降级：直接调用 Dashscope
        return await _fallback_chat(user_message, history, context_type, context_data)


async def _fallback_chat(
    user_message: str,
    history: List[dict] | None = None,
    context_type: str = "general",
    context_data: dict | None = None,
) -> str:
    """降级方案：直接调用 Dashscope（不走 LangGraph）。"""
    messages = [{"role": "system", "content": HIS_SYSTEM_PROMPT}]
    if context_data and context_type != "general":
        ctx_text = (
            f"【当前操作上下文 - {context_type}】\n"
            f"{json.dumps(context_data, ensure_ascii=False, indent=2)}"
        )
        messages.append({"role": "system", "content": ctx_text})
    if history:
        messages.extend(history[-20:])
    messages.append({"role": "user", "content": user_message})
    return await _call_llm(messages)


async def chat_with_safety(
    user_message: str,
    history: List[dict] | None = None,
    context_type: str = "general",
    context_data: dict | None = None,
    current_user: dict | None = None,
) -> Tuple[str, bool]:
    """
    带安全过滤的 AI 对话。

    Args:
        current_user: 当前用户信息，用于工具调用权限校验

    Returns:
        (reply, rejected) — rejected=True 表示被安全过滤拦截
    """
    is_safe, rejection = filter_user_input(user_message)
    if not is_safe:
        return rejection, True

    reply = await chat_with_ai(
        user_message=user_message,
        history=history,
        context_type=context_type,
        context_data=context_data,
        current_user=current_user,
    )
    reply = filter_ai_output(reply)
    return reply, False


async def summarize_patient_history(patient_data: dict) -> str:
    """生成患者病历摘要（200 字以内）。"""
    prompt = (
        f"请为以下患者数据生成一份简洁的病历摘要（200字以内）：\n"
        f"{json.dumps(patient_data, ensure_ascii=False, indent=2)}\n\n"
        "摘要应包含：基本信息、主要诊断、用药情况、注意事项。"
    )
    return await _call_llm(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=("你是一位病历摘要助手。生成简洁、专业的病历摘要。"),
    )


async def analyze_drug_interaction(drug_names: List[str]) -> str:
    """分析药物相互作用。"""
    prompt = f"请分析以下药物联合使用时的相互作用和注意事项：" f"{', '.join(drug_names)}"
    return await _call_llm(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=(
            "你是一位临床药学专家。分析药物相互作用，" "重点关注禁忌配伍、剂量调整和不良反应。"
        ),
    )


async def interpret_report_data(report_type: str, data: dict) -> str:
    """解读报表数据，为院长提供决策支持。"""
    prompt = (
        f"请解读以下{report_type}数据，并提供3条管理建议：\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}"
    )
    return await _call_llm(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=("你是一位医院管理数据分析师。解读报表数据，" "提供数据驱动的管理建议。"),
    )


# ── 语音识别 (ASR) ──────────────────────────────────────────
# 前端 MediaRecorder 产生 WebM 容器（Opus 编码，实际采样率 16000Hz）
# 使用 Dashscope paraformer-v2 文件识别模型 + call(file=...) 同步模式
#
# 【模型区分】
#   paraformer-v2          → 文件识别，用 call(file=...) 传完整文件
#   paraformer-realtime-v2 → 流式识别，用 start()/send_frame()/stop() 推流
#   两者不可互换：realtime 模型走 call() 路径 → text 始终为空
#
# 【采样率】前端 getUserMedia 约束为 16000Hz，AudioContext 也是 16000Hz。
#   即使 Chrome MediaRecorder 用 Opus 编码时会内部处理，最终文件采样率即为 16000Hz。
#
# 【日志】print() 到 stdout（uvicorn 终端必定可见），同时 logger 写日志文件。
class _NoOpRecognitionCallback(RecognitionCallback):
    """空实现的ASR回调，解决 callback=None 报错问题"""

    def on_open(self) -> None:
        pass

    def on_close(self) -> None:
        pass

    def on_error(self, result) -> None:
        pass

    def on_event(self, result) -> None:
        pass


async def asr_transcribe(audio_data: bytes, filename: str = "audio.webm") -> dict:
    """用 qwen3-asr-flash 实现语音转文字（多模态兼容版，不用Recognition类）"""
    t0 = time.perf_counter()
    tmp_path = None

    def log(msg: str) -> None:
        print(f"[ASR] {msg}", flush=True)
        logger.info(msg)

    def log_err(msg: str) -> None:
        print(f"[ASR ERROR] {msg}", flush=True)
        logger.error(msg)

    try:
        # 1. 空音频校验
        if not audio_data or len(audio_data) < 100:
            log_err(f"音频数据过小: {len(audio_data)} bytes")
            return {"text": "", "duration": 0, "error": "音频数据无效，请重新录音"}

        # 2. 写入临时文件（和之前一样）
        tmp_path = os.path.join(tempfile.gettempdir(), f"his_asr_{uuid.uuid4().hex}.webm")
        with open(tmp_path, "wb") as f:
            f.write(audio_data)
        file_size = os.path.getsize(tmp_path)

        log(
            f"收到 {len(audio_data)} bytes | 文件={filename} | API Key 已配置={bool(dashscope.api_key)}"
        )

        # 3. 用多模态对话方式调用模型（核心修改，放弃Recognition类）
        log("调用 qwen3-asr-flash 模型处理音频...")
        messages = [
            {
                "role": "user",
                "content": [
                    {"audio": tmp_path},
                    {"text": "请把这段语音转写成文字，只返回文本内容，不要多余说明"},
                ],
            }
        ]

        # 同步调用放到线程池，不阻塞FastAPI事件循环
        response = await asyncio.to_thread(
            MultiModalConversation.call,
            model="qwen3-asr-flash",
            messages=messages,
            max_tokens=1000,
            temperature=0.0,  # 温度设为0，确保返回文本稳定
        )
        elapsed = time.perf_counter() - t0

        # 4. 解析模型返回结果
        log(f"模型响应状态码: {response.status_code}")
        log(f"模型完整响应: {response.output}")

        if response.status_code == 200:
            text = response.output.choices[0].message.content.strip()
            if text:
                log(f"识别成功 → '{text}' ({len(text)}字)")
                return {"text": text, "duration": round(elapsed, 2), "error": None}
            else:
                log("模型返回文本为空，可能音频无有效语音")
                return {
                    "text": "",
                    "duration": round(elapsed, 2),
                    "error": "音频无有效语音，请重新录音",
                }
        else:
            log_err(f"模型调用失败 | 状态码: {response.status_code} | 错误信息: {response.message}")
            return {"text": "", "duration": 0, "error": "语音识别服务暂时不可用，请稍后重试"}

    except Exception as exc:
        log_err(f"调用异常: {type(exc).__name__}: {exc}")
        logger.exception("ASR调用异常详情")
        return {"text": "", "duration": 0, "error": "语音识别服务暂时不可用，请稍后重试"}
    finally:
        # 安全清理临时文件
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            log(f"临时文件已清理: {tmp_path}")
