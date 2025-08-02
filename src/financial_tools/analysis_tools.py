# -*- coding: utf-8 -*-
"""
분석 도구 모듈

LLM 에이전트가 호출할 수 있는 지출/수입 분석 및 리포트 관련 도구 함수들을 제공합니다.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union

from src.repositories.transaction_repository import TransactionRepository
from src.repositories.db_connection import DatabaseConnection
from src.analyzers.expense_analyzer import ExpenseAnalyzer
from src.analyzers.trend_analyzer import TrendAnalyzer
from src.analyzers.income_analyzer import IncomeAnalyzer
from src.analyzers.comparison_analyzer import ComparisonAnalyzer
from src.analyzers.integrated_analyzer import IntegratedAnalyzer

# 로거 설정
logger = logging.getLogger(__name__)

# 데이터베이스 연결 및 저장소 초기화
def _get_transaction_repository() -> TransactionRepository:
    """
    TransactionRepository 인스턴스를 반환합니다.
    
    Returns:
        TransactionRepository: 거래 저장소 인스턴스
    """
    db_connection = DatabaseConnection()
    return TransactionRepository(db_connection)

def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """
    문자열을 날짜 객체로 변환합니다.
    
    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD)
        
    Returns:
        Optional[date]: 변환된 날짜 객체 또는 None
        
    Raises:
        ValueError: 유효하지 않은 날짜 형식인 경우
    """
    if not date_str:
        return None
    
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"유효하지 않은 날짜 형식입니다: {date_str}. YYYY-MM-DD 형식을 사용하세요.")

def _prepare_chart_data(data: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
    """
    분석 결과를 차트 데이터 형식으로 변환합니다.
    
    Args:
        data: 분석 결과 데이터
        chart_type: 차트 유형 (pie, bar, line)
        
    Returns:
        Dict[str, Any]: 차트 데이터
    """
    if chart_type == "pie":
        # 파이 차트 데이터 형식
        return {
            "type": "pie",
            "labels": [item.get('category', item.get('payment_method', item.get('year_month', ''))) for item in data],
            "values": [item.get('amount', item.get('total', 0)) for item in data],
            "colors": [f"hsl({(i * 25) % 360}, 70%, 50%)" for i in range(len(data))],
            "total": sum(item.get('amount', item.get('total', 0)) for item in data)
        }
    elif chart_type == "bar":
        # 막대 차트 데이터 형식
        return {
            "type": "bar",
            "labels": [item.get('category', item.get('payment_method', item.get('year_month', ''))) for item in data],
            "values": [item.get('amount', item.get('total', 0)) for item in data],
            "colors": [f"hsl({(i * 25) % 360}, 70%, 50%)" for i in range(len(data))],
            "max_value": max(item.get('amount', item.get('total', 0)) for item in data) if data else 0
        }
    elif chart_type == "line":
        # 라인 차트 데이터 형식
        return {
            "type": "line",
            "labels": [item.get('date', item.get('year_month', '')) for item in data],
            "values": [item.get('amount', item.get('total', 0)) for item in data],
            "color": "hsl(210, 70%, 50%)",
            "min_value": min(item.get('amount', item.get('total', 0)) for item in data) if data else 0,
            "max_value": max(item.get('amount', item.get('total', 0)) for item in data) if data else 0
        }
    else:
        # 기본 데이터 형식
        return {
            "type": "raw",
            "data": data
        }

def analyze_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    group_by: str = "category"
) -> Dict[str, Any]:
    """
    지출 분석 리포트를 생성합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        category: 특정 카테고리만 분석
        payment_method: 특정 결제 방식만 분석
        group_by: 그룹화 기준 (category/payment_method/daily/weekly/monthly)
        
    Returns:
        dict: 분석 결과와 요약 정보
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 날짜 파싱
        parsed_start_date = _parse_date(start_date)
        parsed_end_date = _parse_date(end_date)
        
        # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 30일)
        if not parsed_start_date and not parsed_end_date:
            parsed_end_date = date.today()
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_start_date:
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_end_date:
            parsed_end_date = parsed_start_date + timedelta(days=30)
        
        # 필터 구성
        filters = {}
        if category:
            filters['category'] = category
        if payment_method:
            filters['payment_method'] = payment_method
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        expense_analyzer = ExpenseAnalyzer(repo)
        trend_analyzer = TrendAnalyzer(repo)
        
        # 분석 수행
        expense_result = expense_analyzer.analyze(parsed_start_date, parsed_end_date, filters)
        
        # 그룹화 기준에 따른 추가 분석
        if group_by == "daily" or group_by == "weekly" or group_by == "monthly":
            trend_result = trend_analyzer.analyze(parsed_start_date, parsed_end_date, filters)
            
            if group_by == "daily":
                # 일별 지출만 필터링
                daily_expenses = [item for item in trend_result['daily_trend'] 
                                if item['transaction_type'] == 'expense']
                group_data = daily_expenses
                chart_data = _prepare_chart_data(daily_expenses, "line")
            elif group_by == "weekly":
                # 주별 지출만 필터링
                weekly_expenses = [item for item in trend_result['weekly_trend'] 
                                 if item['transaction_type'] == 'expense']
                group_data = weekly_expenses
                chart_data = _prepare_chart_data(weekly_expenses, "bar")
            else:  # monthly
                # 월별 지출만 필터링
                monthly_expenses = [item for item in trend_result['monthly_trend'] 
                                  if item['transaction_type'] == 'expense']
                group_data = monthly_expenses
                chart_data = _prepare_chart_data(monthly_expenses, "bar")
        elif group_by == "category":
            group_data = expense_result['by_category']
            chart_data = _prepare_chart_data(expense_result['by_category'], "pie")
        elif group_by == "payment_method":
            group_data = expense_result['by_payment_method']
            chart_data = _prepare_chart_data(expense_result['by_payment_method'], "pie")
        else:
            raise ValueError(f"유효하지 않은 그룹화 기준입니다: {group_by}")
        
        # 응답 구성
        return {
            "summary": {
                "total_expense": expense_result['total_expense'],
                "transaction_count": expense_result['transaction_count'],
                "average_expense": expense_result['average_expense'],
                "daily_average": expense_result['daily_average'],
                "monthly_estimate": expense_result['monthly_estimate'],
                "period": {
                    "start_date": parsed_start_date.isoformat(),
                    "end_date": parsed_end_date.isoformat(),
                    "days": expense_result['period_days']
                }
            },
            "group_by": group_by,
            "data": group_data,
            "chart": chart_data,
            "filters": {
                "category": category,
                "payment_method": payment_method
            }
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "summary": {},
            "data": [],
            "chart": {"type": "raw", "data": []}
        }
    
    except Exception as e:
        logger.error(f"지출 분석 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"지출 분석 중 오류가 발생했습니다: {e}",
            "summary": {},
            "data": [],
            "chart": {"type": "raw", "data": []}
        }

