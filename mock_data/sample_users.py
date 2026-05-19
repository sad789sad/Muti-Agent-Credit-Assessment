import uuid
from datetime import datetime

# 模拟数据（非标准客户）
SAMPLE_USERS = [
    {
        'user_id': str(uuid.uuid4()),
        'name': '张伟',
        'age': 24,
        'occupation': '外卖骑手',
        'monthly_income': 6000,
        'registration_date': datetime.now().isoformat(),
        'extra_features': {
            'avg_daily_orders': 38,
            'work_hours_per_day': 11,
            'on_time_rate': 0.96,      # 准时率96%
            'customer_rating': 4.8,     # 满分5分
            'platform_tenure_months': 3,   # 入职3个月
            'has_vehicle': False,       # 正在购买电动车
            'vehicle_purpose': '工作需要',
            'daily_trajectory': '覆盖5个商圈',
            'peak_season_income_multiplier': 1.3,
            'special_skills': ['熟悉本地路况', '多平台接单能力']
        }
    },
    {
        'user_id': str(uuid.uuid4()),
        'name': '李芳',
        'age': 32,
        'occupation': '网约车司机',
        'monthly_income': 8000,
        'registration_date': datetime.now().isoformat(),
        'extra_features': {
            'avg_daily_trips': 22,
            'driver_rating': 4.9,
            'vehicle_ownership': '租赁',
            'platform_tenure_years': 2.5,
            'has_commercial_insurance': True,
            'monthly_repair_budget': 500,
            'flexible_income': True,
            'alternative_proofs': ['驾驶证满5年', '安全驾驶记录良好', '平台好评率98%']
        }
    },
    {
        'user_id': str(uuid.uuid4()),
        'name': '王磊',
        'age': 26,
        'occupation': '自由摄影师',
        'monthly_income': 5000,
        'registration_date': datetime.now().isoformat(),
        'extra_features': {
            'avg_monthly_projects': 4,
            'portfolio_links': ['作品集网址'],
            'specialization': '婚礼跟拍',
            'has_own_equipment': True,
            'peak_season': '5-10月',
            'alternative_income_proofs': ['项目合同', '客户评价'],
            'professional_certificates': ['高级摄影师认证']
        }
    },
    {
        'user_id': str(uuid.uuid4()),
        'name': '陈晓',
        'age': 28,
        'occupation': '职场新人/广告策划',
        'monthly_income': 10000,
        'registration_date': datetime.now().isoformat(),
        'extra_features': {
            'company_name': '某4A广告公司',
            'position': '助理策划',
            'tenure_months': 6,
            'graduated_from': '211院校',
            'has_social_security': True,
            'recent_consumption': {
                'housing_payment': 4000,
                'monthly_expenses': 3500
            },
            'education_certificate': '本科学历'
        }
    },
    {
        'user_id': str(uuid.uuid4()),
        'name': '赵敏',
        'age': 22,
        'occupation': '应届毕业生',
        'monthly_income': 4000,
        'registration_date': datetime.now().isoformat(),
        'extra_features': {
            'graduated_from': '985院校',
            'degree': '本科',
            'major': '计算机科学',
            'has_job_offer': True,
            'expected_income': 12000,
            'student_loan_remaining': 20000,
            'scholarship_history': ['国家奖学金', '校一等奖学金'],
            'internship_experience': '大厂实习3个月'
        }
    }
]

# 信用历史数据
SAMPLE_CREDIT_HISTORIES = [
    {
        'record_id': 'hist_001',
        'user_id': '',  
        'original_limit': 0,
        'current_limit': 0,
        'overdue_days': 0,
        'total_repayment': 0,
        'average_utilization': 0,
        'last_updated': datetime.now().isoformat()
    }
]


def init_sample_users(db_handler):
    """初始化数据库的用户数据"""
    from database.db_handler import DatabaseHandler
    from mock_data.sample_users import SAMPLE_USERS
    
    for user in SAMPLE_USERS:
        db_handler.save_user(user)
        print(f"模拟数据已录入用户：{user['name']} ({user['occupation']})")
    
    for user in SAMPLE_USERS:
        import uuid
        history = {
            'record_id': str(uuid.uuid4()),
            'user_id': user['user_id'],
            'original_limit': 500 if user['occupation'] in ['应届毕业生'] else 0,
            'current_limit': 500 if user['occupation'] in ['应届毕业生'] else 0,
            'overdue_days': 0,
            'total_repayment': 0,
            'average_utilization': 0,
            'last_updated': datetime.now().isoformat()
        }
        db_handler.save_credit_history(history)