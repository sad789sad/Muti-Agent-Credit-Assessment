from typing import Dict, Any
from agents.base import BaseAgent, AgentResult
from prompts.system_prompts import PROFILE_BUILDER_PROMPT
from schemas import ProfileResult
from pydantic import ValidationError

class ProfileBuilderAgent(BaseAgent):
    def __init__(self, llm_client=None):
        super().__init__(name="用户画像智能体", role="profile_builder", llm_client=llm_client)

    def process(self, context: Dict[str, Any]) -> AgentResult:
        user_data = context.get('user_data', {})
        aggregated = context.get('aggregated_data', {})
        credit_history = context.get('credit_history', {})

        prompt = f"""
请根据以下用户信息生成信用画像，输出 JSON 格式。

【基本信息】
- 姓名：{user_data.get('name')}
- 年龄：{user_data.get('age')}
- 职业：{user_data.get('occupation')}
- 月收入：{user_data.get('monthly_income')} 元

【额外特征】：
{user_data.get('extra_features', {})}

【信用历史】：
{credit_history if credit_history else '无历史记录'}

【聚合数据摘要】：
{aggregated}

输出格式示例：
{{
    "user_summary": "一句话总结用户",
    "credit_strengths": ["优势1", "优势2"],
    "credit_weaknesses": ["劣势1", "劣势2"],
    "recommended_score_range": [最低分, 最高分],
    "key_insights": "关键洞察"
}}
注意：recommended_score_range 是 [0,750] 区间的两个整数。
"""
        if self.llm_client and self.llm_client.enabled:
            resp = self._call_llm(prompt, PROFILE_BUILDER_PROMPT)
            result = self._parse_json_response(resp)
            try:
                if 'recommended_score_range' in result and isinstance(result['recommended_score_range'], list):
                    result['recommended_score_range'] = tuple(result['recommended_score_range'])
                validated = ProfileResult(**result)
                return AgentResult(
                    status="SUCCESS",
                    data=validated.model_dump()
                )
            except ValidationError as e:
                print(f"LLM 返回画像格式错误: {e}，使用规则引擎")
                return self._rule_based_profile(user_data, aggregated, credit_history)
        else:
            return self._rule_based_profile(user_data, aggregated, credit_history)

    def _rule_based_profile(self, user_data, aggregated, credit_history) -> AgentResult:
        occupation = user_data.get('occupation', '')
        extra = user_data.get('extra_features', {})
        income = user_data.get('monthly_income', 0)

        if occupation == "外卖骑手":
            avg_orders = extra.get('avg_daily_orders', 30)
            rating = extra.get('customer_rating', 0)
            on_time = extra.get('on_time_rate', 0)
            base = 550
            if avg_orders >= 35: base += 30
            if rating >= 4.5: base += 20
            if on_time >= 0.95: base += 20
            result = {
                "user_summary": f"外卖骑手，月收入{income}元，日均{avg_orders}单",
                "credit_strengths": ["工作勤奋，日均订单量较高", "客户评分和准时率高", "购买电动车为生产性消费"],
                "credit_weaknesses": [],
                "recommended_score_range": (base, base+50),
                "key_insights": f"日均{avg_orders}单，准时率{on_time*100:.0f}%，责任心较强。",
            }
        elif occupation == "网约车司机":
            avg_trips = extra.get('avg_daily_trips', 0)
            rating = extra.get('driver_rating', 0)
            tenure = extra.get('platform_tenure_years', 0)
            base = 600
            if rating >= 4.8: base += 25
            if tenure >= 2: base += 20
            if avg_trips >= 20: base += 15
            result = {
                "user_summary": f"网约车司机，从业{tenure}年，月收入{income}元",
                "credit_strengths": ["平台服务年限长", "司机评分高", "有商业保险"],
                "credit_weaknesses": ["车辆为租赁" if extra.get('vehicle_ownership') == '租赁' else ""],
                "recommended_score_range": (base, base+40),
                "key_insights": f"日均{avg_trips}单，评分{rating}，收入稳定。",
            }
        elif occupation == "自由摄影师":
            avg_projects = extra.get('avg_monthly_projects', 0)
            base = 550
            if avg_projects >= 5: base += 20
            if extra.get('has_own_equipment'): base += 15
            if extra.get('professional_certificates'): base += 10
            result = {
                "user_summary": f"自由摄影师，专攻{extra.get('specialization','婚礼跟拍')}，月均{avg_projects}个项目",
                "credit_strengths": ["专业技能和作品集", "有专业认证", "旺季收入高"],
                "credit_weaknesses": ["收入波动较大"],
                "recommended_score_range": (base, base+30),
                "key_insights": "基于项目的计费模式，有专业资质但收入稳定性中等。",
            }
        elif occupation == "职场新人/广告策划":
            tenure = extra.get('tenure_months', 0)
            base = 650
            if tenure >= 12: base += 30
            elif tenure >= 6: base += 15
            if extra.get('has_social_security'): base += 20
            result = {
                "user_summary": f"广告策划，月收入{income}元，入职{tenure}个月",
                "credit_strengths": ["正规就业和社保记录", "收入潜力较高"],
                "credit_weaknesses": ["入职时间较短"],
                "recommended_score_range": (base, base+30),
                "key_insights": "传统标准化数据较完整，信用基础较好。",
            }
        elif occupation == "应届毕业生":
            school = extra.get('graduated_from', '')
            has_offer = extra.get('has_job_offer', False)
            base = 600
            if '985' in school or '211' in school: base += 30
            if has_offer: base += 40
            result = {
                "user_summary": f"{school}高校毕业生，当前收入{income}元，已有工作offer" if has_offer else f"{school}高校毕业生，当前收入{income}元",
                "credit_strengths": ["名校背景", "已有工作offer", "奖学金记录"] if has_offer else ["名校背景", "奖学金记录"],
                "credit_weaknesses": ["当前收入偏低", "信用历史薄"],
                "recommended_score_range": (base, base+40),
                "key_insights": "教育背景优秀但学生贷款压力大，未来收入将增长。",
            }
        else:
            result = {
                "user_summary": f"{occupation}，月收入{income}元",
                "credit_strengths": ["已提交职业信息"],
                "credit_weaknesses": ["职业类型未覆盖专门画像"],
                "recommended_score_range": (500, 530),
                "key_insights": "需进一步核实职业信息。",
            }
        try:
            validated = ProfileResult(**result)
            return AgentResult(
                status="SUCCESS",
                data=validated.model_dump()
            )
        except ValidationError as e:
            print(f"规则引擎画像输出格式错误: {e}")
            default = {
                "user_summary": "默认用户画像",
                "credit_strengths": [],
                "credit_weaknesses": ["数据不足"],
                "recommended_score_range": (300, 400),
                "key_insights": "数据异常，使用默认画像"
            }
            return AgentResult(
                status="FAILURE",
                data=default,
                error_message=str(e)
            )