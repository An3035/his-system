# 阿里云百炼新平台语音识别踩坑全记录：从连续失败到成功的避坑指南

> 踩了一整周的坑，从 FILE_403_FORBIDDEN 到 ModelNotFound，从 SERVER_ERROR 到 UNSUPPORTED_FORMAT，我终于把这条链路跑通了。如果你也在用 FastAPI + 阿里云百炼做语音识别，希望这篇文章能帮你少踩 90% 的坑。

## 前言

我做的是一个医院 HIS 系统，前端 Vue 3，后端 FastAPI，最近在给系统加语音输入功能——医护人员在任何输入框里按住空格说话，松开就自动转成文字填进去。功能设计不复杂，前端用浏览器原生的 MediaRecorder 录 WebM 音频，发到后端 `/api/ai/asr` 接口，调阿里云百炼的语音识别服务，把文字返回来。

听起来挺简单对吧？我在百炼控制台上传了个 WebM 文件测试，fun-asr 模型秒出结果，心想这后端调个 API 还不得分分钟搞定。

然后我就开始了这一周的"渡劫"之旅。

控制台能跑 ≠ 后端能跑，这是我这周学到的最深刻的一课。

---

## 一、先搞懂：为什么控制台能跑，我后端跑不通？

在百炼控制台的"语音识别"页面，你上传一个音频文件，它给你返回识别结果——看起来就是一个简单的文件上传 + API 调用的流程。但实际上，控制台在背后帮你做了好几件事：

```
浏览器上传 WebM → 控制台内部转码 → 上传到 OSS（带权限）→ 调用识别服务 → 返回结果
```

而我最开始的理解是：

```
前端 WebM → 后端原样传过去 → 百炼 API → 返回结果  ← ❌ 大错特错
```

三个关键的东西在我这里全出了问题：

| 维度 | 控制台做的事 | 我最开始做的 |
|------|------------|------------|
| **格式** | 自动转码兼容格式 | WebM 原样传 |
| **模型** | 自动选对模型 | 不知道 realtime 和文件转写的区别 |
| **通道** | 自动匹配 SDK/协议 | 瞎试各种类和方法 |

下面按时间顺序，把我踩过的每一个坑都复盘一遍。

---

## 二、我踩过的所有坑（按顺序复盘）

### 坑 1：Transcription + OSS 上传 → FILE_403_FORBIDDEN

**思路**：看到 SDK 里有 `Transcription` 类，文档说支持"文件转写"。但它要的是 `file_urls`（文件的 HTTP/OSS 地址），不是直接传文件数据。于是我想着先把文件上传到 OSS，再把 OSS 地址传给 Transcription。

**代码大概是这样的**：

```python
from dashscope.audio.asr import Transcription
from dashscope.utils.oss_utils import OssUtils

# 上传文件到 OSS
oss_url, cert = OssUtils.upload(
    model="fun-asr",
    file_path="audio.webm",
)
# 拿 URL 去调异步转写
response = Transcription.async_call(
    model="fun-asr",
    file_urls=[oss_url],
)
# 轮询等待结果
result = Transcription.wait(response.output.task_id)
```

**结果**：任务状态一直是 `FAILED`，错误信息 `FILE_403_FORBIDDEN`，换了文件格式报 `SERVER_ERROR`。

**根因**：`OssUtils.upload()` 上传的 OSS 对象，`x-oss-object-acl` 是服务端下发的权限策略——给多模态模型用的 bucket，ASR 服务没有权限读取。`oss://` 开头的 URL 缺少 bucket 前缀，ASR 服务解析不了。

这本该是我最早放弃的方案，但我硬是换了各种姿势重试了一天。**教训：权限体系是云服务里最容易踩的暗坑，文档上不会写，只有碰了才知道。**

### 坑 2：自己拼 HTTP POST → URL 和参数全错

**思路**：不用 SDK 了，直接调 HTTP API！于是上网搜百炼 ASR 的 API 文档，拼了一个 POST 请求。

