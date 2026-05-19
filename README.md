# Muti-Agent-Credit-Assessment

> 基于大语言模型与规则引擎混合的多智能体信用授信评估系统，模拟贷款审批流程。

## 项目简介

本项目实现了一个**主子智能体协作**的自动化信用授信审批系统。主智能体（协调器）负责调度五个子智能体，各子智能体独立完成特定分析任务并反馈执行状态，主智能体据此动态决策继续、拒绝或报错，最终综合所有结果输出授信决策。

系统支持 **LLM 推理**（默认接入阿里百炼 API）和**规则降级**双模式，确保在 LLM 不可用时仍能稳定运行。同时利用 SQLite 存储用户信息、申请记录和决策日志，便于审计与追溯。

## 核心功能
```
- 多源数据整合
- 合规与反欺诈检测
- 用户信用画像构建
- 量化风险评估
- 授信决策
- 最终综合决策与可解释理由
- 完整的数据持久化与决策日志
```
## 系统架构
```
用户申请（金额 + 用途）
↓
┌─────────────────────────────┐
│ 协调智能体 (Orchestrator) │
│ - 调度子智能体 │
│ - 处理状态（继续/拒绝/报错）│
│ - 综合最终结果 │
└─────────────────────────────┘
↓ 串行调用
┌──────────────────────────────────────────────────┐
│ 1. 数据聚合智能体 (DataAggregatorAgent) │
│ → 结构化多源数据 │
│ 2. 合规反欺诈智能体 (ComplianceAgent) │
│ → 欺诈风险评分（0-100）、合规检查 │
│ 3. 用户画像智能体 (ProfileBuilderAgent) │
│ → 信用优势/劣势、建议评分范围 │
│ 4. 风险评估智能体 (RiskAssessorAgent) │
│ → 最终信用评分（0-750）、风险等级 │
│ 5. 授信决策智能体 (CreditDeciderAgent) │
│ → 初步决策（批准/拒绝）、额度、利率 │
└──────────────────────────────────────────────────┘
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
│ └── llm_client.py # 阿里百炼 API 客户端（兼容 OpenAI）
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
### 2. 
