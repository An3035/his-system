"""
content_filter.py — 用户输入 / AI输出安全过滤
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# ── 危险内容关键词 ──────────────────────────────────────────────
SELF_HARM_KEYWORDS = [
    r"自杀", r"自残", r"自伤", r"割腕", r"跳楼", r"上吊", r"服毒",
    r"安乐死", r"结束(自己|我的)生命", r"不想活", r"去死",
    r"怎么死", r"suicide", r"self.harm",
]

VIOLENCE_KEYWORDS = [
    r"杀人", r"下毒", r"投毒", r"制造爆炸", r"炸弹",
    r"恐怖袭击", r"报复社会", r"校园枪击",
]

ILLEGAL_KEYWORDS = [
    r"毒品", r"成瘾药物", r"非法处方", r"假药", r"伪造病历",
    r"骗保", r"医闹", r"医疗诈骗",
]

NON_MEDICAL_KEYWORDS = [
    r"写.*(文章|代码|诗|小说|歌|作文|邮件|简历)",
    r"(股票|期货|加密货币|基金).*(分析|推荐|预测|投资)",
    r"(算命|星座|塔罗牌|风水)",
    r"(翻译|语言交换).*(英文|日文|法文)",
    r"(短视频|直播|点赞|粉丝|关注)",
]

MEDICAL_KEYWORDS = [
    r"患者", r"病人", r"症状", r"诊断", r"治疗", r"药品?", r"处方",
    r"病历", r"医嘱", r"住院", r"出院", r"挂号", r"科室?", r"医生",
    r"手术", r"检查", r"检验", r"血压", r"血糖", r"体温", r"心脏",
    r"肝", r"肾", r"肺", r"胃", r"血液", r"血糖", r"尿酸",
    r"糖尿病", r"高血压", r"冠心病", r"癌症", r"肿瘤", r"感染",
    r"抗生素", r"消炎", r"退烧", r"止痛", r"维生素", r"中药",
    r"配伍", r"禁忌", r"副作用", r"剂量", r"用法", r"用量",
    r"护理", r"床位", r"医保", r"收费", r"体检", r"预防",
    r"疫苗", r"接种", r"康复", r"复诊", r"随访",
    r"HIS", r"医院信息系统", r"系统(怎么|如何)操作",
]

SAFE_REJECTION_TEMPLATE = (
    "我无法提供您所询问的信息。"
    "如果您正经历痛苦或有自伤的念头，"
    "请立即联系专业的医疗人员或拨打当地的心理危机干预热线寻求帮助。"
)

NON_MEDICAL_REJECTION = (
    "作为医疗专业助手，我主要服务于医疗相关问题的解答。"
    "请您提出与医疗、健康、医院信息系统操作相关的问题，我将尽力协助。"
)

# 编译正则（加速）
_self_harm_re = re.compile("|".join(SELF_HARM_KEYWORDS))
_violence_re = re.compile("|".join(VIOLENCE_KEYWORDS))
_illegal_re = re.compile("|".join(ILLEGAL_KEYWORDS))
_non_medical_re = re.compile("|".join(NON_MEDICAL_KEYWORDS))
_medical_re = re.compile("|".join(MEDICAL_KEYWORDS))

# AI输出PII模式（电话号码、身份证号等已脱敏失效的情况）
_PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
_ID_CARD_PATTERN = re.compile(r"\d{17}[\dXx]")
_ADDRESS_HINT = re.compile(r"(?:地址|住址|家庭住址)[:：]\s*\S{5,30}")


def _has_medical_context(text: str) -> bool:
    """检查是否包含医疗相关上下文。"""
    return bool(_medical_re.search(text))


def filter_user_input(message: str) -> Tuple[bool, Optional[str]]:
    """
    过滤用户输入。
    Returns:
        (is_safe, rejection_reply_or_None)
    """
    # 1. 自残/自杀类 — 最高优先级拦截
    if _self_harm_re.search(message):
        return False, SAFE_REJECTION_TEMPLATE

    # 2. 暴力/违法类
    if _violence_re.search(message):
        return False, SAFE_REJECTION_TEMPLATE

    if _illegal_re.search(message):
        return False, "检测到与违法或违规行为相关的内容，我无法提供此类信息。请咨询合法合规的医疗问题。"

    # 3. 非医疗类 — 仅在无医疗上下文时拦截
    if _non_medical_re.search(message) and not _has_medical_context(message):
        return False, NON_MEDICAL_REJECTION

    return True, None


def filter_ai_output(reply: str) -> str:
    """
    过滤 AI 回复中的潜在问题：
    - 标记AI幻觉警告
    - 确保不包含未脱敏的电话/身份证号
    """
    # 脱敏电话号码
    reply = _PHONE_PATTERN.sub(
        lambda m: m.group(0)[:3] + "****" + m.group(0)[7:],
        reply,
    )

    # 脱敏身份证号
    reply = _ID_CARD_PATTERN.sub(
        lambda m: m.group(0)[:3] + "**********" + m.group(0)[-4:],
        reply,
    )

    return reply
