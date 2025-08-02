# -*- coding: utf-8 -*-
"""
금융 도구 패키지

LLM 에이전트가 호출할 수 있는 금융 관련 도구 함수들을 제공합니다.
"""

from src.financial_tools.transaction_tools import (
    list_transactions,
    get_transaction_details,
    search_transactions,
    get_available_categories,
    get_available_payment_methods,
    get_transaction_date_range
)

from src.financial_tools.analysis_tools import (
    analyze_expenses,
    analyze_income,
    compare_periods,
    analyze_trends,
    get_financial_summary
)

from src.financial_tools.management_tools import (
    add_classification_rule,
    update_classification_rule,
    delete_classification_rule,
    get_classification_rules,
    get_rule_stats,
    backup_data,
    restore_data,
    list_backups,
    export_data,
    get_system_status,
    update_settings,
    get_settings
)

__all__ = [
    # 거래 도구
    'list_transactions',
    'get_transaction_details',
    'search_transactions',
    'get_available_categories',
    'get_available_payment_methods',
    'get_transaction_date_range',
    
    # 분석 도구
    'analyze_expenses',
    'analyze_income',
    'compare_periods',
    'analyze_trends',
    'get_financial_summary',
    
    # 관리 도구
    'add_classification_rule',
    'update_classification_rule',
    'delete_classification_rule',
    'get_classification_rules',
    'get_rule_stats',
    'backup_data',
    'restore_data',
    'list_backups',
    'export_data',
    'get_system_status',
    'update_settings',
    'get_settings'
]