from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from prompts.system_prompts import CREDIT_DECIDER_PROMPT
from schemas import DecisionResult
from pydantic import ValidationError

class CreditDeciderAgent(BaseAgent):
    def __init__(self, llm_client=None):
        super().__init__(name="授信决策智能体", role="credit_decider", llm_client=llm_client)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        user_data = context.get('user_data', {})
        credit_history = context.get('credit_history', {})
        application = context.get('application', {})
        profile = context.get('profile', {})
        risk = context.get('risk', {})

        if self.llm_client and self.llm_client.enabled:
            prompt = f"""
请做出最终授信决策，输出 JSON 格式。

【用户】{user_data.get('name')}，月收入{user_data.get('monthly_income')}元
【申请金额】{application.get('amount', 0)}元，用途"{application.get('purpose', '')}"
【画像】{profile}
【风险评估】{risk}
【信用历史】{credit_history if credit_history else '无'}

输出格式：
{{
    "decision": "APPROVED/REJECTED",
    "final_amount": 整数,
    "interest_rate_suggestion": "年化利率范围，如'12%-18%'",
    "credit_line_usage_suggestion": "额度使用建议",
    "decision_reasoning": "中文原因",
    "approval_duration_days": 整数天数
}}
"""
            resp = self._call_llm(prompt, CREDIT_DECIDER_PROMPT)
            result = self._parse_json_response(resp)
            try:
                validated = DecisionResult(**result)
                return AgentResult(
                    status="SUCCESS",
                    data=validated.model_dump()
                )
            except ValidationError as e:
                print(f"LLM 决策结果格式错误: {e}，使用规则引擎")
                return self._rule_based_decision(user_data, credit_history, application, profile, risk)
        else:
            return self._rule_based_decision(user_data, credit_history, application, profile, risk)

    def _rule_based_decision(self, user_data, credit_history, application, profile, risk) -> AgentResult:
        income = user_data.get('monthly_income', 0)
        risk_level = risk.get('risk_level', 'MEDIUM')
        risk_score = risk.get('final_risk_score', 0)
        requested = application.get('amount', 0)

        if risk_level == "HIGH" or risk_score < 450:
            result = {
                "decision": "REJECTED",
                "final_amount": 0,
                "interest_rate_suggestion": "N/A",
                "credit_line_usage_suggestion": "不适用",
                "decision_reasoning": f"风险等级{risk_level}，信用评分{risk_score}未达门槛",
                "approval_duration_days": 0,
                "decision_detail": {}
            }
        else:
            ratio = self._determine_ratio(profile)
            if risk_level == "MEDIUM" and risk_score >= 500:
                amount = min(int(income * ratio), 15000)
                if requested > 0 and amount > requested:
                    amount = requested
                result = {
                    "decision": "APPROVED",
                    "final_amount": amount,
                    "interest_rate_suggestion": "15%-20%",
                    "credit_line_usage_suggestion": "建议用于合理消费需求",
                    "decision_reasoning": "中等风险但画像有效支撑",
                    "approval_duration_days": 30,
                    "decision_detail": {}
                }
            elif risk_level == "LOW" and risk_score >= 600:
                amount = min(int(income * ratio * 1.2), 30000)
                if requested > 0 and amount > requested:
                    amount = requested
                result = {
                    "decision": "APPROVED",
                    "final_amount": amount,
                    "interest_rate_suggestion": "8%-15%",
                    "credit_line_usage_suggestion": "适用于多种消费场景",
                    "decision_reasoning": "低风险用户，职业稳定",
                    "approval_duration_days": 45,
                    "decision_detail": {}
                }
            else:
                result = {
                    "decision": "REJECTED",
                    "final_amount": 0,
                    "interest_rate_suggestion": "N/A",
                    "credit_line_usage_suggestion": "不适用",
                    "decision_reasoning": f"风险评估不足，分数{risk_score}",
                    "approval_duration_days": 0,
                    "decision_detail": {}
                }
        try:
            validated = DecisionResult(**result)
            return AgentResult(
                status="SUCCESS",
                data=validated.model_dump()
            )
        except ValidationError as e:
            print(f"规则引擎决策输出格式错误: {e}")
            default = {
                "decision": "REJECTED",
                "final_amount": 0,
                "interest_rate_suggestion": "N/A",
                "credit_line_usage_suggestion": "不适用",
                "decision_reasoning": "内部错误，拒绝",
                "approval_duration_days": 0,
                "decision_detail": {}
            }
            return AgentResult(
                status="FAILURE",
                data=default,
                error_message=str(e)
            )

    def _determine_ratio(self, profile: Dict) -> float:
        strengths = profile.get('credit_strengths', [])
        weaknesses = profile.get('credit_weaknesses', [])
        ratio = 0.5
        if any('工作勤奋' in s or '稳定' in s for s in strengths): ratio += 0.2
        if any('服务年限' in s or '从业' in s for s in strengths): ratio += 0.3
        if any('学历' in s for s in strengths): ratio += 0.2
        if any('offer' in s for s in strengths): ratio += 0.2
        if len(weaknesses) > 2: ratio -= 0.2
        elif weaknesses: ratio -= 0.1
        return max(0.3, min(1.0, ratio))