**尝试过的 URL 地址**（没有一个是对的）：

```
https://dashscope.aliyuncs.com/api/v1/services/audio-asr/fun-asr/generation
https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation
https://dashscope.aliyuncs.com/compatible-mode/v1/audio/transcriptions
```

**报错合集**：

```
"url error"
"InvalidParameter"
"task can not be null"
"model not found"
```

**根因**：
1. 百炼新平台的 API 路径一直在变，网上搜到的帖子大部分是旧版文档，地址早就失效了
2. fun-asr 的入参格式和其他模型完全不同——有的要 `{"input": {"file_urls": [...]}}`，有的要 `{"input": {"audio": "base64..."}}`，自己瞎拼的请求体格式根本不对
3. Base64 直传音频数据这条路在新平台根本不支持——我之前一直在各种 Base64 方案上浪费时间

**教训：除非你有最新的官方 API 文档，否则不要自己拼 HTTP 请求。SDK 再烂也比你手拼的强。**

### 坑 3：Recognition 类用错模型名 → ModelNotFound

**思路**：放弃 HTTP，试试 WebSocket 实时流方案！SDK 里有 `Recognition` 类，看起来能直接读本地文件。

```python
from dashscope.audio.asr import Recognition, RecognitionCallback

recognition = Recognition(
    model="fun-asr",           # ← 这里错了！
    format="webm",
    sample_rate=16000,
    callback=RecognitionCallback(),
)
result = recognition.call(file="audio.webm")
```

**结果**：`ModelNotFound: fun-asr`

**根因（关键认知突破）**：百炼的 ASR 分了两条完全不同的链路，模型名不能互换：

| SDK 类 | 协议 | 正确模型名 | 场景 |
|--------|------|-----------|------|
| `Recognition` | WebSocket 实时 | `fun-asr-realtime` | 实时识别、本地文件 |
| `Transcription` | HTTP 异步 | `fun-asr` | 录音文件批量转写 |

**`fun-asr` 和 `fun-asr-realtime` 就差一个 `-realtime` 后缀，但底层是完全不同的两套服务和接入点。** 这个设计确实很容易让人踩坑——我在控制台看到的是"fun-asr"，自然以为 SDK 里用的也是这个名字。

### 坑 4：格式不兼容 → UNSUPPORTED_FORMAT / NO_VALID_AUDIO_ERROR

**思路**：模型名改对了，应该没问题了吧？

```python
recognition = Recognition(
    model="fun-asr-realtime",
    format="webm",             # 浏览器录的就是 WebM 啊
    sample_rate=16000,
    callback=RecognitionCallback(),
)
result = recognition.call(file="audio.webm")
```

**结果**：`UNSUPPORTED_FORMAT`

好，那我改成 `format="opus"`（WebM 的底层编码就是 Opus）：

```python
format="opus"
```

**结果**：`NO_VALID_AUDIO_ERROR`

**根因**：`fun-asr-realtime` 支持的音频格式是 `pcm, wav, mp3, opus, speex, aac, amr`——**没有 WebM**。

浏览器 MediaRecorder 只能产出 WebM 容器格式（`audio/webm;codecs=opus`），虽然底层音频编码是 Opus，但 WebM 是一个容器，前面有 EBML/Matroska 头信息。当服务端收到 `format="opus"` 的声明，它期望的是裸 Opus 帧，结果收到 WebM 容器数据——解析失败。

**这才是核心矛盾**：

```
浏览器只能产出 WebM  ←→  fun-asr-realtime 不支持 WebM
```

必须做格式转换，没有捷径。

### 坑 5：Windows 下异步子进程 → NotImplementedError

**思路**：用 ffmpeg 把 WebM 转成 WAV，然后在 FastAPI 里用 `asyncio.create_subprocess_exec` 异步执行 ffmpeg：

```python
proc = await asyncio.create_subprocess_exec(
    "ffmpeg", "-y", "-i", webm_path,
    "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
    wav_path,
)
await proc.wait()
```

