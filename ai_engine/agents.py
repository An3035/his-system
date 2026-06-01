"""
agents.py — LangGraph 多智能体定义

5 个专业智能体：
  1. Router Agent    — 路由分发（分类用户意图）
  2. Consultant      — 日常健康咨询
  3. Medical Agent   — 诊疗/处方/患者信息（可调用工具）
  4. Science Agent   — 健康科普/医疗政策（可检索 RAG 知识库）
  5. Tool Agent      — HIS 系统内部工具执行

每个 Agent 由 system prompt + tool list 定义，node 函数在 graph.py 中实现。
"""

from __future__ import annotations

from typing import Callable

from loguru import logger

# ── HIS 系统提示词（与原有 ai_service.py 保持一致） ──────────

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

# ── Agent System Prompts ─────────────────────────────────────

ROUTER_SYSTEM_PROMPT = """你是一个智能路由助手。你的任务是根据用户的问题，判断应该由哪个专业智能体处理。

可选的智能体：
1. **tool**（工具智能体）：用户需要查询系统数据时使用，例如查询挂号统计、药品库存、患者信息、处方信息，以及「查一下」「查查」「查询」「统计」「多少」等数据类问题
2. **medical**（医疗智能体）：症状分析、诊断建议、治疗方案、药物相互作用分析、病历摘要等诊疗相关问题
3. **science**（科普智能体）：健康科普知识、医疗政策法规、疾病预防保健知识
4. **consult**（咨询智能体）：日常健康咨询、普通问答、闲聊、系统操作咨询

判断原则：
- 如果问题是查询系统中的数据（挂号数、药品库存、患者信息、处方信息等），请选择 **tool**
- 如果问题是分析症状、诊断或治疗方案，请选择 **medical**
- 如果问题是了解健康知识或政策，请选择 **science**
- 其他情况选择 **consult**

请仅输出一个词表示分类结果，不要输出其他内容。
如果问题涉及多个方面，选择最主要的一个。
"""

CONSULTANT_SYSTEM_PROMPT = """你是一位健康咨询助手，隶属于医院信息系统（HIS）。

你的职责：
- 回答日常健康相关问题
- 解答医院信息系统操作问题
- 提供一般性的医疗信息咨询

注意：
- 所有回答仅供参考，不替代专业医师判断
- 回答简洁专业，使用中文
- 不确定的问题请如实告知用户
"""

MEDICAL_SYSTEM_PROMPT = """你是一位医疗智能助手，可以访问医院信息系统（HIS）中的患者数据。

你的能力：
1. 分析患者症状，提供初步诊断参考
2. 审核处方药物相互作用和剂量合理性
3. 生成患者病历摘要
4. 查询药品信息和用法用量

如果需要查询系统中的患者信息、药品信息、处方信息等具体数据，请引导用户使用数据查询工具。
如果需要分析药物相互作用，直接在回答中进行分析。

注意：
- 所有医疗建议仅供参考，不替代专业医师判断
- 患者隐私保护优先，不要泄露不必要的患者信息
- 回答简洁专业，使用中文
"""

SCIENCE_SYSTEM_PROMPT = """你是一位健康科普助手，专注于医疗健康知识传播。

你的职责：
- 用通俗易懂的语言解释医学知识和健康概念
- 回答疾病预防、保健养生相关问题
- 解读医疗政策和法规
- 必要时检索知识库获取专业信息

注意：
- 引用知识库内容时注明出处
- 回答科学严谨，避免误导
- 使用中文，语言通俗易懂
"""

