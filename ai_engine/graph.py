"""
graph.py — LangGraph StateGraph 多智能体协作流程

用户消息 → Router Agent → 分类意图 → 路由到专业 Agent → 生成回复
                                                │
                                    Medical/Tool Agent
                                        ↓ 需要工具?
                                    结构化工具调用
                                        ↓
                                  自然语言+可选 RAG 混合回复

支持：
- 结构化工具调用（LLM 选工具+提取参数）
- Admin 权限校验
- 工具结果 + RAG 知识库混合回复
"""

from __future__ import annotations

import json
import re
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from dashscope import Generation
from loguru import logger

from ai_engine.agents import (
    HIS_SYSTEM_PROMPT,
    TOOL_META,
    TOOL_REGISTRY,
    AgentDef,
    classify_intent,
    get_agent,
)
from ai_engine.tools import TOOL_DEFINITIONS as _STRUCTURED_TOOLS
from config import settings

# ── State 定义 ──────────────────────────────────────────────


class AgentState(TypedDict):
    """LangGraph 状态（贯穿整个 Agent 流程）。"""

    # 输入
    user_message: str  # 用户当前消息
    history: List[dict]  # 历史对话
    context_type: str  # general / patient / drug / report
    context_data: Optional[dict]  # 上下文数据
    his_system_prompt: str  # HIS 系统提示词

    # 用户认证
    current_user: Optional[dict]  # {"id": int, "role": str, "name": str}

    # 路由
    user_intent: str  # consult / medical / science / tool
    routed_agent: str  # 实际路由到的 Agent 名称

    # 工具调用
    tool_calls: List[dict]  # 需要执行的工具调用记录
    tool_results: List[dict]  # 工具执行结果

    # 输出
    final_response: str  # 最终回复
    error: Optional[str]  # 错误信息


def make_initial_state(
    user_message: str,
    history: List[dict] | None = None,
    context_type: str = "general",
    context_data: dict | None = None,
    current_user: dict | None = None,
) -> AgentState:
    """创建初始状态。"""
    return {
        "user_message": user_message,
        "history": history or [],
        "context_type": context_type,
        "context_data": context_data,
        "his_system_prompt": HIS_SYSTEM_PROMPT,
        "current_user": current_user,
        "user_intent": "consult",
        "routed_agent": "",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "error": None,
    }


# ── Dashscope 调用函数 ─────────────────────────────────────

_MAX_HISTORY_TURNS = 10