**结果**：`NotImplementedError`

**根因**：Windows 上 `asyncio.create_subprocess_exec` 需要 ProactorEventLoop，而 FastAPI/uvicorn 默认用的是 SelectorEventLoop。这个错误信息几乎没有提示，我第一次遇到时完全懵了。

**修法**：改用 `asyncio.to_thread` + `subprocess.run`，在线程池里同步执行 ffmpeg：

```python
def _run_ffmpeg():
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

proc = await asyncio.to_thread(_run_ffmpeg)
```

---

## 三、最终成功的完整方案

### 架构总览

```
浏览器按住空格说话
  → MediaRecorder 录音 → audio/webm;codecs=opus
  → POST /api/ai/asr (FormData)
  → 后端 FastAPI 接收 bytes
  → 写入临时 .webm 文件
  → ffmpeg 转码 → WAV (PCM 16kHz mono)
  → Recognition(model="fun-asr-realtime", format="wav")
  → recognition.call(file=wav_path)
  → SDK 内部 WebSocket 流式发送
  → 返回 {"text": "...", "duration": N, "error": null}
```

### 完整后端代码

以下是 FastAPI 的 ASR 接口和核心识别函数，你可以直接复制使用：

```python
# ============================================================
# ai_service.py — asr_transcribe 函数
# 依赖: dashscope, ffmpeg (系统安装)
# ============================================================

import asyncio
import json
import os
import subprocess
import tempfile
import time

from dashscope.audio.asr import Recognition, RecognitionCallback
from loguru import logger


async def asr_transcribe(audio_data: bytes, filename: str = "audio.webm") -> dict:
    """
    阿里云百炼 fun-asr-realtime 语音识别。

    流程：浏览器 WebM(Opus)
          → ffmpeg 转 WAV (PCM 16kHz mono)
          → Recognition WebSocket 识别

    Returns:
        {"text": "识别文本", "duration": <秒>, "error": None}   成功
        {"text": "",      "duration": <秒>, "error": "原因"}    失败
    """
    t0 = time.perf_counter()
    webm_path: str | None = None
    wav_path: str | None = None

    def _log(msg: str) -> None:
        logger.info(f"[ASR] {msg}")

    def _log_err(msg: str) -> None:
        logger.error(f"[ASR] {msg}")

    def _cleanup(*paths: str) -> None:
        """清理临时文件"""
        for p in paths:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    try:
        # ── 验证输入 ────────────────────────────────
        if not audio_data or len(audio_data) < 100:
            return {"text": "", "duration": 0, "error": "音频数据无效，请重新录音"}

        _log(f"收到音频: {len(audio_data)} bytes | {filename}")

        # ── 第1步：写入 WebM 临时文件 ─────────────────
        suffix = os.path.splitext(filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_data)
            webm_path = f.name
        _log(f"WebM 临时文件: {webm_path} ({os.path.getsize(webm_path)} bytes)")

        # ── 第2步：ffmpeg 转 WebM → WAV ─────────────
        wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(wav_fd)

        cmd = [
            "ffmpeg",
            "-y",                        # 覆盖已存在文件
            "-i", webm_path,             # 输入文件
            "-acodec", "pcm_s16le",      # PCM 16-bit little-endian
            "-ar", "16000",              # 16kHz 采样率
            "-ac", "1",                  # 单声道
            "-loglevel", "error",        # 只输出错误日志
            wav_path,
        ]

        _log("ffmpeg 转码: WebM → WAV...")

        # ⚠️ Windows 上用 asyncio.to_thread + subprocess.run
        # 不要用 asyncio.create_subprocess_exec（会报 NotImplementedError）
        def _run_ffmpeg():
            return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        proc = await asyncio.wait_for(
            asyncio.to_thread(_run_ffmpeg),
            timeout=35,
        )

        if (proc.returncode != 0
                or not os.path.exists(wav_path)
                or os.path.getsize(wav_path) < 100):
            _log_err(f"ffmpeg 失败: exit={proc.returncode}, "
                     f"stderr={proc.stderr[:200]}")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(time.perf_counter() - t0, 2),
                "error": "音频格式转换失败，请重新录音",
            }

        wav_size = os.path.getsize(wav_path)
        _log(f"WAV 文件: {wav_path} ({wav_size} bytes)")

        # ── 第3步：创建 Recognition 实例 ──────────────
        # 关键配置：
        #   model:  fun-asr-realtime（实时模型，别写成 fun-asr）
        #   format: wav（转码后的标准格式）
        #   sample_rate: 16000
        callback = RecognitionCallback()
        recognition = Recognition(
            model="fun-asr-realtime",
            callback=callback,
            format="wav",
            sample_rate=16000,
        )
        _log("Recognition 实例已创建，准备 WebSocket 连接")

        # ── 第4步：调用识别 ──────────────────────────
        # call(file=path) 做的事：
        #   ① 通过 WebSocket 连接百炼实时 ASR 服务
        #   ② 读本地文件 → 12800 bytes/chunk 逐块发送
        #   ③ 接收识别结果
        #   ④ 返回 RecognitionResult（含完整文本）
        result = await asyncio.wait_for(
            asyncio.to_thread(recognition.call, file=wav_path),
            timeout=120,
        )

        elapsed = time.perf_counter() - t0

        # ── 第5步：解析结果 ──────────────────────────
        if result.status_code != 200:
            _log_err(f"识别失败: code={result.code}, msg={result.message}")
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": f"语音识别失败: {result.message or result.code}",
            }

        sentence_data = result.get_sentence()

        if sentence_data is None:
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": "未识别到有效语音内容",
            }

        # 处理单句 dict 或多句 list
        if isinstance(sentence_data, dict):
            text = sentence_data.get("text", "").strip()
        elif isinstance(sentence_data, list):
            parts = [s.get("text", "").strip()
                     for s in sentence_data if s.get("text")]
            text = " ".join(parts)
        else:
            text = ""

        if text:
            _log(f"识别成功: '{text}' ({len(text)}字) "
                 f"| 耗时 {elapsed:.2f}s")
            _cleanup(webm_path, wav_path)
            return {"text": text, "duration": round(elapsed, 2), "error": None}
        else:
            _cleanup(webm_path, wav_path)
            return {
                "text": "",
                "duration": round(elapsed, 2),
                "error": "音频无有效语音内容，请重新录音",
            }

    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - t0
        _cleanup(webm_path, wav_path)
        return {
            "text": "",
            "duration": round(elapsed, 2),
            "error": "语音识别超时，请稍后重试",
        }

    except FileNotFoundError:
        _cleanup(webm_path, wav_path)
        return {
            "text": "",
            "duration": round(time.perf_counter() - t0, 2),
            "error": "ffmpeg 未安装，请联系管理员",
        }

    except Exception as exc:
        elapsed = time.perf_counter() - t0
        logger.exception(f"ASR 异常: {type(exc).__name__}: {exc}")
        _cleanup(webm_path, wav_path)
        return {
            "text": "",
            "duration": round(elapsed, 2),
            "error": f"语音识别服务异常: {type(exc).__name__}",
        }


# ============================================================
# FastAPI 路由（routers.py）
# ============================================================
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

ai_router = APIRouter(prefix="/api/ai", tags=["AI助手"])


@ai_router.post("/asr")
async def speech_to_text(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """语音识别：接收 WebM 音频，返回识别文本"""
    audio_bytes = await file.read()
    result = await asr_transcribe(
        audio_bytes,
        filename=file.filename or "audio.webm",
    )
    return JSONResponse(content=result)
```

