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

import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from dashscope import Generation
from dashscope.audio.asr import Recognition
from loguru import logger

from config import settings
from content_filter import filter_ai_output, filter_user_input

# Dashscope 初始化
import dashscope

dashscope.api_key = settings.DASHSCOPE_API_KEY

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
# 前端 MediaRecorder 产生 WebM 容器（Opus 编码）
# Dashscope Paraformer-v2 通过 WebSocket 接收音频流
# format 参数应指定容器格式（"webm"），而非原始编码（"opus"）


class _NoOpRecognitionCallback:
    """空回调实现 —— 用于满足 Recognition 构造器的类型约束。

    Recognition.__init__ 要求 callback 为 RecognitionCallback 实例，
    但同步 call() 路径不使用 callback（仅异步 start() 需要）。
    传入 None 在 dashscope 1.25 不会崩溃，但类型检查不通过。
    """

    def on_open(self) -> None:
        pass

    def on_close(self) -> None:
        pass

    def on_error(self, result) -> None:
        pass

    def on_event(self, result) -> None:
        pass


async def asr_transcribe(audio_data: bytes, filename: str = "audio.webm") -> dict:
    """调用阿里云百炼 Paraformer 语音识别，返回 {"text", "duration", "error"}。

    处理流程：
        WebM(Opus) 原始字节 → 临时文件 → 直接调用 Dashscope Recognition
        无需 ffmpeg 转码，Dashscope 原生支持 WebM 容器格式

    Args:
        audio_data: 音频文件的原始字节（WebM 容器，Opus 编码）
        filename: 原始文件名，仅用于日志

    Returns:
        {"text": str, "duration": float, "error": str|None}
        失败时 text=""、duration=0、error 包含具体错误信息。
    """
    t0 = time.perf_counter()
    tmp_file = None

    try:
        # 1. 写入临时文件（保存原始 WebM 音频，不做任何转码）
        tmp_file = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
        tmp_file.write(audio_data)
        tmp_file.flush()
        tmp_file.close()

        logger.info(f"ASR: 收到音频数据 {len(audio_data)} bytes, filename={filename}")

        # 2. 调用阿里云识别
        #    format="webm" 是关键：前端 MediaRecorder 输出 WebM 容器 + Opus 编码，
        #    Dashscope Recognition API 通过 WebSocket 接收，format 指定容器格式。
        #    若传 "opus" 则 API 期望原始 Opus 流而非 WebM 容器，会导致解析失败。
        recognition = Recognition(
            model="paraformer-v2",
            callback=_NoOpRecognitionCallback(),
            format="webm",
            sample_rate=16000,
        )
        result = await asyncio.to_thread(recognition.call, file=tmp_file.name)

        elapsed = time.perf_counter() - t0

        # 打印完整响应用于排查
        logger.info(
            f"ASR: Dashscope 响应 — status={result.status_code}, "
            f"code={getattr(result, 'code', 'N/A')}, "
            f"message={getattr(result, 'message', 'N/A')}, "
            f"output={getattr(result, 'output', 'N/A')}"
        )

        if result.status_code == 200:
            sentence = result.get_sentence()
            if isinstance(sentence, dict):
                text = sentence.get("text", "")
            elif isinstance(sentence, list) and len(sentence) > 0:
                text = "".join(s.get("text", "") for s in sentence if isinstance(s, dict))
            else:
                text = ""

            logger.info(f"ASR: 识别成功 — 耗时 {elapsed:.2f}s, 文本: '{text}' (长度 {len(text)})")
            return {"text": text, "duration": round(elapsed, 2)}

        else:
            # 详细错误记录在服务端日志，返回给用户的是通用提示
            dashscope_code = getattr(result, "code", "")
            dashscope_msg = getattr(result, "message", "")
            logger.error(
                f"ASR: 识别失败 — status={result.status_code}, "
                f"code={dashscope_code}, message={dashscope_msg}"
            )
            return {
                "text": "",
                "duration": 0,
                "error": f"Dashscope API错误: {dashscope_code} - {dashscope_msg}",
            }

    except Exception as e:
        logger.exception(f"ASR: 调用异常: {type(e).__name__}: {e}")
        return {"text": "", "duration": 0, "error": "语音识别服务暂时不可用，请稍后重试"}
    finally:
        # 清理临时文件
        if tmp_file:
            try:
                Path(tmp_file.name).unlink(missing_ok=True)
            except OSError:
                pass
