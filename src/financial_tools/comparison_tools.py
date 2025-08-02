# -*- coding: utf-8 -*-
"""
비교 분석 도구 모듈

두 기간의 지출/수입 데이터를 비교 분석하는 도구 함수들을 제공합니다.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union

from src.analyzers.comparison_analyzer import ComparisonAnalyzer
from src.repositories.transaction_repository import TransactionRepository
from src.models import Transaction

# 로거 설정
logger = logging.getLogger(__name__)


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
        Dict[str, Any]: 비교 분석 결과
    """
    try:
        # 날짜 문자열을 date 객체로 변환
        p1_start = datetime.strptime(period1_start, "%Y-%m-%d").date()
        p1_end = datetime.strptime(period1_end, "%Y-%m-%d").date()
        p2_start = datetime.strptime(period2_start, "%Y-%m-%d").date()
        p2_end = datetime.strptime(period2_end, "%Y-%m-%d").date()
        
        # 거래 유형 매핑
        tx_type = None
        if transaction_type.lower() == "expense":
            tx_type = Transaction.TYPE_EXPENSE
        elif transaction_type.lower() == "income":
            tx_type = Transaction.TYPE_INCOME
        
        # 필터 설정
        filters = {}
        if group_by:
            filters['group_by'] = group_by
        
        # ComparisonAnalyzer 인스턴스 생성
        repository = TransactionRepository()
        analyzer = ComparisonAnalyzer(repository)
        
        # 비교 분석 수행
        result = analyzer.compare_periods(
            p1_start, p1_end,
            p2_start, p2_end,
            tx_type, filters
        )
        
        # 결과 포맷팅
        formatted_result = _format_comparison_result(result)
        
        return formatted_result
    
    except Exception as e:
        logger.error(f"기간 비교 분석 중 오류 발생: {e}")
        return {
            "error": f"기간 비교 분석 중 오류가 발생했습니다: {str(e)}",
            "success": False
        }


