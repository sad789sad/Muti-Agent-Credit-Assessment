import sys
import os
import uuid
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db_handler import DatabaseHandler
from mock_data.sample_users import SAMPLE_USERS
from agents.orchestrator import OrchestratorAgent
from utils.llm_client import LLMClient
from schemas import FinalResult
from pydantic import ValidationError

llm_client = LLMClient()

def run_demo_application(db: DatabaseHandler, orchestrator: OrchestratorAgent,
                         user_id: str, amount: int, purpose: str):
    print("新授信申请处理")
    user_data = db.get_user(user_id)
    if not user_data:
        print(f"错误：未找到用户 {user_id}")
        return None
    credit_history = db.get_credit_history(user_id)
    app_id = str(uuid.uuid4())
    context = {
        "user_data": user_data,
        "credit_history": credit_history or {},
        "application": {
            "id": app_id,
            "amount": amount,
            "purpose": purpose,
            "submitted_at": datetime.now().isoformat()
        }
    }
    print(f"正在为用户 {user_data['name']} ({user_data['occupation']}) 处理申请...")
    print(f"  申请金额：{amount}元")
    print(f"  申请用途：{purpose}")
    try:
        result = orchestrator.orchestrate(context)
        try:
            FinalResult(**result)
        except ValidationError as e:
            print(f"警告：最终输出格式验证失败 {e}，但继续显示")
        print("\n" + "-" * 40)
        print("【决策结果】")
        print("-" * 40)
        print(f"最终决策：{result['final_decision']}")
        if result['final_decision'] == "APPROVED":
            print(f"批准金额：{result['final_approved_amount']}元")
        print(f"信用评分：{result['final_credit_score']:.2f}")
        print(f"决策理由：{result['final_reasoning']}")
        print("\n【各智能体输出详情】")
        trace = result.get('decision_trace', {})
        executed = trace.get('executed_agents', {})
        if executed:
            for agent_name, output in executed.items():
                print(f"\n--- {agent_name} ---")
                print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            for key in ['aggregated_data', 'compliance_result', 'profile', 'risk', 'decision']:
                if key in trace:
                    print(f"\n--- {key} ---")
                    print(json.dumps(trace[key], ensure_ascii=False, indent=2))
        print("-" * 40)

        app_record = {
            "app_id": app_id,
            "user_id": user_id,
            "application_amount": amount,
            "purpose": purpose,
            "status": result['final_decision'],
            "submitted_at": datetime.now().isoformat(),
            "decision_at": datetime.now().isoformat(),
            "final_credit_score": result['final_credit_score'],
            "final_amount": result['final_approved_amount'],
            "reasoning": result['final_reasoning'],
            "trace_data": json.dumps(result.get('decision_trace', {}))
        }
        db.save_application(app_record)

        return result

    except Exception as e:
        print(f"处理过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        return None

def print_all_records(db: DatabaseHandler):
    print("当前系统数据概览")
    users = db.get_all_users()
    print(f"\n已注册用户 ({len(users)}位):")
    for user in users:
        print(f"  - {user['name']} ({user['occupation']})")

    for status in ["APPROVED", "REJECTED"]:
        apps = db.query_applications_by_status(status)
        if apps:
            print(f"\n{status}申请记录 ({len(apps)}笔):")
            for app in apps:
                print(f"  - 用户ID: {app['user_id']}, 金额: {app['application_amount']}元")

def init_database_if_empty(db: DatabaseHandler):
    conn = sqlite3.connect("risk_control.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()

    if user_count == 0:
        print("首次运行，正在初始化数据库和模拟用户数据...")
        for user in SAMPLE_USERS:
            db.save_user(user)
            print(f"✓ 模拟数据已录入用户：{user['name']} ({user['occupation']})")

        for user in SAMPLE_USERS:
            import uuid as uuid_module
            occupation = user['occupation']
            
            if occupation == '外卖骑手':
                history = {
                    'record_id': str(uuid_module.uuid4()),
                    'user_id': user['user_id'],
                    'original_limit': 500,
                    'current_limit': 500,
                    'overdue_days': 0,
                    'total_repayment': 1200,
                    'average_utilization': 0.45,
                    'last_updated': datetime.now().isoformat()
                }
            elif occupation == '网约车司机':
                history = {
                    'record_id': str(uuid_module.uuid4()),
                    'user_id': user['user_id'],
                    'original_limit': 2000,
                    'current_limit': 2000,
                    'overdue_days': 0,
                    'total_repayment': 8500,
                    'average_utilization': 0.68,
                    'last_updated': datetime.now().isoformat()
                }
            elif occupation == '自由摄影师':
                history = {
                    'record_id': str(uuid_module.uuid4()),
                    'user_id': user['user_id'],
                    'original_limit': 1000,
                    'current_limit': 1000,
                    'overdue_days': 3,   
                    'total_repayment': 2800,
                    'average_utilization': 0.62,
                    'last_updated': datetime.now().isoformat()
                }
            elif occupation == '职场新人/广告策划':
                history = {
                    'record_id': str(uuid_module.uuid4()),
                    'user_id': user['user_id'],
                    'original_limit': 3000,
                    'current_limit': 3000,
                    'overdue_days': 0,
                    'total_repayment': 5600,
                    'average_utilization': 0.51,
                    'last_updated': datetime.now().isoformat()
                }
            elif occupation == '应届毕业生':
                history = {
                    'record_id': str(uuid_module.uuid4()),
                    'user_id': user['user_id'],
                    'original_limit': 500,
                    'current_limit': 500,
                    'overdue_days': 0,
                    'total_repayment': 200,
                    'average_utilization': 0.40,
                    'last_updated': datetime.now().isoformat()
                }
            else:
                history = {
                    'record_id': str(uuid_module.uuid4()),
                    'user_id': user['user_id'],
                    'original_limit': 0,
                    'current_limit': 0,
                    'overdue_days': 0,
                    'total_repayment': 0,
                    'average_utilization': 0,
                    'last_updated': datetime.now().isoformat()
                }
            db.save_credit_history(history)
            print(f"✓ 信用历史初始化：{user['name']} (额度{history['original_limit']}元，逾期{history['overdue_days']}天)")
        print("数据库初始化完成！\n")
    else:
        print(f"检测到已有 {user_count} 位用户数据，直接使用现有数据库。\n")

def main():
    db = DatabaseHandler()
    init_database_if_empty(db)
    orchestrator = OrchestratorAgent(llm_client=llm_client)
    print("开始运行授信申请演示")

    all_users = db.get_all_users()
    if not all_users:
        print("数据库中没有用户，请检查初始化。")
        return
    
    test_cases = [
    (4000, "购买工作所需电动车"),
    (10000, "车辆定期保养及维修"),
    (3000, "报名求职技能培训"),
    (8000, "相机镜头升级"),
    (5000, "日常消费"),]

    for idx, user_info in enumerate(all_users):
        amount, purpose = test_cases[idx % len(test_cases)]
        print(f"\n>>> 开始处理用户：{user_info['name']} ({user_info['occupation']}) <<<")
        run_demo_application(db, orchestrator, user_info['user_id'], amount, purpose)
    print_all_records(db)

if __name__ == "__main__":
    main()