async def _call_dashscope(
    messages: List[dict],
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """调用 Dashscope API（与原有 ai_service.py 相同的方式）。"""
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    try:
        response = Generation.call(
            model=settings.DASHSCOPE_MODEL,
            messages=full_messages,
            result_format="message",
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            logger.error(f"Dashscope error: {response.code} - {response.message}")
            return f"AI服务暂时不可用（{response.code}），请稍后重试。"
    except Exception as e:
        logger.exception(f"AI调用异常: {e}")
        return "AI服务异常，请联系管理员。"


# ── 结构化工具调用 ─────────────────────────────────────────


def _build_tool_prompt(user_message: str) -> str:
    """构建工具选择提示词，让 LLM 选择工具并提取参数。"""
    lines = ["你是一个 HIS 工具调用助手。根据用户的问题，选择最合适的工具并提取参数。", ""]
    lines.append("可用工具：")

    for name, meta in TOOL_META.items():
        desc = meta.get("description", "")
        params = meta.get("params", {})
        if params:
            param_desc = ", ".join(f"{k}={v}" for k, v in params.items())
            lines.append(f"- {name}: {desc} | 参数: {{{param_desc}}}")
        else:
            lines.append(f"- {name}: {desc}（无需参数）")

    lines.append("")
    lines.append("请以 JSON 格式输出（只输出 JSON，不要其他文字）：")
    lines.append("""{
  "tool": "工具名称",
  "reason": "选择该工具的简短理由",
  "params": {
    "参数名1": "参数值1",
    "参数名2": "参数值2"
  }
}""")
    lines.append(
        '如果不需要调用任何工具，输出：{"tool": "none", "reason": "不需要调用工具", "params": {}}'
    )
    lines.append("")
    lines.append(f"用户问题：{user_message}")
    return "\n".join(lines)


async def _execute_structured_tool(
    tool_name: str, params: dict, user_info: dict | None
) -> str:
    """执行结构化工具调用。"""
    # 优先使用结构化工具（tools.py）
    if tool_name in _STRUCTURED_TOOLS:
        tool_fn = _STRUCTURED_TOOLS[tool_name]["fn"]
        result = await tool_fn(user_info=user_info, **params)
        return result

    # 回退到旧有工具（TOOL_REGISTRY，非结构化）
    if tool_name in TOOL_REGISTRY:
        tool_fn = TOOL_REGISTRY[tool_name]
        # 旧工具直接传用户消息
        result = await tool_fn(user_message=params.get("query", ""))
        if isinstance(result, list):
            # RAG 工具返回列表，格式化为文本
            formatted = "\n".join(
                f"- [{r.get('document_title', '知识')}] {r.get('content', '')[:200]}"
                for r in result
            )
            return f"知识库检索结果：\n{formatted}" if formatted else "知识库未找到相关信息。"
        return str(result)

    logger.warning(f"未知工具: {tool_name}")
    return ""


async def _search_rag_for_context(user_message: str) -> str:
    """检索 RAG 知识库获取补充信息，如果失败则返回空字符串。"""
    try:
        from rag_engine import get_rag_engine

        rag_results = get_rag_engine().search(user_message, top_k=2)
        if rag_results:
            kb_context = "\n".join(
                f"[知识] {r['content'][:300]}"
                for r in rag_results
            )
            return kb_context
    except Exception as e:
        logger.warning(f"RAG 知识库检索失败（非致命）: {e}")
    return ""


async def _format_final_response(
    tool_result: str, rag_context: str, user_message: str
) -> str:
    """组装工具结果 + RAG 知识为最终自然语言回复。"""
    if tool_result.startswith("⚠️"):
        # 权限不足，直接返回
        return tool_result

    result_parts = [tool_result]

    if rag_context:
        result_parts.append(
            "\n\n💡 相关知识参考：\n" + rag_context
        )

    combined = "\n".join(result_parts)

    # 用 LLM 将结果润色为自然语言（仅当内容较长时）
    if len(combined) > 500:
        polish_prompt = (
            f"以下是根据用户问题「{user_message}」查询到的系统数据结果。\n"
            f"请用自然语言将它们组织成一段清晰的回复，"
            f"保留所有关键数据，去掉 JSON 风格结构，"
            f"使内容读起来像人写的分析报告。\n\n"
            f"{combined}"
        )
        polished = await _call_dashscope(
            messages=[{"role": "user", "content": polish_prompt}],
            system_prompt="你是一个 HIS 数据汇报助手。将数据结果整理成自然语言。",
            temperature=0.5,
            max_tokens=1000,
        )
        return polished.strip() or combined

    return combined


def _parse_tool_json(response: str) -> dict | None:
    """从 LLM 响应中解析工具调用 JSON。"""
    # 尝试直接解析
    text = response.strip()
    # 提取 ```json 块
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试用正则提取 { }
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return None


# ── Node 函数 ───────────────────────────────────────────────


async def router_node(state: AgentState) -> AgentState:
    """路由节点：分类用户意图。

    先用关键词快速分类，再用 LLM 确认（对边界情况）。
    """
    user_message = state["user_message"]

    # 关键词快速分类
    intent = classify_intent(user_message)

    # 用 LLM 做精确分类（对于边界情况）
    if intent == "consult":
        prompt = (
            f"用户消息：{user_message}\n\n"
            f"请将上述消息分类为以下之一：tool, medical, science, consult\n\n"
            f"分类规则：\n"
            f"- tool = 查询系统数据，如挂号统计、药品库存、患者信息、处方信息等\n"
            f"- medical = 分析症状、诊断、治疗、药物相互作用、处方审核\n"
            f"- science = 健康科普、疾病知识、医疗政策\n"
            f"- consult = 日常咨询、闲聊、系统操作问题\n\n"
            f"仅输出一个词。"
        )
        llm_intent = await _call_dashscope(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10,
        )
        llm_intent = llm_intent.strip().lower()
        if llm_intent in ("medical", "science", "tool"):
            intent = llm_intent

    state["user_intent"] = intent
    state["routed_agent"] = intent
    logger.info(f"🔀 路由决策: {intent} (消息: {user_message[:40]}...)")
    return state


async def consultant_node(state: AgentState) -> AgentState:
    """咨询节点：处理日常健康咨询和问答。"""
    agent = get_agent("consultant")
    system = agent.system_prompt + "\n\n" + state["his_system_prompt"]

    messages = []
    for msg in state["history"][-_MAX_HISTORY_TURNS * 2:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": state["user_message"]})

    reply = await _call_dashscope(messages, system_prompt=system)
    state["final_response"] = reply
    return state


async def medical_node(state: AgentState) -> AgentState:
    """医疗节点：处理诊疗/处方/患者信息相关请求，必要时调用工具。"""
    agent = get_agent("medical")
    system = agent.system_prompt + "\n\n" + state["his_system_prompt"]

    # 注入上下文
    if state["context_data"] and state["context_type"] != "general":
        ctx_text = (
            f"\n【当前操作上下文 - {state['context_type']}】\n"
            f"{json.dumps(state['context_data'], ensure_ascii=False, indent=2)}"
        )
        system += ctx_text

    messages = []
    for msg in state["history"][-_MAX_HISTORY_TURNS * 2:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": state["user_message"]})

    reply = await _call_dashscope(messages, system_prompt=system)
    state["final_response"] = reply
    return state


async def science_node(state: AgentState) -> AgentState:
    """科普节点：处理健康科普/医疗政策查询，可选检索 RAG 知识库。"""
    agent = get_agent("science")

    # 判断是否需要检索知识库
    kb_prompt = (
        f"用户消息：{state['user_message']}\n\n"
        f"判断是否需要检索医疗知识库来回答这个问题。"
        f"如果问题涉及专业知识，输出 YES 否则 NO。仅输出一个词。"
    )
    need_kb = await _call_dashscope(
        messages=[{"role": "user", "content": kb_prompt}],
        temperature=0.3,
        max_tokens=5,
    )

    kb_context = ""
    if need_kb.strip().upper() == "YES":
        kb_context = await _search_rag_for_context(state["user_message"])

    system = agent.system_prompt + "\n\n" + state["his_system_prompt"]
    if kb_context:
        system += "\n\n【知识库检索结果】\n" + kb_context

    messages = []
    for msg in state["history"][-_MAX_HISTORY_TURNS * 2:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": state["user_message"]})

    reply = await _call_dashscope(messages, system_prompt=system)
    state["final_response"] = reply
    return state


async def tool_node(state: AgentState) -> AgentState:
    """工具节点：结构化工具调用 + 可选 RAG 混合模式。

    流程：
    1. LLM 选择工具 + 提取参数
    2. 执行工具（含 admin 权限校验）
    3. 可选检索 RAG 知识库补充
    4. 组装自然语言回复
    """
    user_message = state["user_message"]
    user_info = state.get("current_user")

    # ── 第一步：LLM 选择工具 ──
    tool_prompt = _build_tool_prompt(user_message)
    llm_response = await _call_dashscope(
        messages=[{"role": "user", "content": tool_prompt}],
        temperature=0.3,
        max_tokens=200,
    )

    decision = _parse_tool_json(llm_response)
    tool_name = decision.get("tool", "none") if decision else "none"

    if tool_name and tool_name != "none" and tool_name in _STRUCTURED_TOOLS:
        # ── 第二步：执行结构化工具 ──
        params = decision.get("params", {}) if decision else {}
        logger.info(f"🔧 结构化工具调用: {tool_name}, params={params}")

        tool_result = await _execute_structured_tool(
            tool_name, params, user_info
        )

        # ── 第三步（可选）：RAG 知识库补充 ──
        rag_context = ""
        # 对药品/患者查询补充知识库信息
        if tool_name in ("drug_inventory", "patient_info"):
            rag_context = await _search_rag_for_context(user_message)

        # ── 第四步：组装最终回复 ──
        state["final_response"] = await _format_final_response(
            tool_result, rag_context, user_message
        )
        state["tool_calls"] = [{"tool": tool_name, "params": params}]
        state["tool_results"] = [{"tool": tool_name, "result": tool_result}]
        return state

    # ── 尝试旧有工具（TOOL_REGISTRY 回退） ──
    if tool_name and tool_name in TOOL_REGISTRY:
        logger.info(f"🔧 旧工具调用（回退）: {tool_name}")
        try:
            tool_fn = TOOL_REGISTRY[tool_name]
            result = await tool_fn(user_message)
            if isinstance(result, list):
                formatted = "\n".join(
                    f"- {r.get('content', '')[:200]}"
                    for r in result
                )
                rep = f"知识库检索结果：\n{formatted}"
            else:
                rep = str(result)

            # 组装回复
            agent = get_agent("tool")
            system = agent.system_prompt + "\n\n" + state["his_system_prompt"]
            system += f"\n\n【工具调用结果 - {tool_name}】\n{rep}"

            messages = [{"role": "user", "content": user_message}]
            reply = await _call_dashscope(messages, system_prompt=system)
            state["final_response"] = reply
            state["tool_calls"] = [{"tool": tool_name, "params": {}}]
            state["tool_results"] = [{"tool": tool_name, "result": rep}]
            return state
        except Exception as e:
            logger.error(f"旧工具执行失败: {e}")

    # ── 没有匹配工具，回退到咨询 Agent ──
    logger.info("🔀 工具节点无匹配工具，回退到咨询")
    state["user_intent"] = "consult"
    return await consultant_node(state)


# ── 条件边 ─────────────────────────────────────────────────


def route_by_intent(state: AgentState) -> str:
    """根据意图路由到对应的 Agent。"""
    return state.get("user_intent", "consult")


# ── Graph 构建 ──────────────────────────────────────────────

_agent_executor = None


def build_graph():
    """构建 LangGraph StateGraph。"""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node("router", router_node)
    workflow.add_node("consultant", consultant_node)
    workflow.add_node("medical", medical_node)
    workflow.add_node("science", science_node)
    workflow.add_node("tool", tool_node)

    # 设置入口
    workflow.set_entry_point("router")

    # 条件边：根据意图路由
    workflow.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "consult": "consultant",
            "medical": "medical",
            "science": "science",
            "tool": "tool",
        },
    )

    # 所有叶子节点 → END
    workflow.add_edge("consultant", END)
    workflow.add_edge("medical", END)
    workflow.add_edge("science", END)
    workflow.add_edge("tool", END)

    return workflow.compile()


def get_agent_executor():
    """获取 LangGraph agent executor 单例。"""
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = build_graph()
        logger.info("🤖 LangGraph 多智能体系统已初始化（支持结构化工具+混合RAG）")
    return _agent_executor
