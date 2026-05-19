from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class UserData(BaseModel):
    user_id: str
    name: str
    age: int
    occupation: str
    monthly_income: int
    registration_date: str
    extra_features: Dict[str, Any] = Field(default_factory=dict)

class CreditHistory(BaseModel):
    record_id: str
    user_id: str
    original_limit: int = 0
    current_limit: int = 0
    overdue_days: int = 0
    total_repayment: int = 0
    average_utilization: float = 0.0
    last_updated: str

class Application(BaseModel):
    id: str
    amount: int
    purpose: str
    submitted_at: str

class PipelineContext(BaseModel):
    user_data: UserData
    credit_history: Optional[CreditHistory] = None
    application: Application
    aggregated_data: Optional['AggregatedData'] = None
    compliance_result: Optional['ComplianceResult'] = None
    profile_result: Optional['ProfileResult'] = None
    risk_result: Optional['RiskResult'] = None
    decision_result: Optional['DecisionResult'] = None

class AggregatedData(BaseModel):
    demographic: Dict[str, Any]
    credit_profile: Dict[str, Any]
    application_details: Dict[str, Any]
    alternative_data: Dict[str, Any]
    raw_data_available: Dict[str, Any]

class ComplianceResult(BaseModel):
    compliance_check_passed: bool
    fraud_risk_score: int  
    issues_found: List[str] = []
    fraud_signals_detected: List[str] = []
    recommended_action: str  
    compliance_reasoning: str

    @field_validator('fraud_risk_score')
    def check_score_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('fraud_risk_score must be between 0 and 100')
        return v

class ProfileResult(BaseModel):
    user_summary: str
    credit_strengths: List[str]
    credit_weaknesses: List[str]
    recommended_score_range: Tuple[int, int]  
    key_insights: str

class RiskResult(BaseModel):
    base_score: int
    risk_adjustment: int
    final_risk_score: int
    risk_level: str  
    risk_factors: List[str] = []
    fraud_indicators: List[str] = []

    @field_validator('final_risk_score')
    def check_final_score(cls, v):
        if not 0 <= v <= 750:
            raise ValueError('final_risk_score must be between 0 and 750')
        return v

class DecisionResult(BaseModel):
    decision: str 
    final_amount: int
    interest_rate_suggestion: str = ""
    credit_line_usage_suggestion: str = ""
    decision_reasoning: str
    approval_duration_days: int = 0
    decision_detail: Dict[str, Any] = Field(default_factory=dict)

class FinalResult(BaseModel):
    final_decision: str
    final_credit_score: float
    final_approved_amount: int
    final_reasoning: str
    agent_votes: Dict[str, str]
    confidence_level: str
    next_steps_suggestion: str
    decision_trace: Dict[str, Any]

PipelineContext.model_rebuild()