def compare_months(
    year1: int,
    month1: int,
    year2: int,
    month2: int,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> Dict[str, Any]:
    """
    두 월의 지출 또는 수입을 비교 분석합니다.
    
    Args:
        year1: 첫 번째 연도
        month1: 첫 번째 월
        year2: 두 번째 연도
        month2: 두 번째 월
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        Dict[str, Any]: 비교 분석 결과
    """
    try:
        # 거래 유형 매핑
        tx_type = None
        if transaction_type.lower() == "expense":
            tx_type = Transaction.TYPE_EXPENSE
        elif transaction_type.lower() == "income":
            tx_type = Transaction.TYPE_INCOME
        
        # 필터 설정
        filters = {}
        if group_by:
            filters['group_by'] = group_by
        
        # ComparisonAnalyzer 인스턴스 생성
        repository = TransactionRepository()
        analyzer = ComparisonAnalyzer(repository)
        
        # 비교 분석 수행
        result = analyzer.compare_months(
            year1, month1,
            year2, month2,
            tx_type, filters
        )
        
        # 결과 포맷팅
        formatted_result = _format_comparison_result(result)
        
        return formatted_result
    
    except Exception as e:
        logger.error(f"월 비교 분석 중 오류 발생: {e}")
        return {
            "error": f"월 비교 분석 중 오류가 발생했습니다: {str(e)}",
            "success": False
        }


def compare_with_previous_period(
    start_date: str,
    end_date: str,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> Dict[str, Any]:
    """
    지정된 기간과 동일한 길이의 이전 기간을 비교합니다.
    
    Args:
        start_date: 현재 기간 시작 날짜 (YYYY-MM-DD)
        end_date: 현재 기간 종료 날짜 (YYYY-MM-DD)
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        Dict[str, Any]: 비교 분석 결과
    """
    try:
        # 날짜 문자열을 date 객체로 변환
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # 거래 유형 매핑
        tx_type = None
        if transaction_type.lower() == "expense":
            tx_type = Transaction.TYPE_EXPENSE
        elif transaction_type.lower() == "income":
            tx_type = Transaction.TYPE_INCOME
        
        # 필터 설정
        filters = {}
        if group_by:
            filters['group_by'] = group_by
        
        # ComparisonAnalyzer 인스턴스 생성
        repository = TransactionRepository()
        analyzer = ComparisonAnalyzer(repository)
        
        # 비교 분석 수행
        result = analyzer.compare_with_previous_period(
            start, end,
            tx_type, filters
        )
        
        # 결과 포맷팅
        formatted_result = _format_comparison_result(result)
        
        return formatted_result
    
    except Exception as e:
        logger.error(f"이전 기간 비교 분석 중 오류 발생: {e}")
        return {
            "error": f"이전 기간 비교 분석 중 오류가 발생했습니다: {str(e)}",
            "success": False
        }


def compare_with_previous_month(
    year: int,
    month: int,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> Dict[str, Any]:
    """
    지정된 월과 이전 월을 비교합니다.
    
    Args:
        year: 현재 연도
        month: 현재 월
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        Dict[str, Any]: 비교 분석 결과
    """
    try:
        # 거래 유형 매핑
        tx_type = None
        if transaction_type.lower() == "expense":
            tx_type = Transaction.TYPE_EXPENSE
        elif transaction_type.lower() == "income":
            tx_type = Transaction.TYPE_INCOME
        
        # 필터 설정
        filters = {}
        if group_by:
            filters['group_by'] = group_by
        
        # ComparisonAnalyzer 인스턴스 생성
        repository = TransactionRepository()
        analyzer = ComparisonAnalyzer(repository)
        
        # 비교 분석 수행
        result = analyzer.compare_with_previous_month(
            year, month,
            tx_type, filters
        )
        
        # 결과 포맷팅
        formatted_result = _format_comparison_result(result)
        
        return formatted_result
    
    except Exception as e:
        logger.error(f"이전 월 비교 분석 중 오류 발생: {e}")
        return {
            "error": f"이전 월 비교 분석 중 오류가 발생했습니다: {str(e)}",
            "success": False
        }


def find_significant_changes(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    transaction_type: str = "expense",
    threshold_percentage: float = 20.0,
    min_amount: float = 10000.0
) -> Dict[str, Any]:
    """
    두 기간 사이의 주요 변동 사항을 찾습니다.
    
    Args:
        period1_start: 첫 번째 기간 시작 날짜 (YYYY-MM-DD)
        period1_end: 첫 번째 기간 종료 날짜 (YYYY-MM-DD)
        period2_start: 두 번째 기간 시작 날짜 (YYYY-MM-DD)
        period2_end: 두 번째 기간 종료 날짜 (YYYY-MM-DD)
        transaction_type: 분석할 거래 유형 (expense/income)
        threshold_percentage: 변화율 임계값 (%)
        min_amount: 최소 금액 임계값
        
    Returns:
        Dict[str, Any]: 주요 변동 사항 분석 결과
    """
    try:
        # 날짜 문자열을 date 객체로 변환
        p1_start = datetime.strptime(period1_start, "%Y-%m-%d").date()
        p1_end = datetime.strptime(period1_end, "%Y-%m-%d").date()
        p2_start = datetime.strptime(period2_start, "%Y-%m-%d").date()
        p2_end = datetime.strptime(period2_end, "%Y-%m-%d").date()
        
        # 거래 유형 매핑
        tx_type = None
        if transaction_type.lower() == "expense":
            tx_type = Transaction.TYPE_EXPENSE
        elif transaction_type.lower() == "income":
            tx_type = Transaction.TYPE_INCOME
        
        # ComparisonAnalyzer 인스턴스 생성
        repository = TransactionRepository()
        analyzer = ComparisonAnalyzer(repository)
        
        # 비교 분석 수행
        result = analyzer.compare_periods(
            p1_start, p1_end,
            p2_start, p2_end,
            tx_type
        )
        
        # 주요 변동 사항 추출
        significant_changes = {
            "increases": [],
            "decreases": [],
            "new_categories": [],
            "removed_categories": []
        }
        
        # 카테고리별 변동 분석
        for category_item in result['category_comparison']:
            category = category_item['category']
            amount1 = category_item['amount1']
            amount2 = category_item['amount2']
            diff = category_item['diff']
            diff_percentage = category_item['diff_percentage']
            
            # 새로운 카테고리 (첫 번째 기간에 없었던 경우)
            if amount1 == 0 and amount2 > min_amount:
                significant_changes["new_categories"].append({
                    "category": category,
                    "amount": amount2,
                })
                continue
            
            # 사라진 카테고리 (두 번째 기간에 없는 경우)
            if amount2 == 0 and amount1 > min_amount:
                significant_changes["removed_categories"].append({
                    "category": category,
                    "amount": amount1,
                })
                continue
            
            # 임계값 이상 증가한 카테고리
            if diff_percentage is not None and diff_percentage > threshold_percentage and abs(diff) > min_amount:
                significant_changes["increases"].append({
                    "category": category,
                    "amount1": amount1,
                    "amount2": amount2,
                    "diff": diff,
                    "diff_percentage": diff_percentage
                })
            
            # 임계값 이상 감소한 카테고리
            elif diff_percentage is not None and diff_percentage < -threshold_percentage and abs(diff) > min_amount:
                significant_changes["decreases"].append({
                    "category": category,
                    "amount1": amount1,
                    "amount2": amount2,
                    "diff": diff,
                    "diff_percentage": diff_percentage
                })
        
        # 결과 정렬
        significant_changes["increases"].sort(key=lambda x: x["diff_percentage"], reverse=True)
        significant_changes["decreases"].sort(key=lambda x: x["diff_percentage"])
        significant_changes["new_categories"].sort(key=lambda x: x["amount"], reverse=True)
        significant_changes["removed_categories"].sort(key=lambda x: x["amount"], reverse=True)
        
        # 요약 정보 추가
        significant_changes["summary"] = {
            "period1": {
                "start_date": period1_start,
                "end_date": period1_end,
                "total": result["summary_comparison"]["total1"]
            },
            "period2": {
                "start_date": period2_start,
                "end_date": period2_end,
                "total": result["summary_comparison"]["total2"]
            },
            "total_diff": result["summary_comparison"]["diff"],
            "total_diff_percentage": result["summary_comparison"]["diff_percentage"],
            "transaction_type": transaction_type
        }
        
        return {
            "significant_changes": significant_changes,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"주요 변동 사항 분석 중 오류 발생: {e}")
        return {
            "error": f"주요 변동 사항 분석 중 오류가 발생했습니다: {str(e)}",
            "success": False
        }


def _format_comparison_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    비교 분석 결과를 사용자 친화적인 형태로 포맷팅합니다.
    
    Args:
        result: ComparisonAnalyzer에서 반환한 원본 결과
        
    Returns:
        Dict[str, Any]: 포맷팅된 결과
    """
    # 기간 정보
    period1 = {
        "start_date": result["period1"]["start_date"],
        "end_date": result["period1"]["end_date"],
        "days": result["period1"]["days"],
        "transaction_count": result["period1"]["transaction_count"]
    }
    
    if "year_month" in result["period1"]:
        period1["year_month"] = result["period1"]["year_month"]
    
    period2 = {
        "start_date": result["period2"]["start_date"],
        "end_date": result["period2"]["end_date"],
        "days": result["period2"]["days"],
        "transaction_count": result["period2"]["transaction_count"]
    }
    
    if "year_month" in result["period2"]:
        period2["year_month"] = result["period2"]["year_month"]
    
    # 요약 비교
    summary = {
        "total": {
            "period1": result["summary_comparison"]["total1"],
            "period2": result["summary_comparison"]["total2"],
            "diff": result["summary_comparison"]["diff"],
            "diff_percentage": result["summary_comparison"]["diff_percentage"]
        },
        "count": {
            "period1": result["summary_comparison"]["count1"],
            "period2": result["summary_comparison"]["count2"],
            "diff": result["summary_comparison"]["count_diff"],
            "diff_percentage": result["summary_comparison"]["count_diff_percentage"]
        },
        "average": {
            "period1": result["summary_comparison"]["avg1"],
            "period2": result["summary_comparison"]["avg2"],
            "diff": result["summary_comparison"]["avg_diff"],
            "diff_percentage": result["summary_comparison"]["avg_diff_percentage"]
        },
        "daily_average": {
            "period1": result["summary_comparison"]["daily_avg1"],
            "period2": result["summary_comparison"]["daily_avg2"],
            "diff": result["summary_comparison"]["daily_avg_diff"],
            "diff_percentage": result["summary_comparison"]["daily_avg_diff_percentage"]
        }
    }
    
    # 카테고리별 비교
    categories = []
    for item in result["category_comparison"]:
        categories.append({
            "category": item["category"],
            "period1": {
                "amount": item["amount1"],
                "count": item["count1"]
            },
            "period2": {
                "amount": item["amount2"],
                "count": item["count2"]
            },
            "diff": item["diff"],
            "diff_percentage": item["diff_percentage"],
            "count_diff": item["count_diff"],
            "count_diff_percentage": item["count_diff_percentage"]
        })
    
    # 결제 방식별 비교
    payment_methods = []
    for item in result["payment_method_comparison"]:
        payment_methods.append({
            "payment_method": item["payment_method"],
            "period1": {
                "amount": item["amount1"],
                "count": item["count1"]
            },
            "period2": {
                "amount": item["amount2"],
                "count": item["count2"]
            },
            "diff": item["diff"],
            "diff_percentage": item["diff_percentage"],
            "count_diff": item["count_diff"],
            "count_diff_percentage": item["count_diff_percentage"]
        })
    
    # 일평균 비교
    daily_avg = {
        "period1": {
            "daily_avg": result["daily_avg_comparison"]["daily_avg1"],
            "days": result["daily_avg_comparison"]["period1_days"]
        },
        "period2": {
            "daily_avg": result["daily_avg_comparison"]["daily_avg2"],
            "days": result["daily_avg_comparison"]["period2_days"]
        },
        "diff": result["daily_avg_comparison"]["diff"],
        "diff_percentage": result["daily_avg_comparison"]["diff_percentage"]
    }
    
    # 주요 변동 요인 (상위 5개 카테고리)
    top_changes = []
    sorted_categories = sorted(
        categories,
        key=lambda x: abs(x["diff"]) if x["diff"] is not None else 0,
        reverse=True
    )
    
    for item in sorted_categories[:5]:
        if item["diff"] != 0:
            change_type = "증가" if item["diff"] > 0 else "감소"
            top_changes.append({
                "category": item["category"],
                "diff": item["diff"],
                "diff_percentage": item["diff_percentage"],
                "change_type": change_type
            })
    
    # 최종 결과
    formatted_result = {
        "period1": period1,
        "period2": period2,
        "summary": summary,
        "categories": categories,
        "payment_methods": payment_methods,
        "daily_average": daily_avg,
        "top_changes": top_changes,
        "success": True
    }
    
    return formatted_result