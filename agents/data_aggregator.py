from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from schemas import AggregatedData

class DataAggregatorAgent(BaseAgent):
    """数据聚合智能体 - 负责收集和整合多源数据"""

    def __init__(self, llm_client=None):
        super().__init__(
            name="数据聚合智能体",
            role="data_aggregator",
            llm_client=llm_client
        )

    def process(self, context: Dict[str, Any]) -> AgentResult:
        """整合用户数据、信用历史和申请信息"""
        user_data = context.get('user_data', {})
        credit_history = context.get('credit_history', {})
        application = context.get('application', {})

        extra = user_data.get('extra_features', {})

        aggregated_data = {
            "demographic": {
                "age": user_data.get('age'),
                "occupation": user_data.get('occupation'),
                "income_bracket": self._determine_income_bracket(user_data.get('monthly_income', 0))
            },
            "credit_profile": {
                "existing_limit": credit_history.get('current_limit', 0),
                "has_credit_history": bool(credit_history and credit_history.get('current_limit', 0) > 0),
                "overdue_days": credit_history.get('overdue_days', 0),
                "avg_utilization": credit_history.get('average_utilization', 0)
            },
            "application_details": {
                "amount": application.get('amount', 0),
                "purpose": application.get('purpose', ''),
                "amount_vs_income_ratio": self._calculate_amount_vs_income(
                    application.get('amount', 0),
                    user_data.get('monthly_income', 1)
                )
            },
            "alternative_data": {
                "has_alternative_proofs": bool(extra.get('alternative_proofs')),
                "professional_certificates": extra.get('professional_certificates', []),
                "special_skills_mentioned": extra.get('special_skills', []),
                "workload_intensity": self._evaluate_workload_intensity(extra)
            },
            "raw_data_available": {
                "user_extra": extra,
                "occupation": user_data.get('occupation'),
                "reason_for_credit": application.get('purpose', '')
            }
        }

        try:
            validated = AggregatedData(**aggregated_data)
            return AgentResult(
                status="SUCCESS",
                data=validated.model_dump(),
                confidence=1.0  
            )
        except Exception as e:
            return AgentResult(
                status="FAILURE",
                data={},
                confidence=0.0,
                error_message=f"数据聚合失败: {e}"
            )

    def _determine_income_bracket(self, income: int) -> str:
        if income < 3000:
            return "LOW"
        elif income < 8000:
            return "MID_LOW"
        elif income < 15000:
            return "MID"
        else:
            return "HIGH"

    def _calculate_amount_vs_income(self, amount: int, income: int) -> float:
        if income <= 0:
            return 99.9
        return round(amount / income, 2)

    def _evaluate_workload_intensity(self, extra: Dict[str, Any]) -> str:
        intensity_score = 0
        if extra.get('avg_daily_orders', 0) > 30:
            intensity_score += 2
        if extra.get('work_hours_per_day', 0) > 10:
            intensity_score += 2
        if extra.get('avg_daily_trips', 0) > 20:
            intensity_score += 2
        if extra.get('peak_season_income_multiplier', 1) > 1.2:
            intensity_score += 1

        if intensity_score >= 4:
            return "HIGH"
        elif intensity_score >= 2:
            return "MID"
        else:
            return "LOW"