### 前端调用（参考）

```typescript
// utils/request.ts
export async function asrRecognize(audioBlob: Blob): Promise<{
  text: string
  duration?: number
  error?: string
}> {
  const form = new FormData()
  form.append('file', audioBlob, 'recording.webm')
  const { data } = await request.post('/api/ai/asr', form)
  return data
}
```

### 安装 ffmpeg

```bash
# Windows (winget)
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux (Debian/Ubuntu)
sudo apt install ffmpeg
```

---

## 四、避坑总结：给后来人抄作业

### 1. 格式 / 模型 / SDK 必须严格匹配

这是最核心的教训。下面这张表贴在屏幕旁边，写代码时对着看：

| 场景 | SDK 类 | 正确模型 | 协议 | 需要 URL？ |
|------|--------|---------|------|-----------|
| 实时识别 + 本地文件 | `Recognition` | `fun-asr-realtime` | WebSocket | ❌ 不用 |
| 实时识别 + 流式推送 | `Recognition` | `fun-asr-realtime` | WebSocket | ❌ 不用 |
| 录音文件批量转写 | `Transcription` | `fun-asr` | HTTP 异步 | ✅ 需要 HTTP/OSS URL |

### 2. 前端 WebM 必须转码，别绕

浏览器 MediaRecorder 只能产出 WebM。fun-asr-realtime 支持的格式没有 WebM。所以**转码这一步绕不过去**。