def analyze_income(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    income_type: Optional[str] = None,
    group_by: str = "income_type"
) -> Dict[str, Any]:
    """
    수입 분석 리포트를 생성합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        income_type: 특정 수입 유형만 분석
        group_by: 그룹화 기준 (income_type/daily/weekly/monthly)
        
    Returns:
        dict: 분석 결과와 요약 정보
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 날짜 파싱
        parsed_start_date = _parse_date(start_date)
        parsed_end_date = _parse_date(end_date)
        
        # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 30일)
        if not parsed_start_date and not parsed_end_date:
            parsed_end_date = date.today()
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_start_date:
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_end_date:
            parsed_end_date = parsed_start_date + timedelta(days=30)
        
        # 필터 구성
        filters = {}
        if income_type:
            filters['income_type'] = income_type
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        income_analyzer = IncomeAnalyzer(repo)
        trend_analyzer = TrendAnalyzer(repo)
        
        # 분석 수행
        income_result = income_analyzer.analyze(parsed_start_date, parsed_end_date, filters)
        
        # 그룹화 기준에 따른 추가 분석
        if group_by == "daily" or group_by == "weekly" or group_by == "monthly":
            trend_result = trend_analyzer.analyze(parsed_start_date, parsed_end_date, filters)
            
            if group_by == "daily":
                # 일별 수입만 필터링
                daily_income = [item for item in trend_result['daily_trend'] 
                              if item['transaction_type'] == 'income']
                group_data = daily_income
                chart_data = _prepare_chart_data(daily_income, "line")
            elif group_by == "weekly":
                # 주별 수입만 필터링
                weekly_income = [item for item in trend_result['weekly_trend'] 
                               if item['transaction_type'] == 'income']
                group_data = weekly_income
                chart_data = _prepare_chart_data(weekly_income, "bar")
            else:  # monthly
                # 월별 수입만 필터링
                monthly_income = [item for item in trend_result['monthly_trend'] 
                                if item['transaction_type'] == 'income']
                group_data = monthly_income
                chart_data = _prepare_chart_data(monthly_income, "bar")
        elif group_by == "income_type":
            group_data = income_result['by_income_type']
            chart_data = _prepare_chart_data(income_result['by_income_type'], "pie")
        else:
            raise ValueError(f"유효하지 않은 그룹화 기준입니다: {group_by}")
        
        # 응답 구성
        return {
            "summary": {
                "total_income": income_result['total_income'],
                "transaction_count": income_result['transaction_count'],
                "average_income": income_result['average_income'],
                "daily_average": income_result['daily_average'],
                "monthly_estimate": income_result['monthly_estimate'],
                "period": {
                    "start_date": parsed_start_date.isoformat(),
                    "end_date": parsed_end_date.isoformat(),
                    "days": income_result['period_days']
                }
            },
            "group_by": group_by,
            "data": group_data,
            "chart": chart_data,
            "filters": {
                "income_type": income_type
            }
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "summary": {},
            "data": [],
            "chart": {"type": "raw", "data": []}
        }
    
    except Exception as e:
        logger.error(f"수입 분석 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"수입 분석 중 오류가 발생했습니다: {e}",
            "summary": {},
            "data": [],
            "chart": {"type": "raw", "data": []}
        }

def compare_periods(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> Dict[str, Any]:
    """
    두 기간의 지출 또는 수입을 비교 분석합니다.
    
    Args:
        period1_start: 첫 번째 기간 시작 날짜 (YYYY-MM-DD)
        period1_end: 첫 번째 기간 종료 날짜 (YYYY-MM-DD)
        period2_start: 두 번째 기간 시작 날짜 (YYYY-MM-DD)
        period2_end: 두 번째 기간 종료 날짜 (YYYY-MM-DD)
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        dict: 비교 분석 결과
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 날짜 파싱
        parsed_period1_start = _parse_date(period1_start)
        parsed_period1_end = _parse_date(period1_end)
        parsed_period2_start = _parse_date(period2_start)
        parsed_period2_end = _parse_date(period2_end)
        
        # 필수 파라미터 검증
        if not parsed_period1_start or not parsed_period1_end or not parsed_period2_start or not parsed_period2_end:
            raise ValueError("모든 기간 날짜는 필수 항목입니다.")
        
        # 거래 유형 검증
        if transaction_type not in ["expense", "income"]:
            raise ValueError(f"유효하지 않은 거래 유형입니다: {transaction_type}. 'expense' 또는 'income'을 사용하세요.")
        
        # 그룹화 기준 검증
        valid_group_by = ["category", "payment_method", "income_type"]
        if group_by not in valid_group_by:
            raise ValueError(f"유효하지 않은 그룹화 기준입니다: {group_by}. {', '.join(valid_group_by)} 중 하나를 사용하세요.")
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        comparison_analyzer = ComparisonAnalyzer(repo)
        
        # 분석 수행
        comparison_result = comparison_analyzer.compare_periods(
            parsed_period1_start, parsed_period1_end,
            parsed_period2_start, parsed_period2_end,
            transaction_type, group_by
        )
        
        # 차트 데이터 준비
        chart_data = {
            "type": "comparison",
            "labels": [item['name'] for item in comparison_result['comparison']],
            "period1_values": [item['period1_amount'] for item in comparison_result['comparison']],
            "period2_values": [item['period2_amount'] for item in comparison_result['comparison']],
            "colors": [f"hsl({(i * 25) % 360}, 70%, 50%)" for i in range(len(comparison_result['comparison']))],
            "max_value": max(
                max([item['period1_amount'] for item in comparison_result['comparison']], default=0),
                max([item['period2_amount'] for item in comparison_result['comparison']], default=0)
            )
        }
        
        # 응답 구성
        return {
            "summary": {
                "period1": {
                    "start_date": parsed_period1_start.isoformat(),
                    "end_date": parsed_period1_end.isoformat(),
                    "days": comparison_result['period1_days'],
                    "total": comparison_result['period1_total']
                },
                "period2": {
                    "start_date": parsed_period2_start.isoformat(),
                    "end_date": parsed_period2_end.isoformat(),
                    "days": comparison_result['period2_days'],
                    "total": comparison_result['period2_total']
                },
                "change": {
                    "absolute": comparison_result['absolute_change'],
                    "percentage": comparison_result['percentage_change'],
                    "daily_average_change": comparison_result['daily_average_change']
                }
            },
            "transaction_type": transaction_type,
            "group_by": group_by,
            "comparison": comparison_result['comparison'],
            "chart": chart_data
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "summary": {},
            "comparison": [],
            "chart": {"type": "raw", "data": []}
        }
    
    except Exception as e:
        logger.error(f"기간 비교 분석 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"기간 비교 분석 중 오류가 발생했습니다: {e}",
            "summary": {},
            "comparison": [],
            "chart": {"type": "raw", "data": []}
        }

