# -*- coding: utf-8 -*-
"""
거래 상세 리포트 생성기

거래 내역을 기반으로 상세 리포트를 생성합니다.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Union

from src.reports.base_report_generator import BaseReportGenerator

# 로거 설정
logger = logging.getLogger(__name__)


class TransactionDetailReport(BaseReportGenerator):
    """
    거래 상세 리포트 생성기
    
    거래 내역을 기반으로 상세 리포트를 생성합니다.
    """
    
    def __init__(self, title: str = "거래 상세 리포트"):
        """
        거래 상세 리포트 생성기 초기화
        
        Args:
            title: 리포트 제목
        """
        super().__init__()
        self.title = title
    
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래 상세 리포트를 생성합니다.
        
        Args:
            data: 거래 데이터
            
        Returns:
            Dict[str, Any]: 리포트 데이터
        """
        # 리포트 메타데이터
        self.report_data = {
            "title": self.title,
            "generated_at": datetime.now().isoformat(),
            "report_type": "transaction_detail"
        }
        
        # 기간 정보
        if "period" in data:
            self.report_data["period"] = data["period"]
        
        # 필터 정보
        if "filters" in data:
            self.report_data["filters"] = data["filters"]
        
        # 거래 요약
        self.report_data["summary"] = self._create_summary(data)
        
        # 거래 목록
        if "transactions" in data:
            self.report_data["transactions"] = self._process_transactions(data["transactions"])
        
        # 일별 거래 요약
        if "daily_summary" in data:
            self.report_data["daily_summary"] = data["daily_summary"]
        
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
        
        # 필터 정보
        if "filters" in self.report_data:
            filters = self.report_data["filters"]
            output.append(f"\n[적용된 필터]")
            for key, value in filters.items():
                output.append(f"{key}: {value}")
        
        # 거래 요약
        if "summary" in self.report_data:
            summary = self.report_data["summary"]
            output.append(f"\n[거래 요약]")
            output.append(f"{'-' * 60}")
            output.append(f"총 거래 건수: {summary['transaction_count']}건")
            output.append(f"총 금액: {summary['total_amount']}")
            
            if "expense_count" in summary:
                output.append(f"지출 건수: {summary['expense_count']}건 ({summary['expense_amount']})")
            
            if "income_count" in summary:
                output.append(f"수입 건수: {summary['income_count']}건 ({summary['income_amount']})")
        
        # 일별 거래 요약
        if "daily_summary" in self.report_data:
            output.append(f"\n[일별 거래 요약]")
            output.append(f"{'-' * 60}")
            output.append(f"{'날짜':10} | {'건수':5} | {'금액':>12}")
            output.append(f"{'-' * 60}")
            
            for day_data in self.report_data["daily_summary"]:
                output.append(
                    f"{day_data['date']:10} | {day_data['count']:5} | {day_data['amount']:>12}"
                )
        
        # 거래 목록
        if "transactions" in self.report_data:
            output.append(f"\n[거래 목록]")
            output.append(f"{'-' * 100}")
            output.append(f"{'날짜':10} | {'설명':30} | {'금액':>12} | {'유형':8} | {'카테고리':12} | {'결제 방식':12}")
            output.append(f"{'-' * 100}")
            
            for tx in self.report_data["transactions"]:
                output.append(
                    f"{tx['date']:10} | {tx['description'][:30]:30} | {tx['amount']:>12} | "
                    f"{tx['type']:8} | {tx['category']:12} | {tx['payment_method']:12}"
                )
        
        return "\n".join(output)
    
    def _create_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래 요약 정보를 생성합니다.
        
        Args:
            data: 거래 데이터
            
        Returns:
            Dict[str, Any]: 요약 정보
        """
        summary = {
            "transaction_count": 0,
            "total_amount": "0원",
            "expense_count": 0,
            "expense_amount": "0원",
            "income_count": 0,
            "income_amount": "0원"
        }
        
        # 거래 건수 및 금액 계산
        if "transactions" in data:
            transactions = data["transactions"]
            summary["transaction_count"] = len(transactions)
            
            total_expense = 0
            total_income = 0
            expense_count = 0
            income_count = 0
            
            for tx in transactions:
                amount = tx.get("amount", 0)
                if isinstance(amount, str):
                    try:
                        amount = float(amount.replace(',', '').replace('원', ''))
                    except ValueError:
                        amount = 0
                
                if tx.get("transaction_type") == "expense":
                    total_expense += amount
                    expense_count += 1
                elif tx.get("transaction_type") == "income":
                    total_income += amount
                    income_count += 1
            
            summary["expense_count"] = expense_count
            summary["expense_amount"] = self._format_amount(total_expense)
            summary["income_count"] = income_count
            summary["income_amount"] = self._format_amount(total_income)
            summary["total_amount"] = self._format_amount(total_expense + total_income)
        
        # 총계 정보가 직접 제공된 경우
        elif "total_expense" in data:
            summary["expense_amount"] = self._format_amount(data["total_expense"])
            summary["expense_count"] = data.get("transaction_count", 0)
            summary["transaction_count"] = data.get("transaction_count", 0)
            summary["total_amount"] = summary["expense_amount"]
        
        elif "total_income" in data:
            summary["income_amount"] = self._format_amount(data["total_income"])
            summary["income_count"] = data.get("transaction_count", 0)
            summary["transaction_count"] = data.get("transaction_count", 0)
            summary["total_amount"] = summary["income_amount"]
        
        return summary
    
    def _process_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        거래 목록을 처리합니다.
        
        Args:
            transactions: 거래 목록
            
        Returns:
            List[Dict[str, Any]]: 처리된 거래 목록
        """
        result = []
        
        for tx in transactions:
            processed_tx = {
                "date": self._format_date(tx.get("transaction_date", "")),
                "description": tx.get("description", ""),
                "amount": self._format_amount(tx.get("amount", 0)),
                "type": tx.get("transaction_type", ""),
                "category": tx.get("category", ""),
                "payment_method": tx.get("payment_method", "")
            }
            
            # 추가 정보가 있으면 포함
            if "memo" in tx:
                processed_tx["memo"] = tx["memo"]
            
            if "source" in tx:
                processed_tx["source"] = tx["source"]
            
            result.append(processed_tx)
        
        return result