import json
from typing import Dict, Any, List, Optional
from agents.base import BaseAgent, AgentResult
from schemas import (
    PipelineContext, UserData, CreditHistory, Application,
    AggregatedData, ComplianceResult, ProfileResult, RiskResult, DecisionResult, FinalResult
)
from pydantic import ValidationError

class OrchestratorAgent(BaseAgent):
    def __init__(self, llm_client=None):
        super().__init__(
            name="协调智能体",
            role="orchestrator",
            llm_client=llm_client
        )
        self.available_agents = {
            "DataAggregatorAgent": {"context_keys": ["user_data", "credit_history", "application"]},
            "ComplianceAgent": {"context_keys": ["user_data", "credit_history", "application", "aggregated_data"]},
            "ProfileBuilderAgent": {"context_keys": ["user_data", "aggregated_data", "credit_history"]},
            "RiskAssessorAgent": {"context_keys": ["user_data", "credit_history", "application", "profile", "aggregated_data", "compliance_result"]},
            "CreditDeciderAgent": {"context_keys": ["user_data", "credit_history", "application", "profile", "risk", "aggregated_data"]}
        }

    def process(self, context: Dict[str, Any]) -> AgentResult:
        final = self.orchestrate(context)
        return AgentResult(
            status="SUCCESS",
            data=final
        )

    def orchestrate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ctx = PipelineContext(
                user_data=UserData(**context.get('user_data', {})),
                credit_history=CreditHistory(**context.get('credit_history', {})) if context.get('credit_history') else None,
                application=Application(**context.get('application', {}))
            )
        except ValidationError as e:
            print(f"输入数据格式错误: {e}")
            return self._build_error_response("输入数据格式错误")

        shared_ctx = {
            "user_data": context.get('user_data', {}),
            "credit_history": context.get('credit_history', {}),
            "application": context.get('application', {}),
        }

        plan = self._generate_initial_plan()
        results = {}   
        executed_agents = []  

        for task in plan:
            agent_name = task["agent"]
            required_keys = self.available_agents.get(agent_name, {}).get("context_keys", [])
            agent_input = {k: shared_ctx.get(k) for k in required_keys if k in shared_ctx}
            
            if not agent_input:
                print(f"警告：Agent {agent_name} 缺少必要输入，跳过")
                continue

            agent = self._import_agent(agent_name)
            agent_result = agent.process(agent_input)
            executed_agents.append(agent_name)

            if agent_result.status == "FAILURE":
                print(f"Agent {agent_name} 执行失败: {agent_result.error_message}")
                return self._build_error_response(f"{agent_name} 失败: {agent_result.error_message}")
            
            elif agent_result.status == "NEED_MORE_INFO":
                print(f"Agent {agent_name} 需要更多信息: {agent_result.missing_fields}")
                executed_outputs = {name: results.get(name) for name in executed_agents if name in results}
                return self._build_rejection(
                    f"信息不全: {agent_name} 需要 {agent_result.missing_fields}，请补充材料后重试",
                    agent_result.data,
                    trace_data=executed_outputs
                )
            
            if agent_result.status == "SUCCESS":
                if agent_name == "DataAggregatorAgent":
                    shared_ctx["aggregated_data"] = agent_result.data
                elif agent_name == "ComplianceAgent":
                    shared_ctx["compliance_result"] = agent_result.data
                    compliance = ComplianceResult(**agent_result.data)
                    if not compliance.compliance_check_passed or compliance.fraud_risk_score > 70:
                        executed_outputs = {
                            "DataAggregatorAgent": shared_ctx.get("aggregated_data"),
                            "ComplianceAgent": agent_result.data
                        }
                        return self._build_rejection(
                            f"合规/反欺诈未通过: {compliance.compliance_reasoning}",
                            agent_result.data,
                            trace_data=executed_outputs
                        )
                elif agent_name == "ProfileBuilderAgent":
                    shared_ctx["profile"] = agent_result.data
                elif agent_name == "RiskAssessorAgent":
                    shared_ctx["risk"] = agent_result.data
                elif agent_name == "CreditDeciderAgent":
                    shared_ctx["decision"] = agent_result.data
                results[agent_name] = agent_result.data

        final = self._synthesize_final_decision(shared_ctx, results)
        return final

    def _generate_initial_plan(self) -> List[Dict[str, Any]]:
        """生成初始执行计划（顺序依赖）"""
        return [
            {"id": 1, "agent": "DataAggregatorAgent"},
            {"id": 2, "agent": "ComplianceAgent"},
            {"id": 3, "agent": "ProfileBuilderAgent"},
            {"id": 4, "agent": "RiskAssessorAgent"},
            {"id": 5, "agent": "CreditDeciderAgent"}
        ]

    def _import_agent(self, agent_class_name: str):
        """延迟导入智能体类，避免循环导入"""
        if agent_class_name == "DataAggregatorAgent":
            from agents.data_aggregator import DataAggregatorAgent
            return DataAggregatorAgent(self.llm_client)
        elif agent_class_name == "ProfileBuilderAgent":
            from agents.profile_builder import ProfileBuilderAgent
            return ProfileBuilderAgent(self.llm_client)
        elif agent_class_name == "RiskAssessorAgent":
            from agents.risk_assessor import RiskAssessorAgent
            return RiskAssessorAgent(self.llm_client)
        elif agent_class_name == "CreditDeciderAgent":
            from agents.credit_decider import CreditDeciderAgent
            return CreditDeciderAgent(self.llm_client)
        elif agent_class_name == "ComplianceAgent":
            from agents.compliance_agent import ComplianceAgent
            return ComplianceAgent(self.llm_client)
        else:
            raise ValueError(f"Unknown agent: {agent_class_name}")

    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        return {
            "final_decision": "REJECTED",
            "final_credit_score": 0,
            "final_approved_amount": 0,
            "final_reasoning": f"系统内部错误: {error_msg}",
            "agent_votes": {},
            "confidence_level": "LOW",
            "next_steps_suggestion": "请联系客服",
            "decision_trace": {"error": error_msg}
        }

    def _build_rejection(self, reason: str, extra_info: Dict = None, trace_data: Dict = None) -> Dict[str, Any]:
        return {
            "final_decision": "REJECTED",
            "final_credit_score": 0,
            "final_approved_amount": 0,
            "final_reasoning": reason,
            "agent_votes": {"协调智能体": "REJECT"},
            "confidence_level": "HIGH",
            "next_steps_suggestion": "请补充材料后重新申请",
            "decision_trace": {
                "rejection_reason": reason,
                "extra": extra_info or {},
                "executed_agents": trace_data or {}
            }
        }

    def _synthesize_final_decision(self, shared_ctx: Dict, results: Dict) -> Dict[str, Any]:
        """综合所有子 Agent 的输出，做出最终决策（优先使用 LLM，降级规则）"""
        compliance = shared_ctx.get("compliance_result", {})
        profile = shared_ctx.get("profile", {})
        risk = shared_ctx.get("risk", {})
        decision = shared_ctx.get("decision", {})
        aggregated = shared_ctx.get("aggregated_data", {})

        if not compliance.get("compliance_check_passed", True) or compliance.get("fraud_risk_score", 0) > 70:
            return self._build_rejection("合规/反欺诈检查未通过", compliance)

        if self.llm_client and self.llm_client.enabled:
            prompt = f"""
你是一位授信审批主管。请综合以下专家智能体的分析报告，做出最终决策。

【合规智能体】
{json.dumps(compliance, ensure_ascii=False, indent=2)}

【画像智能体】
{json.dumps(profile, ensure_ascii=False, indent=2)}

【风险智能体】
{json.dumps(risk, ensure_ascii=False, indent=2)}

【授信决策智能体初步建议】
{json.dumps(decision, ensure_ascii=False, indent=2)}

输出要求（严格 JSON 格式）：
{{
    "final_decision": "APPROVED" 或 "REJECTED",
    "final_credit_score": 整数 (0-750),
    "final_approved_amount": 整数,
    "final_reasoning": "简短的中文理由",
    "agent_votes": {{
        "合规智能体": "APPROVE/REJECT/UNCLEAR",
        "画像智能体": "APPROVE/REJECT/UNCLEAR",
        "风险智能体": "APPROVE/REJECT/UNCLEAR",
        "授信决策智能体": "APPROVE/REJECT/UNCLEAR"
    }},
    "confidence_level": "HIGH/MEDIUM/LOW",
    "next_steps_suggestion": "后续建议"
}}
"""
            try:
                resp = self._call_llm(prompt, system_prompt="你是专业的信贷审批主管，决策要合理且可解释。")
                parsed = self._parse_json_response(resp)
                if parsed:
                    parsed.setdefault("final_decision", "REJECTED")
                    parsed.setdefault("final_credit_score", 0)
                    parsed.setdefault("final_approved_amount", 0)
                    parsed.setdefault("final_reasoning", "LLM 未提供理由")
                    parsed.setdefault("agent_votes", {})
                    parsed.setdefault("confidence_level", "MEDIUM")
                    parsed.setdefault("next_steps_suggestion", "无")
                    parsed["decision_trace"] = {
                        "aggregated_data": shared_ctx.get("aggregated_data"),
                        "compliance_result": shared_ctx.get("compliance_result"),
                        "profile": shared_ctx.get("profile"),
                        "risk": shared_ctx.get("risk"),
                        "decision": shared_ctx.get("decision")
                    }
                    return parsed
            except Exception as e:
                print(f"LLM 综合决策失败: {e}，降级到规则引擎")
        return self._rule_based_synthesis(shared_ctx, results)

    def _rule_based_synthesis(self, shared_ctx: Dict, results: Dict) -> Dict[str, Any]:
        """规则引擎综合决策"""
        compliance = shared_ctx.get("compliance_result", {})
        profile = shared_ctx.get("profile", {})
        risk = shared_ctx.get("risk", {})
        decision = shared_ctx.get("decision", {})
        
        compliance_passed = compliance.get('compliance_check_passed', True)
        fraud_score = compliance.get('fraud_risk_score', 0)
        risk_score = risk.get('final_risk_score', 0)
        risk_level = risk.get('risk_level', 'MEDIUM')
        decider_decision = decision.get('decision', 'REJECTED')
        proposed_amount = decision.get('final_amount', 0)

        if not compliance_passed or fraud_score > 60:
            final_decision = "REJECTED"
            final_score = min(risk_score, 300)
            final_amount = 0
            reasoning = f"合规检查未通过，欺诈风险评分{fraud_score}"
        elif risk_level == "HIGH" or risk_score < 400:
            final_decision = "REJECTED"
            final_score = risk_score
            final_amount = 0
            reasoning = f"高风险等级（{risk_level}），信用评分{risk_score}偏低"
        elif decider_decision == "REJECTED":
            final_decision = "REJECTED"
            final_score = risk_score
            final_amount = 0
            reasoning = decision.get('decision_reasoning', '授信决策智能体判定为拒绝')
        else:
            final_decision = "APPROVED"
            final_score = min(risk_score + 50, 750)
            final_amount = proposed_amount
            reasoning = f"通过综合评估：{profile.get('user_summary', '')}；风险评级{risk_level}"

        votes = {
            "合规智能体": "APPROVE" if compliance_passed else "REJECT",
            "画像智能体": "APPROVE" if profile.get('recommended_score_range', (0, 0))[1] > 400 else "UNCLEAR",
            "风险智能体": "APPROVE" if risk_level in ["LOW", "MEDIUM"] else "REJECT",
            "授信决策智能体": decider_decision
        }

        return {
            "final_decision": final_decision,
            "final_credit_score": final_score,
            "final_approved_amount": final_amount,
            "final_reasoning": reasoning,
            "agent_votes": votes,
            "confidence_level": "HIGH" if final_decision == "REJECTED" else "MEDIUM",
            "next_steps_suggestion": "无需额外操作" if final_decision == "APPROVED" else "请联系人工客服",
            "decision_trace": {
                "aggregated_data": shared_ctx.get("aggregated_data"),
                "compliance_result": shared_ctx.get("compliance_result"),
                "profile": shared_ctx.get("profile"),
                "risk": shared_ctx.get("risk"),
                "decision": shared_ctx.get("decision")
            }
        }