def analyze_trends(
    months: int = 6,
    transaction_type: str = "expense",
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    지출 또는 수입 트렌드를 분석합니다.
    
    Args:
        months: 분석할 개월 수
        transaction_type: 분석할 거래 유형 (expense/income)
        category: 특정 카테고리만 분석
        
    Returns:
        dict: 트렌드 분석 결과
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 입력 검증
        if months <= 0:
            raise ValueError("개월 수는 양수여야 합니다.")
        
        if transaction_type not in ["expense", "income"]:
            raise ValueError(f"유효하지 않은 거래 유형입니다: {transaction_type}. 'expense' 또는 'income'을 사용하세요.")
        
        # 필터 구성
        filters = {'transaction_type': transaction_type}
        if category:
            filters['category'] = category
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        trend_analyzer = TrendAnalyzer(repo)
        
        # 분석 수행
        trend_result = trend_analyzer.analyze_monthly_trends(months, filters)
        
        # 월별 트렌드 데이터
        monthly_data = trend_result['monthly_trend']
        
        # 차트 데이터 준비
        chart_data = {
            "type": "line",
            "labels": [item['year_month'] for item in monthly_data],
            "values": [item['total'] for item in monthly_data],
            "color": "hsl(210, 70%, 50%)" if transaction_type == "expense" else "hsl(120, 70%, 50%)",
            "min_value": min([item['total'] for item in monthly_data], default=0),
            "max_value": max([item['total'] for item in monthly_data], default=0)
        }
        
        # 추세 계산
        if len(monthly_data) >= 2:
            first_value = monthly_data[0]['total'] if monthly_data else 0
            last_value = monthly_data[-1]['total'] if monthly_data else 0
            trend_change = last_value - first_value
            trend_percentage = (trend_change / first_value * 100) if first_value > 0 else 0
            trend_direction = "증가" if trend_change > 0 else "감소" if trend_change < 0 else "유지"
        else:
            trend_change = 0
            trend_percentage = 0
            trend_direction = "데이터 부족"
        
        # 응답 구성
        return {
            "summary": {
                "months_analyzed": months,
                "transaction_type": transaction_type,
                "category": category,
                "trend": {
                    "direction": trend_direction,
                    "change": trend_change,
                    "percentage": trend_percentage
                },
                "average_per_month": sum(item['total'] for item in monthly_data) / len(monthly_data) if monthly_data else 0
            },
            "monthly_data": monthly_data,
            "chart": chart_data
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "summary": {},
            "monthly_data": [],
            "chart": {"type": "raw", "data": []}
        }
    
    except Exception as e:
        logger.error(f"트렌드 분석 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"트렌드 분석 중 오류가 발생했습니다: {e}",
            "summary": {},
            "monthly_data": [],
            "chart": {"type": "raw", "data": []}
        }

def analyze_income_patterns(
    min_frequency: int = 2,
    min_amount: Optional[float] = None,
    max_months: int = 12
) -> Dict[str, Any]:
    """
    정기적인 수입 패턴을 분석합니다.
    
    Args:
        min_frequency: 최소 발생 빈도 (기본값: 2)
        min_amount: 최소 금액 (선택)
        max_months: 분석할 최대 개월 수 (기본값: 12)
        
    Returns:
        dict: 정기 수입 패턴 분석 결과
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 입력 검증
        if min_frequency < 2:
            raise ValueError("최소 발생 빈도는 2 이상이어야 합니다.")
        
        if max_months <= 0:
            raise ValueError("분석 개월 수는 양수여야 합니다.")
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        income_analyzer = IncomeAnalyzer(repo)
        
        # 정기 수입 패턴 분석
        regular_income = income_analyzer.find_regular_income(min_frequency)
        
        # 최소 금액 필터링
        if min_amount is not None:
            regular_income = [item for item in regular_income if item['amount'] >= min_amount]
        
        # 결과 분석
        total_regular_income = sum(item['amount'] for item in regular_income)
        
        # 월별 예상 수입 계산
        monthly_estimates = []
        for item in regular_income:
            avg_interval = item.get('avg_interval_days', 30)  # 기본값 30일
            if avg_interval <= 0:
                avg_interval = 30  # 안전장치
            
            # 월간 예상 발생 횟수
            monthly_occurrences = 30 / avg_interval
            monthly_amount = item['amount'] * monthly_occurrences
            
            monthly_estimates.append({
                'description': item['description'],
                'amount_per_occurrence': item['amount'],
                'avg_interval_days': item['avg_interval_days'],
                'monthly_occurrences': round(monthly_occurrences, 2),
                'monthly_amount': round(monthly_amount, 2),
                'category': item['category'],
                'source': item['source']
            })
        
        # 월간 총 예상 수입
        total_monthly_estimate = sum(item['monthly_amount'] for item in monthly_estimates)
        
        # 차트 데이터 준비
        chart_data = {
            "type": "bar",
            "labels": [item['description'] for item in monthly_estimates],
            "values": [item['monthly_amount'] for item in monthly_estimates],
            "colors": [f"hsl({(i * 25) % 360}, 70%, 50%)" for i in range(len(monthly_estimates))],
            "max_value": max([item['monthly_amount'] for item in monthly_estimates], default=0)
        }
        
        # 응답 구성
        return {
            "summary": {
                "total_patterns_found": len(regular_income),
                "total_regular_income": total_regular_income,
                "total_monthly_estimate": total_monthly_estimate,
                "analysis_period_months": max_months
            },
            "regular_patterns": regular_income,
            "monthly_estimates": monthly_estimates,
            "chart": chart_data
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "summary": {},
            "regular_patterns": [],
            "monthly_estimates": [],
            "chart": {"type": "raw", "data": []}
        }
    
    except Exception as e:
        logger.error(f"수입 패턴 분석 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"수입 패턴 분석 중 오류가 발생했습니다: {e}",
            "summary": {},
            "regular_patterns": [],
            "monthly_estimates": [],
            "chart": {"type": "raw", "data": []}
        }

def compare_income_expense(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "monthly"
) -> Dict[str, Any]:
    """
    수입과 지출을 비교 분석하고 순 현금 흐름을 계산합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        group_by: 그룹화 기준 (daily/weekly/monthly)
        
    Returns:
        dict: 수입-지출 비교 분석 결과
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 날짜 파싱
        parsed_start_date = _parse_date(start_date)
        parsed_end_date = _parse_date(end_date)
        
        # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 6개월)
        if not parsed_start_date and not parsed_end_date:
            parsed_end_date = date.today()
            parsed_start_date = date(parsed_end_date.year, parsed_end_date.month - 6 if parsed_end_date.month > 6 else parsed_end_date.month + 6 - 12, 1)
        elif not parsed_start_date:
            parsed_start_date = date(parsed_end_date.year, parsed_end_date.month - 6 if parsed_end_date.month > 6 else parsed_end_date.month + 6 - 12, 1)
        elif not parsed_end_date:
            parsed_end_date = date(parsed_start_date.year, parsed_start_date.month + 6 if parsed_start_date.month <= 6 else parsed_start_date.month - 6 + 12, 1)
        
        # 그룹화 기준 검증
        valid_group_by = ["daily", "weekly", "monthly"]
        if group_by not in valid_group_by:
            raise ValueError(f"유효하지 않은 그룹화 기준입니다: {group_by}. {', '.join(valid_group_by)} 중 하나를 사용하세요.")
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        integrated_analyzer = IntegratedAnalyzer(repo)
        
        # 수입-지출 비교 분석
        comparison_result = integrated_analyzer.compare_income_expense(parsed_start_date, parsed_end_date)
        
        # 그룹화 기준에 따른 데이터 추출
        if group_by == "daily":
            time_series = comparison_result['daily_comparison']
            time_unit = "일별"
        elif group_by == "weekly":
            time_series = comparison_result['weekly_comparison']
            time_unit = "주별"
        else:  # monthly
            time_series = comparison_result['monthly_comparison']
            time_unit = "월별"
        
        # 순 현금 흐름 계산
        for item in time_series:
            item['net_cash_flow'] = item['income'] - item['expense']
            item['is_positive'] = item['net_cash_flow'] >= 0
            if item['income'] > 0:
                item['savings_rate'] = (item['net_cash_flow'] / item['income']) * 100
            else:
                item['savings_rate'] = 0
        
        # 차트 데이터 준비
        chart_data = {
            "type": "cash_flow",
            "labels": [item['period'] for item in time_series],
            "income_values": [item['income'] for item in time_series],
            "expense_values": [item['expense'] for item in time_series],
            "net_values": [item['net_cash_flow'] for item in time_series],
            "income_color": "hsl(120, 70%, 50%)",
            "expense_color": "hsl(0, 70%, 50%)",
            "net_color": "hsl(210, 70%, 50%)",
            "max_value": max(
                max([item['income'] for item in time_series], default=0),
                max([item['expense'] for item in time_series], default=0)
            )
        }
        
        # 전체 요약 계산
        total_income = sum(item['income'] for item in time_series)
        total_expense = sum(item['expense'] for item in time_series)
        total_net_cash_flow = total_income - total_expense
        avg_savings_rate = (total_net_cash_flow / total_income * 100) if total_income > 0 else 0
        
        # 응답 구성
        return {
            "summary": {
                "period": {
                    "start_date": parsed_start_date.isoformat(),
                    "end_date": parsed_end_date.isoformat(),
                    "days": (parsed_end_date - parsed_start_date).days + 1
                },
                "total_income": total_income,
                "total_expense": total_expense,
                "net_cash_flow": total_net_cash_flow,
                "savings_rate": avg_savings_rate,
                "is_positive": total_net_cash_flow >= 0
            },
            "group_by": group_by,
            "time_unit": time_unit,
            "time_series": time_series,
            "chart": chart_data
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "summary": {},
            "time_series": [],
            "chart": {"type": "raw", "data": []}
        }
    
    except Exception as e:
        logger.error(f"수입-지출 비교 분석 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"수입-지출 비교 분석 중 오류가 발생했습니다: {e}",
            "summary": {},
            "time_series": [],
            "chart": {"type": "raw", "data": []}
        }

def get_financial_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    지정된 기간의 재정 요약 정보를 제공합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        
    Returns:
        dict: 재정 요약 정보
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 날짜 파싱
        parsed_start_date = _parse_date(start_date)
        parsed_end_date = _parse_date(end_date)
        
        # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 30일)
        if not parsed_start_date and not parsed_end_date:
            parsed_end_date = date.today()
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_start_date:
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_end_date:
            parsed_end_date = parsed_start_date + timedelta(days=30)
        
        # 분석기 초기화
        repo = _get_transaction_repository()
        expense_analyzer = ExpenseAnalyzer(repo)
        income_analyzer = IncomeAnalyzer(repo)
        
        # 분석 수행
        expense_result = expense_analyzer.analyze(parsed_start_date, parsed_end_date)
        income_result = income_analyzer.analyze(parsed_start_date, parsed_end_date)
        
        # 순 현금 흐름 계산
        net_cash_flow = income_result['total_income'] - expense_result['total_expense']
        savings_rate = (net_cash_flow / income_result['total_income'] * 100) if income_result['total_income'] > 0 else 0
        
        # 응답 구성
        return {
            "period": {
                "start_date": parsed_start_date.isoformat(),
                "end_date": parsed_end_date.isoformat(),
                "days": expense_result['period_days']
            },
            "income": {
                "total": income_result['total_income'],
                "transaction_count": income_result['transaction_count'],
                "daily_average": income_result['daily_average'],
                "monthly_estimate": income_result['monthly_estimate'],
                "top_sources": income_result['by_income_type'][:3] if 'by_income_type' in income_result else []
            },
            "expense": {
                "total": expense_result['total_expense'],
                "transaction_count": expense_result['transaction_count'],
                "daily_average": expense_result['daily_average'],
                "monthly_estimate": expense_result['monthly_estimate'],
                "top_categories": expense_result['by_category'][:3],
                "top_payment_methods": expense_result['by_payment_method'][:3]
            },
            "balance": {
                "net_cash_flow": net_cash_flow,
                "savings_rate": savings_rate,
                "is_positive": net_cash_flow >= 0
            }
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "period": {},
            "income": {},
            "expense": {},
            "balance": {}
        }
    
    except Exception as e:
        logger.error(f"재정 요약 정보 생성 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"재정 요약 정보 생성 중 오류가 발생했습니다: {e}",
            "period": {},
            "income": {},
            "expense": {},
            "balance": {}
        }