from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from prompts.system_prompts import RISK_ASSESSOR_PROMPT
from schemas import RiskResult
from pydantic import ValidationError

class RiskAssessorAgent(BaseAgent):
    def __init__(self, llm_client=None):
        super().__init__(name="风险评估智能体", role="risk_assessor", llm_client=llm_client)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        user_data = context.get('user_data', {})
        credit_history = context.get('credit_history', {})
        application = context.get('application', {})
        profile = context.get('profile', {})
        aggregated = context.get('aggregated_data', {})

        if self.llm_client and self.llm_client.enabled:
            prompt = f"""
请评估用户的信用风险，输出 JSON 格式。

【用户】{user_data.get('name')}，职业{user_data.get('occupation')}，月收入{user_data.get('monthly_income')}
【信用历史】{credit_history if credit_history else '无'}
【申请金额】{application.get('amount', 0)} 元，用途"{application.get('purpose', '')}"
【画像摘要】{profile}
【聚合数据】{aggregated}

输出格式：
{{
    "base_score": 整数(0-750),
    "risk_adjustment": 整数(-100到+50),
    "final_risk_score": 整数(0-750),
    "risk_level": "LOW/MEDIUM/HIGH",
    "risk_factors": ["因素1", "因素2"],
    "fraud_indicators": []
}}
"""
            resp = self._call_llm(prompt, RISK_ASSESSOR_PROMPT)
            result = self._parse_json_response(resp)
            try:
                validated = RiskResult(**result)
                return AgentResult(
                    status="SUCCESS",
                    data=validated.model_dump()
                )
            except ValidationError as e:
                print(f"LLM 风险结果格式错误: {e}，使用规则引擎")
                return self._rule_based_risk(user_data, credit_history, application, profile, aggregated)
        else:
            return self._rule_based_risk(user_data, credit_history, application, profile, aggregated)

    def _rule_based_risk(self, user_data, credit_history, application, profile, aggregated) -> AgentResult:
        rec_range = profile.get('recommended_score_range', (500, 600))
        if isinstance(rec_range, list):
            base = rec_range[0] if rec_range else 550
        else:
            base = rec_range[0] if rec_range else 550
        adjustment = 0
        risk_factors = []
        fraud = []

        occupation = user_data.get('occupation', '')
        stability = {'外卖骑手': -20, '网约车司机': -10, '自由摄影师': -25, '职场新人/广告策划': +10, '应届毕业生': -15}
        if occupation in stability:
            adjustment += stability[occupation]
            risk_factors.append(f"职业{occupation}稳定性调整{stability[occupation]}")

        amount = application.get('amount', 0)
        income = user_data.get('monthly_income', 1)
        ratio = amount / income
        if ratio > 1.0:
            adjustment -= 30
            risk_factors.append("申请金额超过月收入")
            if ratio > 2.0:
                adjustment -= 40
                fraud.append("金额收入严重不匹配")
        elif ratio > 0.5:
            adjustment -= 10
        else:
            adjustment += 10

        purpose = application.get('purpose', '').lower()
        if any(k in purpose for k in ['电动车', '电脑', '设备', '工作需要', '升级', '工具']):
            adjustment += 15
            risk_factors.append("生产性消费")

        if credit_history and credit_history.get('overdue_days', 0) > 0:
            overdue = credit_history['overdue_days']
            adjustment -= min(60, overdue * 2)
            risk_factors.append(f"{overdue}天逾期记录")
        elif credit_history:
            adjustment += 10

        workload = aggregated.get('alternative_data', {}).get('workload_intensity', 'MID')
        if workload == 'HIGH':
            adjustment += 15
        elif workload == 'LOW':
            adjustment -= 10

        final_score = base * 0.4 + 400 * 0.6 + adjustment
        final_score = max(300, min(750, final_score))
        if final_score >= 600:
            risk_level = "LOW"
        elif final_score >= 450:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        result = {
            "base_score": base,
            "risk_adjustment": adjustment,
            "final_risk_score": int(final_score),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "fraud_indicators": fraud,
        }
        try:
            validated = RiskResult(**result)
            return AgentResult(
                status="SUCCESS",
                data=validated.model_dump()
            )
        except ValidationError as e:
            print(f"规则引擎风险输出格式错误: {e}")
            default = {
                "base_score": 400,
                "risk_adjustment": 0,
                "final_risk_score": 400,
                "risk_level": "HIGH",
                "risk_factors": ["规则引擎异常"],
                "fraud_indicators": []
            }
            return AgentResult(
                status="FAILURE",
                data=default,
                error_message=str(e)
            )