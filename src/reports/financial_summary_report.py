# -*- coding: utf-8 -*-
"""
재무 요약 리포트 생성기

통합 분석 결과를 기반으로 재무 요약 리포트를 생성합니다.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Union

from src.reports.base_report_generator import BaseReportGenerator

# 로거 설정
logger = logging.getLogger(__name__)


class FinancialSummaryReport(BaseReportGenerator):
    """
    재무 요약 리포트 생성기
    
    통합 분석 결과를 기반으로 재무 요약 리포트를 생성합니다.
    """
    
    def __init__(self, title: str = "재무 요약 리포트"):
        """
        재무 요약 리포트 생성기 초기화
        
        Args:
            title: 리포트 제목
        """
        super().__init__()
        self.title = title
    
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        재무 요약 리포트를 생성합니다.
        
        Args:
            data: 통합 분석 결과 데이터
            
        Returns:
            Dict[str, Any]: 리포트 데이터
        """
        # 리포트 메타데이터
        self.report_data = {
            "title": self.title,
            "generated_at": datetime.now().isoformat(),
            "report_type": "financial_summary"
        }
        
        # 기간 정보
        if "period" in data:
            self.report_data["period"] = data["period"]
        
        # 현금 흐름 요약
        if "cash_flow" in data:
            self.report_data["cash_flow_summary"] = self._process_cash_flow(data["cash_flow"])
        
        # 지출 요약
        if "expense" in data:
            self.report_data["expense_summary"] = self._process_expense(data["expense"])
        
        # 수입 요약
        if "income" in data:
            self.report_data["income_summary"] = self._process_income(data["income"])
        
        # 비교 분석 결과
        if "expense_comparison" in data:
            self.report_data["expense_comparison"] = self._process_comparison(
                data["expense_comparison"], "expense"
            )
        
        if "income_comparison" in data:
            self.report_data["income_comparison"] = self._process_comparison(
                data["income_comparison"], "income"
            )
        
        # 트렌드 분석 결과
        if "trends" in data:
            self.report_data["trends"] = self._process_trends(data["trends"])
        
        return self.report_data
    
    def _output_console(self) -> str:
        """
        콘솔 출력 형식으로 변환합니다.
        
        Returns:
            str: 콘솔 출력용 문자열
        """
        output = []
        
        # 제목 및 생성 시간
        output.append(f"\n{'=' * 60}")
        output.append(f"{self.report_data['title']}")
        output.append(f"생성 시간: {self._format_date(self.report_data['generated_at'])}")
        output.append(f"{'=' * 60}")
        
        # 기간 정보
        if "period" in self.report_data:
            period = self.report_data["period"]
            output.append(f"\n[분석 기간]")
            output.append(f"시작일: {self._format_date(period.get('start_date', ''))}")
            output.append(f"종료일: {self._format_date(period.get('end_date', ''))}")
            output.append(f"기간: {period.get('days', '')}일")
            
            if "year_month" in period:
                output.append(f"연월: {period['year_month']}")
        
        # 현금 흐름 요약
        if "cash_flow_summary" in self.report_data:
            cf = self.report_data["cash_flow_summary"]
            output.append(f"\n[현금 흐름 요약]")
            output.append(f"{'-' * 60}")
            output.append(f"총 수입: {cf['total_income']}")
            output.append(f"총 지출: {cf['total_expense']}")
            output.append(f"순 흐름: {cf['net_flow']} ({cf['status']})")
            
            if cf.get('income_expense_ratio'):
                output.append(f"수입/지출 비율: {cf['income_expense_ratio']}")
        
        # 지출 요약
        if "expense_summary" in self.report_data:
            exp = self.report_data["expense_summary"]
            output.append(f"\n[지출 요약]")
            output.append(f"{'-' * 60}")
            output.append(f"총 지출: {exp['total_expense']}")
            output.append(f"거래 건수: {exp['transaction_count']}건")
            output.append(f"일평균 지출: {exp['daily_average']}")
            output.append(f"월 예상 지출: {exp['monthly_estimate']}")
            
            if "top_categories" in exp:
                output.append(f"\n[주요 지출 카테고리 (상위 5개)]")
                for item in exp["top_categories"]:
                    output.append(f"{item['category']:15} | {item['amount']:>12} ({item['percentage']:5.1f}%)")
        
        # 수입 요약
        if "income_summary" in self.report_data:
            inc = self.report_data["income_summary"]
            output.append(f"\n[수입 요약]")
            output.append(f"{'-' * 60}")
            output.append(f"총 수입: {inc['total_income']}")
            output.append(f"거래 건수: {inc['transaction_count']}건")
            output.append(f"일평균 수입: {inc['daily_average']}")
            output.append(f"월 예상 수입: {inc['monthly_estimate']}")
            
            if "top_categories" in inc:
                output.append(f"\n[주요 수입 유형]")
                for item in inc["top_categories"]:
                    output.append(f"{item['category']:15} | {item['amount']:>12} ({item['percentage']:5.1f}%)")
        
        # 지출 비교
        if "expense_comparison" in self.report_data:
            output.append(f"\n[이전 기간 대비 지출 변화]")
            output.append(f"{'-' * 60}")
            ec = self.report_data["expense_comparison"]["summary"]
            output.append(f"총 지출: {ec['diff']} ({ec['diff_percentage']:+.1f}%)")
            output.append(f"일평균 지출: {ec['daily_avg_diff']} ({ec['daily_avg_diff_percentage']:+.1f}%)")
            
            if "top_changes" in self.report_data["expense_comparison"]:
                output.append(f"\n[주요 변화 카테고리 (상위 3개)]")
                for item in self.report_data["expense_comparison"]["top_changes"]:
                    output.append(f"{item['category']:15} | {item['diff']:>12} ({item['diff_percentage']:+.1f}%)")
        
        # 수입 비교
        if "income_comparison" in self.report_data:
            output.append(f"\n[이전 기간 대비 수입 변화]")
            output.append(f"{'-' * 60}")
            ic = self.report_data["income_comparison"]["summary"]
            output.append(f"총 수입: {ic['diff']} ({ic['diff_percentage']:+.1f}%)")
            output.append(f"일평균 수입: {ic['daily_avg_diff']} ({ic['daily_avg_diff_percentage']:+.1f}%)")
        
        # 트렌드 요약
        if "trends" in self.report_data:
            output.append(f"\n[트렌드 요약]")
            output.append(f"{'-' * 60}")
            trends = self.report_data["trends"]
            
            if "expense_trend" in trends:
                output.append(f"지출 트렌드: {trends['expense_trend']['direction']}")
                output.append(f"월별 변화율: {trends['expense_trend']['monthly_change_rate']:+.1f}%")
            
            if "income_trend" in trends:
                output.append(f"수입 트렌드: {trends['income_trend']['direction']}")
                output.append(f"월별 변화율: {trends['income_trend']['monthly_change_rate']:+.1f}%")
        
        return "\n".join(output)
    
    def _process_cash_flow(self, cash_flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        현금 흐름 데이터를 처리합니다.
        
        Args:
            cash_flow_data: 현금 흐름 분석 결과
            
        Returns:
            Dict[str, Any]: 처리된 현금 흐름 데이터
        """
        result = {
            "total_income": self._format_amount(cash_flow_data.get("total_income", 0)),
            "total_expense": self._format_amount(cash_flow_data.get("total_expense", 0)),
            "net_flow": self._format_amount(cash_flow_data.get("net_flow", 0)),
            "is_positive": cash_flow_data.get("is_positive", False),
            "status": "흑자" if cash_flow_data.get("is_positive", False) else "적자"
        }
        
        # 수입/지출 비율 추가
        if cash_flow_data.get("income_expense_ratio") is not None:
            result["income_expense_ratio"] = f"{cash_flow_data['income_expense_ratio']:.1f}"
        
        return result
    
    def _process_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        지출 데이터를 처리합니다.
        
        Args:
            expense_data: 지출 분석 결과
            
        Returns:
            Dict[str, Any]: 처리된 지출 데이터
        """
        result = {
            "total_expense": self._format_amount(expense_data.get("total_expense", 0)),
            "transaction_count": expense_data.get("transaction_count", 0),
            "daily_average": self._format_amount(expense_data.get("daily_average", 0)),
            "monthly_estimate": self._format_amount(expense_data.get("monthly_estimate", 0))
        }
        
        # 카테고리별 지출 추가
        if "by_category" in expense_data:
            top_categories = []
            for item in expense_data["by_category"][:5]:  # 상위 5개만
                top_categories.append({
                    "category": item["category"],
                    "amount": self._format_amount(item["amount"]),
                    "percentage": item["percentage"]
                })
            result["top_categories"] = top_categories
        
        return result
    
    def _process_income(self, income_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        수입 데이터를 처리합니다.
        
        Args:
            income_data: 수입 분석 결과
            
        Returns:
            Dict[str, Any]: 처리된 수입 데이터
        """
        result = {
            "total_income": self._format_amount(income_data.get("total_income", 0)),
            "transaction_count": income_data.get("transaction_count", 0),
            "daily_average": self._format_amount(income_data.get("daily_average", 0)),
            "monthly_estimate": self._format_amount(income_data.get("monthly_estimate", 0))
        }
        
        # 카테고리별 수입 추가
        if "by_category" in income_data:
            top_categories = []
            for item in income_data["by_category"]:
                top_categories.append({
                    "category": item["category"],
                    "amount": self._format_amount(item["amount"]),
                    "percentage": item["percentage"]
                })
            result["top_categories"] = top_categories
        
        return result
    
    def _process_comparison(self, comparison_data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """
        비교 분석 데이터를 처리합니다.
        
        Args:
            comparison_data: 비교 분석 결과
            data_type: 데이터 유형 (expense/income)
            
        Returns:
            Dict[str, Any]: 처리된 비교 분석 데이터
        """
        result = {"summary": {}}
        
        # 요약 비교 정보
        if "summary_comparison" in comparison_data:
            sc = comparison_data["summary_comparison"]
            result["summary"] = {
                "diff": self._format_amount(sc.get("diff", 0)),
                "diff_percentage": sc.get("diff_percentage", 0),
                "daily_avg_diff": self._format_amount(sc.get("daily_avg_diff", 0)),
                "daily_avg_diff_percentage": sc.get("daily_avg_diff_percentage", 0)
            }
        
        # 카테고리별 비교 정보
        if "category_comparison" in comparison_data:
            top_changes = []
            for item in comparison_data["category_comparison"][:3]:  # 상위 3개만
                if item.get("diff_percentage") is not None:
                    top_changes.append({
                        "category": item["category"],
                        "diff": self._format_amount(item["diff"]),
                        "diff_percentage": item["diff_percentage"]
                    })
            result["top_changes"] = top_changes
        
        return result
    
    def _process_trends(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        트렌드 분석 데이터를 처리합니다.
        
        Args:
            trends_data: 트렌드 분석 결과
            
        Returns:
            Dict[str, Any]: 처리된 트렌드 분석 데이터
        """
        result = {}
        
        # 지출 트렌드
        if "expense_trend" in trends_data:
            et = trends_data["expense_trend"]
            result["expense_trend"] = {
                "direction": self._get_trend_direction(et.get("slope", 0)),
                "monthly_change_rate": et.get("monthly_change_rate", 0)
            }
        
        # 수입 트렌드
        if "income_trend" in trends_data:
            it = trends_data["income_trend"]
            result["income_trend"] = {
                "direction": self._get_trend_direction(it.get("slope", 0)),
                "monthly_change_rate": it.get("monthly_change_rate", 0)
            }
        
        return result
    
    def _get_trend_direction(self, slope: float) -> str:
        """
        기울기에 따른 트렌드 방향을 반환합니다.
        
        Args:
            slope: 추세선 기울기
            
        Returns:
            str: 트렌드 방향 설명
        """
        if slope > 0.05:
            return "크게 증가"
        elif slope > 0.01:
            return "소폭 증가"
        elif slope > -0.01:
            return "유지"
        elif slope > -0.05:
            return "소폭 감소"
        else:
            return "크게 감소"