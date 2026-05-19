from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from prompts.system_prompts import COMPLIANCE_AGENT_PROMPT
from schemas import ComplianceResult
from pydantic import ValidationError

class ComplianceAgent(BaseAgent):
    def __init__(self, llm_client=None):
        super().__init__(name="合规与反欺诈智能体", role="compliance_fraud", llm_client=llm_client)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        user_data = context.get('user_data', {})
        extra = user_data.get('extra_features', {})
        credit_history = context.get('credit_history', {})
        application = context.get('application', {})
        aggregated = context.get('aggregated_data', {})

        if self.llm_client and self.llm_client.enabled:
            prompt = f"""
请根据以下信息检测合规与欺诈风险，输出 JSON 格式。

【用户信息】
姓名：{user_data.get('name')}
职业：{user_data.get('occupation')}
月收入：{user_data.get('monthly_income')}
额外特征：{extra}

【信用历史】{credit_history if credit_history else '无'}
【申请金额】{application.get('amount', 0)} 元
【聚合数据】{aggregated}

输出格式：
{{
    "compliance_check_passed": true/false,
    "fraud_risk_score": 整数0-100,
    "issues_found": ["问题1", "问题2"],
    "fraud_signals_detected": ["信号1"],
    "recommended_action": "PASS/REVIEW/REJECT",
    "compliance_reasoning": "原因"
}}
"""
            resp = self._call_llm(prompt, COMPLIANCE_AGENT_PROMPT)
            result = self._parse_json_response(resp)
            try:
                validated = ComplianceResult(**result)
                missing = []
                if not user_data.get('monthly_income'):
                    missing.append("monthly_income")
                if missing:
                    return AgentResult(
                        status="NEED_MORE_INFO",
                        data=validated.model_dump(),
                        missing_fields=missing,
                        suggested_next_actions=["请补充收入证明"]
                    )
                return AgentResult(
                    status="SUCCESS",
                    data=validated.model_dump()
                )
            except ValidationError as e:
                print(f"LLM 合规结果格式错误: {e}，使用规则引擎")

        rule_result = self._rule_based_compliance(user_data, credit_history, application, aggregated)
        if rule_result.get("fraud_risk_score", 0) > 50 and not user_data.get('extra_features', {}).get('income_proof'):
            return AgentResult(
                status="NEED_MORE_INFO",
                data=rule_result,
                missing_fields=["收入证明文件"],
                suggested_next_actions=["上传近3个月银行流水"]
            )
        return AgentResult(
            status="SUCCESS",
            data=rule_result
        )

    def _rule_based_compliance(self, user_data, credit_history, application, aggregated):
        extra = user_data.get('extra_features', {})
        issues = []
        fraud_signals = []
        risk_weight = 0

        occupation = user_data.get('occupation', '')
        income = user_data.get('monthly_income', 0)
        expected_map = {
            '外卖骑手': (4000, 12000),
            '网约车司机': (6000, 15000),
            '自由摄影师': (3000, 20000),
            '职场新人/广告策划': (8000, 15000),
            '应届毕业生': (3000, 8000)
        }
        if occupation in expected_map:
            low, high = expected_map[occupation]
            if income < low - 1000 or income > high + 10000:
                issues.append(f"收入和职业不匹配")
                fraud_signals.append("income_mismatch")
                risk_weight += 30

        if credit_history:
            current_limit = credit_history.get('current_limit', 0)
            app_amount = application.get('amount', 0)
            if current_limit > 0 and app_amount > current_limit * 3:
                issues.append("申请金额远超现有额度")
                fraud_signals.append("excessive_application")
                risk_weight += 50

        if occupation == "外卖骑手":
            orders = extra.get('avg_daily_orders', 0)
            hours = extra.get('work_hours_per_day', 0)
            if orders > 0 and hours > 0:
                per_hour = orders / hours
                if per_hour < 2 or per_hour > 8:
                    issues.append("工作时长与订单量不匹配")
                    fraud_signals.append("workload_inconsistency")
                    risk_weight += 25

        fraud_score = min(risk_weight, 100)
        compliance_passed = len(issues) <= 2 and fraud_score < 60
        recommended = "REJECT" if (not compliance_passed or fraud_score > 70) else ("REVIEW" if fraud_score > 40 else "PASS")

        result = {
            "compliance_check_passed": compliance_passed,
            "fraud_risk_score": fraud_score,
            "issues_found": issues,
            "fraud_signals_detected": fraud_signals,
            "recommended_action": recommended,
            "compliance_reasoning": f"发现{len(issues)}个问题，欺诈风险评分{fraud_score}"
        }
        try:
            validated = ComplianceResult(**result)
            return validated.model_dump()
        except ValidationError as e:
            print(f"规则引擎输出格式错误: {e}")
            return {
                "compliance_check_passed": False,
                "fraud_risk_score": 100,
                "issues_found": ["内部错误"],
                "fraud_signals_detected": [],
                "recommended_action": "REJECT",
                "compliance_reasoning": "系统错误"
            }