虽然 WebM 底层编码是 Opus，但 `format="opus"` 要求裸 Opus 帧，WebM 前面有容器头。`format="webm"` 直接报 UNSUPPORTED_FORMAT。

最稳的方案：**ffmpeg 转标准 WAV**，这个格式所有 ASR 服务都支持。

### 3. Windows 上的 ffmpeg 调用姿势

```python
# ❌ Windows 上会报 NotImplementedError
proc = await asyncio.create_subprocess_exec("ffmpeg", ...)

# ✅ 正确：丢线程池
proc = await asyncio.to_thread(subprocess.run, [...])
```

### 4. 别自己拼 HTTP 请求

除非你有最新的官方 API 文档，而且确认了完整的请求体 Schema（包括所有必填字段和枚举值），否则**不要自己拼 HTTP 请求**。用 SDK，哪怕 SDK 难用，也比手拼的成功率高十倍。

### 5. 百炼控制台 ≠ 你的后端

控制台帮你做了很多"隐藏工作"：格式转换、权限管理、模型选择。当你把同样的流程搬到后端时，这些都要你自己实现。**在控制台测试通过只是第一步，离后端跑通还差一个"理解了全部隐藏细节"。**

### 6. 我的完整错误对照表

| 错误信息 | 原因 | 怎么修 |
|---------|------|-------|
| `FILE_403_FORBIDDEN` | OSS 权限不对 | 别用 OssUtils + Transcription 方案 |
| `SERVER_ERROR` | OSS URL 格式有问题 | 同上 |
| `ModelNotFound: fun-asr` | Recognition 类用错了模型名 | 改用 `fun-asr-realtime` |
| `UNSUPPORTED_FORMAT` | WebM 格式不被支持 | ffmpeg 转 WAV |
| `NO_VALID_AUDIO_ERROR` | 传了 WebM 但声明的格式是 opus | 同上 |
| `NotImplementedError` | Windows 异步子进程 | 改用 `asyncio.to_thread` |

---

## 结语

一周时间，从控制台秒出结果到后端终于吐出"喂，你好，你是谁？"，中间经历了：权限错误、URL 拼错、模型名搞混、格式不兼容、Windows 异步子进程报错……每一个坑都踩得实实在在。

如果你也在做类似的事情，希望这篇文章能帮你绕开我踩过的这些坑。说到底，这种"看起来应该很简单"的集成，往往就是因为这种"应该"的心态，才让我们踩得最深。

控制台能跑 ≠ 你后端能跑。这句话，与所有做集成的开发者共勉。

---

👨‍💻 博客：[https://an3035.github.io/](https://an3035.github.io/)（国外）/ [https://an-96x.pages.dev](https://an-96x.pages.dev)（国内，可无代理访问）

🏷️ `FastAPI` `阿里云百炼` `语音识别` `踩坑记录` `ffmpeg` `fun-asr`