TOOL_SYSTEM_PROMPT = """你是一个 HIS 系统工具调用助手。你负责执行具体的系统工具函数，并用自然语言回复用户。

可用工具：
1. today_registrations — 查询今日挂号患者数量（按挂号类型分类统计），无需参数
2. drug_inventory — 根据药品名称查询药房和药库库存信息
3. patient_info — 根据患者姓名或病历号查询患者基本信息
4. prescription_info — 根据处方编号查询处方详细信息（含药品明细）
5. search_knowledge_base(query) — 检索医疗知识库
6. analyze_drug_interaction(drug_names) — 分析药物相互作用
7. interpret_report_data(report_type, data) — 解读报表数据
8. summarize_patient_history(patient_data) — 生成患者病历摘要

工具执行后，请将结果以简洁、自然语言的方式返回给用户。
对于数值型数据，用清晰的格式呈现关键信息。
"""


# ── Agent 定义 ──────────────────────────────────────────────

class AgentDef:
    """智能体定义。"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        description: str,
        tools: list[Callable] | None = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.description = description
        self.tools = tools or []

    def __repr__(self) -> str:
        return f"Agent({self.name})"


# ── 工具函数 ────────────────────────────────────────────────

# 旧有工具（通过 ai_service.py 实现）

async def tool_search_kb(query: str) -> list[dict]:
    """检索医疗知识库（RAG）。"""
    from rag_engine import get_rag_engine
    return get_rag_engine().search(query, top_k=3)


async def tool_drug_interaction(drug_names: list[str]) -> str:
    """分析药物相互作用。"""
    from ai_service import analyze_drug_interaction as _interact
    return await _interact(drug_names)


async def tool_interpret_report(report_type: str, data: dict) -> str:
    """解读报表数据。"""
    from ai_service import interpret_report_data as _interpret
    return await _interpret(report_type, data)


async def tool_summarize_patient(patient_data: dict) -> str:
    """生成患者病历摘要。"""
    from ai_service import summarize_patient_history as _summarize
    return await _summarize(patient_data)


# 新 HIS 数据查询工具（委托 tools.py，用于传统 TOOL_REGISTRY 回退路径）

async def tool_today_registrations(user_message: str = "") -> str:
    """查询今日挂号统计（包装器，用于 TOOL_REGISTRY 兼容）。"""
    from ai_engine.tools import today_registrations as _tool
    return await _tool(user_info=None)


async def tool_drug_inventory(user_message: str = "") -> str:
    """查询药品库存（包装器，用于 TOOL_REGISTRY 兼容）。"""
    from ai_engine.tools import drug_inventory as _tool
    # 旧路径无法提取参数，返回提示
    return "请使用结构化工具调用模式，需要提供药品名称参数。"


async def tool_patient_info(user_message: str = "") -> str:
    """查询患者信息（包装器，用于 TOOL_REGISTRY 兼容）。"""
    from ai_engine.tools import patient_info as _tool
    return "请使用结构化工具调用模式，需要提供患者姓名或病历号参数。"


async def tool_prescription_info(user_message: str = "") -> str:
    """查询处方信息（包装器，用于 TOOL_REGISTRY 兼容）。"""
    from ai_engine.tools import prescription_info as _tool
    return "请使用结构化工具调用模式，需要提供处方编号参数。"


TOOL_REGISTRY: dict[str, Callable] = {
    "search_knowledge_base": tool_search_kb,
    "analyze_drug_interaction": tool_drug_interaction,
    "interpret_report_data": tool_interpret_report,
    "summarize_patient_history": tool_summarize_patient,
    "today_registrations": tool_today_registrations,
    "drug_inventory": tool_drug_inventory,
    "patient_info": tool_patient_info,
    "prescription_info": tool_prescription_info,
}

# ── 统一工具元数据（供 Graph 结构化调用） ─────────────────

TOOL_META: dict[str, dict] = {
    # 新：HIS 数据查询工具
    "today_registrations": {
        "description": "查询今日挂号患者数量（按挂号类型分类统计，含支付状态）",
        "params": {},
        "category": "统计查询",
        "structured": True,
    },
    "drug_inventory": {
        "description": "根据药品名称查询药房和药库库存信息",
        "params": {"drug_name": "药品名称（支持模糊匹配）"},
        "category": "药品管理",
        "structured": True,
    },
    "patient_info": {
        "description": "根据患者姓名或病历号查询患者基本信息（含联系方式）",
        "params": {"query": "患者姓名或病历号"},
        "category": "患者管理",
        "structured": True,
    },
    "prescription_info": {
        "description": "根据处方编号查询处方详细信息（含药品明细和患者信息）",
        "params": {"prescription_id": "处方编号"},
        "category": "处方管理",
        "structured": True,
    },
    # 旧有工具（非结构化，直接传用户消息）
    "search_knowledge_base": {
        "description": "检索医疗知识库",
        "params": {"query": "搜索关键词"},
        "category": "知识库",
        "structured": False,
    },
    "analyze_drug_interaction": {
        "description": "分析药物相互作用与配伍禁忌",
        "params": {"drug_names": "药品名称列表"},
        "category": "药学",
        "structured": False,
    },
    "interpret_report_data": {
        "description": "解读报表数据，提供管理建议",
        "params": {"report_type": "报表类型", "data": "数据字典"},
        "category": "管理",
        "structured": False,
    },
    "summarize_patient_history": {
        "description": "生成患者病历摘要",
        "params": {"patient_data": "患者数据字典"},
        "category": "医疗",
        "structured": False,
    },
}


# ── Agent 注册表 ────────────────────────────────────────────

AGENTS: dict[str, AgentDef] = {
    "router": AgentDef(
        name="router",
        system_prompt=ROUTER_SYSTEM_PROMPT,
        description="路由分发：分类用户意图",
    ),
    "consultant": AgentDef(
        name="consultant",
        system_prompt=CONSULTANT_SYSTEM_PROMPT,
        description="日常健康咨询与问答",
    ),
    "medical": AgentDef(
        name="medical",
        system_prompt=MEDICAL_SYSTEM_PROMPT,
        description="诊疗/处方/患者信息查询",
        tools=[tool_search_kb, tool_drug_interaction, tool_summarize_patient],
    ),
    "science": AgentDef(
        name="science",
        system_prompt=SCIENCE_SYSTEM_PROMPT,
        description="健康科普与医疗政策",
        tools=[tool_search_kb],
    ),
    "tool": AgentDef(
        name="tool",
        system_prompt=TOOL_SYSTEM_PROMPT,
        description="HIS 系统工具执行",
        tools=list(TOOL_REGISTRY.values()),
    ),
}


def get_agent(name: str) -> AgentDef:
    """通过名称获取 Agent 定义。"""
    agent = AGENTS.get(name)
    if not agent:
        logger.warning(f"未知 Agent: {name}，回退到 consultant")
        return AGENTS["consultant"]
    return agent


def classify_intent(user_message: str) -> str:
    """基于关键词的快速意图分类（作为 LLM 分类的后备和补充）。

    返回: "consult" | "medical" | "science" | "tool"
    """
    msg = user_message.lower()

    # 工具类（数据查询、统计、报表、信息检索）
    tool_keywords = [
        "统计", "报表", "数据", "趋势", "排行", "多少", "数量",
        "收入", "挂号", "库存", "查询", "查一下", "查查", "查",
        "分析数据", "今日", "信息", "患者信息", "药品库存",
        "处方信息", "处方编号",
    ]
    # 医疗类（诊疗、症状、药物、处方）
    medical_keywords = [
        "症状", "诊断", "治疗", "处方", "药物", "药品",
        "病历", "患者", "手术", "检查", "剂量", "相互作用",
        "发烧", "咳嗽", "疼痛", "感染",
    ]
    # 科普类（健康知识、政策）
    science_keywords = [
        "科普", "知识", "政策", "预防", "保健", "养生",
        "疾病", "了解", "什么是", "怎么回事", "如何预防",
        "怎么治", "注意事项",
    ]

    for kw in tool_keywords:
        if kw in msg:
            return "tool"
    for kw in medical_keywords:
        if kw in msg:
            return "medical"
    for kw in science_keywords:
        if kw in msg:
            return "science"

    return "consult"
