from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import re
from pydantic import BaseModel, Field

class AgentResult(BaseModel):
    status: str 
    data: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    suggested_next_actions: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, llm_client=None):
        self.name = name
        self.role = role
        self.llm_client = llm_client

    @abstractmethod
    def process(self, context: Dict[str, Any]) -> AgentResult:
        pass

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.llm_client:
            return self.llm_client.chat(prompt, system_prompt)
        return '{"error": "no_llm_client"}'
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            match_brace = re.search(r"\{.*\}", text, re.DOTALL)
            if match_brace:
                try:
                    return json.loads(match_brace.group(0))
                except:
                    pass
            return {}
    def get_info(self) -> Dict[str, Any]:
        return {"name": self.name, "role": self.role, "type": self.__class__.__name__}