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
import time
import requests
from pathlib import Path
from typing import List, Optional, Tuple

from dashscope import Generation
from loguru import logger

from config import settings
from content_filter import filter_ai_output, filter_user_input

# Dashscope 初始化
import dashscope

dashscope.api_key = settings.DASHSCOPE_API_KEY
dashscope.region = settings.DASHSCOPE_REGION  # 从配置读取区域（北京）
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
# 浏览器 MediaRecorder → WebM(Opus) → ffmpeg → WAV(PCM 16kHz) → fun-asr-realtime
#
# 格式断层（核心问题）：
#   浏览器只能产出 WebM 容器 → fun-asr-realtime 不支持 WebM
#   解法：ffmpeg 转 WAV（PCM 16kHz mono），业界通用做法
#
# 踩坑记录：
#   ❌ Recognition(model="fun-asr") → ModelNotFound（fun-asr 是文件转写模型，不是实时模型）
#   ❌ Recognition(model="fun-asr-realtime", format="webm") → UNSUPPORTED_FORMAT
#   ❌ Recognition(model="fun-asr-realtime", format="opus") → NO_VALID_AUDIO_ERROR（WebM 容器头 ≠ 裸 Opus）
#   ❌ Transcription + OssUtils → FILE_403_FORBIDDEN / SERVER_ERROR（OSS 权限不对）
#   ❌ paraformer-* → 华北2 已下线


def _extract_transcription_text(data: dict) -> str:
    """从转录结果JSON中提取纯文本（兼容多种返回格式）。"""
    # 格式A（官方标准）: {"transcripts":[{"sentences":[{"text":"..."}]}]}
    transcripts = data.get("transcripts", [])
    if transcripts:
        parts: list[str] = []
        for t in transcripts:
            for s in t.get("sentences", []):
                txt = s.get("text", "").strip()
                if txt:
                    parts.append(txt)
        if parts:
            return " ".join(parts)

    # 格式B（简化版）: {"text": "..."}
    if data.get("text"):
        return data["text"].strip()

    # 格式C（旧版）: {"result": "..."}
    if data.get("result"):
        return data["result"].strip()

    # 格式D: {"results":[{"text":"..."}]}
    results = data.get("results", [])
    if isinstance(results, list) and results:
        parts = []
        for r in results:
            txt = r.get("text", "").strip()
            if txt:
                parts.append(txt)
        if parts:
            return " ".join(parts)

    return ""


