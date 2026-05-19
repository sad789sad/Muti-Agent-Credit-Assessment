import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None,
                 max_tokens: int = 20000, temperature: float = 0.1, timeout: int = 100):

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("必须提供 api_key 或设置环境变量 DASHSCOPE_API_KEY")
        
        self.base_url = base_url or os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model or os.getenv("DASHSCOPE_MODEL", "qwen3.5-plus")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        self.enabled = True

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用百炼 API 时出错: {e}")
            return self._fallback(prompt)

    def _fallback(self, prompt: str) -> str:
        """降级响应"""
        if "画像" in prompt or "profile" in prompt.lower():
            return json.dumps({
                "user_summary": "默认画像（降级模式）",
                "credit_strengths": ["工作勤奋", "收入稳定"],
                "credit_weaknesses": ["信用历史不足"],
                "recommended_score_range": [550, 600],
                "key_insights": "规则引擎降级输出"
            })
        elif "风险" in prompt or "risk" in prompt.lower():
            return json.dumps({
                "base_score": 550,
                "risk_adjustment": 0,
                "final_risk_score": 550,
                "risk_level": "MEDIUM",
                "risk_factors": ["降级模式"],
                "fraud_indicators": []
            })
        elif "决策" in prompt or "credit" in prompt.lower():
            return json.dumps({
                "decision": "APPROVED",
                "final_amount": 5000,
                "interest_rate_suggestion": "12%-18%",
                "credit_line_usage_suggestion": "合理消费",
                "decision_reasoning": "降级决策：信用良好",
                "approval_duration_days": 30
            })
        else:
            return json.dumps({"status": "fallback", "message": "模拟响应"})