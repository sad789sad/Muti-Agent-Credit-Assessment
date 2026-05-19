# Muti-Agent-Credit-Assessment
基于大语言模型与规则引擎混合的多智能体信用授信评估系统，模拟贷款审批流程。传统风控模型往往只能处理离散/连续数值特征，难以利用“客户自述的车辆用途”、“平台评价文本”、“技能描述”这类非结构化信息。本项目通过 LLM 与规则引擎的结合，实现了异构数据融合决策，适合评估缺乏传统信用记录但拥有替代数据（文本型）的非标准化客户。

## 项目简介

本项目实现了一个**主子智能体协作**的自动化信用授信审批系统。主智能体（协调器）负责调度五个子智能体，各子智能体独立完成特定分析任务并反馈执行状态，主智能体据此动态决策继续、拒绝或报错，最终综合所有结果输出授信决策。

系统支持 **LLM 推理**（默认接入阿里百炼 API）和**规则降级**双模式，确保在 LLM 不可用时仍能稳定运行。同时利用 SQLite 存储用户信息、申请记录和决策日志，便于审计与追溯。

## 核心功能

- 多源数据整合
- 合规与反欺诈检测
- 用户信用画像构建
- 量化风险评估
- 授信决策
- 最终综合决策与可解释理由
- 完整的数据持久化与决策日志

## 系统架构
```
    用户申请（金额 + 用途）
             ↓
┌─────────────────────────────┐
│ 协调智能体 (Orchestrator)    │
│ - 调度子智能体               │
│ - 处理状态（继续/拒绝/报错）  │
│ - 综合最终结果               │
└─────────────────────────────┘
              ↓ 串行调用
┌─────────────────────────────────────────┐
│ 1. 数据聚合智能体 (DataAggregatorAgent)  │
│ → 结构化多源数据                         │
│ 2. 合规反欺诈智能体 (ComplianceAgent)    │
│ → 欺诈风险评分（0-100）、合规检查         │
│ 3. 用户画像智能体 (ProfileBuilderAgent)  │ 
│ → 信用优势/劣势、建议评分范围             │
│ 4. 风险评估智能体 (RiskAssessorAgent)    │
│ → 最终信用评分（0-750）、风险等级         │
│ 5. 授信决策智能体 (CreditDeciderAgent)   │ 
│ → 初步决策（批准/拒绝）、额度、利率       │
└────────────────────────────────────────┘
                ↓
协调智能体综合决策 → 输出最终结果
```

## 项目结构
```
├── agents/ # 所有智能体
│ ├── base.py # 基类与 AgentResult 定义
│ ├── data_aggregator.py
│ ├── compliance_agent.py
│ ├── profile_builder.py
│ ├── risk_assessor.py
│ ├── credit_decider.py
│ ├── orchestrator.py
│ └── init.py
├── database/
│ └── db_handler.py # SQLite 数据库操作
├── prompts/
│ └── system_prompts.py # LLM 系统提示词
├── mock_data/
│ └── sample_users.py # 模拟用户数据（5个非标职业）
├── utils/
│ └── llm_client.py # 阿里百炼 API 客户端
├── schemas.py # Pydantic 数据模型
├── main.py # 程序入口，演示流程
├── .env.example # 环境变量模板
├── requirements.txt # 依赖列表
└── README.md
```

## 安装与运行
### 1. 克隆项目
```bash
git clone https://github.com/Muti-Agent-Credit-Assessment/Muti-Agent-Credit-Assessment.git
cd Muti-Agent-Credit-Assessment
```
### 2. 安装依赖
```bash
pip install -r requirements.txt
```
### 3.配置 LLM
```bash
cp .env.example .env
```
### 4. 运行演示
```bash
python main.py
```
首次运行会自动创建 risk_control.db 数据库，并插入 5 个模拟用户及其信用历史。随后对每个用户生成合理的申请金额和用途，执行完整授信流程。

## 输出示例
```text
>>> 开始处理用户：张伟 (外卖骑手) <<<
新授信申请处理
正在为用户 张伟 (外卖骑手) 处理申请...
  申请金额：4000元
  申请用途：购买工作所需电动车

----------------------------------------
【决策结果】
----------------------------------------
最终决策：REJECTED
信用评分：0.00
决策理由：合规/反欺诈未通过: 用户自述为外卖骑手且数据显示高强度工作（日均 38 单，持续 3 个月），但系统记录显示无交通工具，存在严重的逻辑矛盾，疑似伪造就业数据或账户共用。同时，短期内申请额度远超现有授信及还款能力证明，结合薄弱的信用历史和高负债收入比，符合欺诈风险特征，建议拒绝以避免坏账及合规风险。

【各智能体输出详情】

--- DataAggregatorAgent ---
{
  "demographic": {
    "age": 24,
    "occupation": "外卖骑手",
    "income_bracket": "MID_LOW"
  },
  "credit_profile": {
    "existing_limit": 500,
    "has_credit_history": true,
    "overdue_days": 0,
    "avg_utilization": 0.45
  },
  "application_details": {
    "amount": 4000,
    "purpose": "购买工作所需电动车",
    "amount_vs_income_ratio": 0.67
  },
  "alternative_data": {
    "has_alternative_proofs": false,
    "professional_certificates": [],
    "special_skills_mentioned": [
      "熟悉本地路况",
      "多平台接单能力"
    ],
    "workload_intensity": "HIGH"
  },
  "raw_data_available": {
    "user_extra": {
      "avg_daily_orders": 38,
      "work_hours_per_day": 11,
      "on_time_rate": 0.96,
      "customer_rating": 4.8,
      "platform_tenure_months": 3,
      "has_vehicle": false,
      "vehicle_purpose": "工作需要",
      "daily_trajectory": "覆盖5个商圈",
      "peak_season_income_multiplier": 1.3,
      "special_skills": [
        "熟悉本地路况",
        "多平台接单能力"
      ]
    },
    "occupation": "外卖骑手",
    "reason_for_credit": "购买工作所需电动车"
  }
}

--- ComplianceAgent ---
{
  "compliance_check_passed": false,
  "fraud_risk_score": 88,
  "issues_found": [
    "职业逻辑矛盾：平台工龄 3 个月且日均单量 38 单，但系统记录无车辆，高强度配送无交通工具支撑不符合常理",
    "授信跨度异常：现有额度 500 元，申请金额 4000 元，增幅 8 倍，且信用历史薄弱（总还款仅 1200 元）",
    "负债收入比偏高：申请金额占月收入比例 67%，超出低风险阈值",
    "缺乏辅助证明材料：无额外收入证明或资产证明，仅依赖平台数据"
  ],
  "fraud_signals_detected": [
    " employment_data_inconsistency",
    "aggressive_credit_limit_increase",
    "thin_credit_file",
    "high_debt_to_income_ratio"
  ],
  "recommended_action": "REJECT",
  "compliance_reasoning": "用户自述为外卖骑手且数据显示高强度工作（日均 38 单，持续 3 个月），但系统记录显示无交通工具，存在严重的逻辑矛盾，疑似伪造就业数据或账户共用。同时，短期内申请额度远超现有授信及还款能力证明，结合薄弱的信用历史和高负债收入比，符合欺诈风险特征，建议拒绝以避免坏账及合规风险。"
}
```
## License
MIT © [sad789sad](https://github.com/sad789sad)