async def asr_transcribe(audio_data: bytes, filename: str = "audio.webm") -> dict:
    """
    阿里云百炼 fun-asr-realtime 语音识别。

    流程：浏览器 WebM(Opus) → ffmpeg 转 WAV(PCM 16kHz mono) → Recognition WebSocket

    Returns:
        {"text": "识别文本", "duration": <秒>, "error": None}   成功
        {"text": "",      "duration": <秒>, "error": "原因"}    失败
    """
    import os as _os
    import subprocess as _subprocess
    import tempfile as _tempfile
    from dashscope.audio.asr import Recognition, RecognitionCallback

    t0 = time.perf_counter()
    webm_path: str | None = None
    wav_path: str | None = None

    def _log(msg: str) -> None:
        print(f"[ASR] {msg}", flush=True)
        logger.info(msg)

    def _log_err(msg: str) -> None:
        print(f"[ASR ERROR] {msg}", flush=True)
        logger.error(msg)

    def _cleanup(*paths: str) -> None:
        for p in paths:
            if p and _os.path.exists(p):
                try:
                    _os.unlink(p)
                except OSError:
                    pass

    try:
        # ── 验证输入 ────────────────────────────────────────
        if not audio_data or len(audio_data) < 100:
            _log_err(f"音频过小（{len(audio_data)} bytes），拒绝处理")
            return {"text": "", "duration": 0, "error": "音频数据无效，请重新录音"}

        _log(f"📥 收到音频 → {len(audio_data)} bytes | {filename}")

        # ── 第1步：写入 WebM 临时文件 ──────────────────────
        suffix = _os.path.splitext(filename)[1] or ".webm"
        with _tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_data)
            webm_path = f.name
        _log(f"💾 WebM → {webm_path} ({_os.path.getsize(webm_path)} bytes)")

        # ── 第2步：ffmpeg WebM → WAV (PCM 16kHz mono) ─────
        # 浏览器 MediaRecorder 产出 WebM(Opus)，fun-asr-realtime 不支持 WebM
        # 用 ffmpeg 转成标准 WAV，这是业界通用做法
        wav_fd, wav_path = _tempfile.mkstemp(suffix=".wav")
        _os.close(wav_fd)

        cmd = [
            "ffmpeg",
            "-y",                  # 覆盖输出文件
            "-i", webm_path,       # 输入 WebM
            "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
            "-ar", "16000",        # 16kHz 采样率
            "-ac", "1",            # 单声道
            "-loglevel", "error",  # 只输出错误
            wav_path,
        ]
        _log(f"🔄 ffmpeg 转码: WebM → WAV...")

        # Windows 上 asyncio.create_subprocess_exec 有 ProactorEventLoop 限制
        # 用 subprocess.run 放在线程池里执行，更可靠
        def _run_ffmpeg():
            return _subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        try:
            proc = await asyncio.wait_for(
                asyncio.to_thread(_run_ffmpeg),
                timeout=35,
            )
        except asyncio.TimeoutError:
            _log_err("ffmpeg 转码超时")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(time.perf_counter() - t0, 2),
                "error": "音频格式转换超时，请重新录音",
            }

        if proc.returncode != 0 or not _os.path.exists(wav_path) or _os.path.getsize(wav_path) < 100:
            _log_err(f"ffmpeg 转码失败，exit_code={proc.returncode}, stderr={proc.stderr[:200]}")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(time.perf_counter() - t0, 2),
                "error": "音频格式转换失败，请重新录音",
            }

        wav_size = _os.path.getsize(wav_path)
        _log(f"🎵 WAV → {wav_path} ({wav_size} bytes)")

        # ── 第3步：创建 Recognition 实例 ────────────────────
        callback = RecognitionCallback()
        recognition = Recognition(
            model="fun-asr-realtime",
            callback=callback,
            format="wav",
            sample_rate=16000,
        )
        _log("🔌 Recognition(fun-asr-realtime, wav) → 准备连接 WebSocket")

        # ── 第4步：同步文件识别 ────────────────────────────
        _log("🚀 调用 recognition.call(file=wav)...")
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(recognition.call, file=wav_path),
                timeout=120,
            )
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - t0
            _log_err("识别超时（120s）")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": "语音识别超时，请稍后重试",
            }

        elapsed = time.perf_counter() - t0

        # ── 第5步：解析结果 ────────────────────────────────
        _log(f"📊 status_code={result.status_code} code={result.code} message={result.message}")

        if result.status_code != 200:
            _log_err(f"识别失败: code={result.code}, message={result.message}")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": f"语音识别失败: {result.message or result.code or '未知错误'}",
            }

        sentence_data = result.get_sentence()
        _log(f"📝 sentence_data 类型={type(sentence_data).__name__}, "
             f"内容={json.dumps(sentence_data, ensure_ascii=False)[:500]}")

        if sentence_data is None:
            _log("识别结果为空")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": "未识别到有效语音内容",
            }

        if isinstance(sentence_data, dict):
            text = sentence_data.get("text", "").strip()
        elif isinstance(sentence_data, list):
            parts = [s.get("text", "").strip() for s in sentence_data if s.get("text")]
            text = " ".join(parts)
        else:
            text = ""

        if text:
            _log(f"✅ 识别成功 → '{text}' ({len(text)}字) | 总耗时 {elapsed:.2f}s")
            _cleanup(webm_path, wav_path)
            return {"text": text, "duration": round(elapsed, 2), "error": None}
        else:
            _log("识别结果无文本")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": "音频无有效语音内容，请重新录音",
            }

    except FileNotFoundError:
        elapsed = time.perf_counter() - t0
        _log_err("临时文件或 ffmpeg 不存在")
        _cleanup(webm_path, wav_path)
        return {
            "text": "",
            "duration": round(elapsed, 2),
            "error": "ffmpeg 未安装，请联系管理员",
        }
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        _log_err(f"💥 异常: {type(exc).__name__}: {exc}")
        logger.exception("ASR 完整异常堆栈")
        _cleanup(webm_path, wav_path)
        return {
            "text": "",
            "duration": round(elapsed, 2),
            "error": f"语音识别服务异常: {type(exc).__name__}",
        }
