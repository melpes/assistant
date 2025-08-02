# -*- coding: utf-8 -*-
"""
리포트 생성기 테스트

리포트 생성 시스템의 기능을 테스트합니다.
"""

import os
import json
import tempfile
import unittest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch

from src.reports.base_report_generator import BaseReportGenerator
from src.reports.financial_summary_report import FinancialSummaryReport
from src.reports.transaction_detail_report import TransactionDetailReport
from src.reports.template_report import TemplateReport
from src.reports.report_generator import ReportGenerator


class TestBaseReportGenerator(unittest.TestCase):
    """BaseReportGenerator 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 리포트 생성기 클래스
        class TestReportGenerator(BaseReportGenerator):
            def generate_report(self, data):
                self.report_data = data
                return data
        
        self.report_generator = TestReportGenerator()
        self.test_data = {
            "title": "테스트 리포트",
            "date": date.today().isoformat(),
            "value": 12345,
            "nested": {"key": "value"}
        }
    
    def test_generate_report(self):
        """리포트 생성 테스트"""
        result = self.report_generator.generate_report(self.test_data)
        self.assertEqual(result, self.test_data)
        self.assertEqual(self.report_generator.report_data, self.test_data)
    
    def test_output_json(self):
        """JSON 출력 테스트"""
        self.report_generator.generate_report(self.test_data)
        
        # 임시 파일에 출력
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            output_path = temp_file.name
        
        try:
            # JSON 출력
            result = self.report_generator.output_report(
                output_format=BaseReportGenerator.FORMAT_JSON,
                output_file=output_path
            )
            
            # 결과 검증
            self.assertIsNotNone(result)
            
            # 파일 내용 검증
            with open(output_path, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
            
            self.assertEqual(file_content, self.test_data)
        
        finally:
            # 임시 파일 삭제
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_output_csv(self):
        """CSV 출력 테스트"""
        self.report_generator.generate_report(self.test_data)
        
        # CSV 출력 (파일 없이)
        result = self.report_generator.output_report(
            output_format=BaseReportGenerator.FORMAT_CSV
        )
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIn("title", result)
        self.assertIn("테스트 리포트", result)
    
    def test_flatten_dict(self):
        """딕셔너리 평탄화 테스트"""
        nested_dict = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            },
            "f": [1, 2, 3]
        }
        
        flat_dict = self.report_generator._flatten_dict(nested_dict)
        
        self.assertEqual(flat_dict["a"], 1)
        self.assertEqual(flat_dict["b_c"], 2)
        self.assertEqual(flat_dict["b_d_e"], 3)
        self.assertEqual(flat_dict["f_0"], 1)
        self.assertEqual(flat_dict["f_1"], 2)
        self.assertEqual(flat_dict["f_2"], 3)


class TestFinancialSummaryReport(unittest.TestCase):
    """FinancialSummaryReport 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.report_generator = FinancialSummaryReport()
        
        # 테스트 데이터
        self.test_data = {
            "period": {
                "start_date": (date.today() - timedelta(days=30)).isoformat(),
                "end_date": date.today().isoformat(),
                "days": 30
            },
            "cash_flow": {
                "total_income": 1000000,
                "total_expense": 800000,
                "net_flow": 200000,
                "is_positive": True,
                "income_expense_ratio": 1.25
            },
            "expense": {
                "total_expense": 800000,
                "transaction_count": 50,
                "daily_average": 26666.67,
                "monthly_estimate": 800000,
                "by_category": [
                    {"category": "식비", "amount": 300000, "percentage": 37.5},
                    {"category": "교통비", "amount": 100000, "percentage": 12.5},
                    {"category": "주거비", "amount": 400000, "percentage": 50.0}
                ]
            },
            "income": {
                "total_income": 1000000,
                "transaction_count": 2,
                "daily_average": 33333.33,
                "monthly_estimate": 1000000,
                "by_category": [
                    {"category": "급여", "amount": 900000, "percentage": 90.0},
                    {"category": "이자", "amount": 100000, "percentage": 10.0}
                ]
            }
        }
    
    def test_generate_report(self):
        """리포트 생성 테스트"""
        result = self.report_generator.generate_report(self.test_data)
        
        # 기본 정보 검증
        self.assertEqual(result["title"], "재무 요약 리포트")
        self.assertIn("generated_at", result)
        self.assertEqual(result["report_type"], "financial_summary")
        
        # 현금 흐름 요약 검증
        self.assertIn("cash_flow_summary", result)
        self.assertEqual(result["cash_flow_summary"]["status"], "흑자")
        
        # 지출 요약 검증
        self.assertIn("expense_summary", result)
        self.assertEqual(result["expense_summary"]["transaction_count"], 50)
        
        # 수입 요약 검증
        self.assertIn("income_summary", result)
        self.assertEqual(result["income_summary"]["transaction_count"], 2)
    
    def test_output_console(self):
        """콘솔 출력 테스트"""
        self.report_generator.generate_report(self.test_data)
        
        # 콘솔 출력
        result = self.report_generator.output_report(
            output_format=BaseReportGenerator.FORMAT_CONSOLE
        )
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIn("재무 요약 리포트", result)
        self.assertIn("현금 흐름 요약", result)
        self.assertIn("지출 요약", result)
        self.assertIn("수입 요약", result)


class TestTransactionDetailReport(unittest.TestCase):
    """TransactionDetailReport 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.report_generator = TransactionDetailReport()
        
        # 테스트 데이터
        self.test_data = {
            "period": {
                "start_date": (date.today() - timedelta(days=7)).isoformat(),
                "end_date": date.today().isoformat(),
                "days": 7
            },
            "transactions": [
                {
                    "transaction_date": date.today().isoformat(),
                    "description": "테스트 거래 1",
                    "amount": 10000,
                    "transaction_type": "expense",
                    "category": "식비",
                    "payment_method": "카드"
                },
                {
                    "transaction_date": (date.today() - timedelta(days=1)).isoformat(),
                    "description": "테스트 거래 2",
                    "amount": 20000,
                    "transaction_type": "expense",
                    "category": "교통비",
                    "payment_method": "현금"
                },
                {
                    "transaction_date": (date.today() - timedelta(days=2)).isoformat(),
                    "description": "테스트 수입",
                    "amount": 100000,
                    "transaction_type": "income",
                    "category": "급여",
                    "payment_method": "계좌이체"
                }
            ]
        }
    
    def test_generate_report(self):
        """리포트 생성 테스트"""
        result = self.report_generator.generate_report(self.test_data)
        
        # 기본 정보 검증
        self.assertEqual(result["title"], "거래 상세 리포트")
        self.assertIn("generated_at", result)
        self.assertEqual(result["report_type"], "transaction_detail")
        
        # 거래 요약 검증
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["transaction_count"], 3)
        self.assertEqual(result["summary"]["expense_count"], 2)
        self.assertEqual(result["summary"]["income_count"], 1)
        
        # 거래 목록 검증
        self.assertIn("transactions", result)
        self.assertEqual(len(result["transactions"]), 3)
        self.assertEqual(result["transactions"][0]["type"], "expense")
        self.assertEqual(result["transactions"][2]["type"], "income")
    
    def test_output_console(self):
        """콘솔 출력 테스트"""
        self.report_generator.generate_report(self.test_data)
        
        # 콘솔 출력
        result = self.report_generator.output_report(
            output_format=BaseReportGenerator.FORMAT_CONSOLE
        )
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIn("거래 상세 리포트", result)
        self.assertIn("거래 요약", result)
        self.assertIn("거래 목록", result)


class TestTemplateReport(unittest.TestCase):
    """TemplateReport 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 템플릿 내용
        self.template_content = """
# {{title}}

**생성일시**: {{generated_at}}

## 요약
- 총액: {{total}}원
- 건수: {{count}}건

{% if items %}
## 항목 목록
{% for item in items %}
- {{item.name}}: {{item.value}}원
{% endfor %}
{% endif %}
"""
        
        # 테스트 데이터
        self.test_data = {
            "title": "테스트 템플릿 리포트",
            "generated_at": datetime.now().isoformat(),
            "total": 50000,
            "count": 3,
            "items": [
                {"name": "항목 1", "value": 10000},
                {"name": "항목 2", "value": 20000},
                {"name": "항목 3", "value": 20000}
            ]
        }
        
        # 템플릿 리포트 생성기
        self.report_generator = TemplateReport()
        self.report_generator.set_template_content(self.template_content)
    
    def test_generate_report(self):
        """리포트 생성 테스트"""
        result = self.report_generator.generate_report(self.test_data)
        
        # 기본 정보 검증
        self.assertIn("content", result)
        self.assertIn("data", result)
        self.assertIn("generated_at", result)
        
        # 템플릿 렌더링 결과 검증
        content = result["content"]
        self.assertIn("테스트 템플릿 리포트", content)
        self.assertIn("총액: 50000원", content)
        self.assertIn("건수: 3건", content)
        self.assertIn("항목 1: 10000원", content)
        self.assertIn("항목 2: 20000원", content)
        self.assertIn("항목 3: 20000원", content)
    
    def test_conditional_blocks(self):
        """조건부 블록 테스트"""
        # 항목이 없는 데이터
        data_without_items = self.test_data.copy()
        data_without_items["items"] = []
        
        result = self.report_generator.generate_report(data_without_items)
        content = result["content"]
        
        # 항목 목록 섹션이 없어야 함
        self.assertNotIn("항목 목록", content)
    
    def test_filters(self):
        """필터 테스트"""
        # 날짜 포맷팅 필터 테스트용 템플릿
        date_template = "날짜: {{date|format_date}}"
        
        # 템플릿 설정
        self.report_generator.set_template_content(date_template)
        
        # 테스트 데이터
        date_data = {"date": "2023-01-01T12:34:56"}
        
        result = self.report_generator.generate_report(date_data)
        content = result["content"]
        
        # 날짜 포맷팅 결과 검증
        self.assertIn("날짜: 2023-01-01", content)


class TestReportGenerator(unittest.TestCase):
    """ReportGenerator 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 설정 저장소 모의 객체
        self.mock_config_repository = MagicMock()
        self.mock_config_repository.get_config.return_value = None
        
        # 리포트 생성기
        self.report_generator = ReportGenerator(self.mock_config_repository)
        
        # 테스트 데이터
        self.test_data = {
            "period": {
                "start_date": (date.today() - timedelta(days=30)).isoformat(),
                "end_date": date.today().isoformat(),
                "days": 30
            },
            "total": 100000,
            "count": 10
        }
    
    def test_create_financial_summary_report(self):
        """재무 요약 리포트 생성 테스트"""
        result = self.report_generator.create_report(
            report_type=ReportGenerator.REPORT_FINANCIAL_SUMMARY,
            data=self.test_data,
            output_format=ReportGenerator.FORMAT_CONSOLE
        )
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIn("재무 요약 리포트", result)
    
    def test_create_transaction_detail_report(self):
        """거래 상세 리포트 생성 테스트"""
        result = self.report_generator.create_report(
            report_type=ReportGenerator.REPORT_TRANSACTION_DETAIL,
            data=self.test_data,
            output_format=ReportGenerator.FORMAT_CONSOLE
        )
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIn("거래 상세 리포트", result)
    
    def test_add_template(self):
        """템플릿 추가 테스트"""
        template_name = "test_template"
        template_content = "# 테스트 템플릿\n\n내용: {{content}}"
        
        # 템플릿 추가
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            result = self.report_generator.add_template(template_name, template_content)
            
            # 결과 검증
            self.assertTrue(result)
            self.assertIn(template_name, self.report_generator.report_templates)
            
            # 파일 저장 확인
            mock_file.assert_called_once()
    
    @patch('os.path.exists')
    def test_create_template_report(self, mock_exists):
        """템플릿 리포트 생성 테스트"""
        # 템플릿 파일 존재 모의
        mock_exists.return_value = True
        
        # 템플릿 추가
        template_name = "test_template"
        template_path = os.path.join(self.report_generator.template_dir, f"{template_name}.template")
        self.report_generator.report_templates[template_name] = template_path
        
        # 템플릿 리포트 생성기 모의
        with patch('src.reports.template_report.TemplateReport') as mock_template_report:
            mock_instance = MagicMock()
            mock_instance.generate_report.return_value = {"content": "테스트 내용"}
            mock_instance.output_report.return_value = "테스트 출력"
            mock_template_report.return_value = mock_instance
            
            # 리포트 생성
            result = self.report_generator.create_report(
                report_type=ReportGenerator.REPORT_TEMPLATE,
                data=self.test_data,
                output_format=ReportGenerator.FORMAT_CONSOLE,
                template_name=template_name
            )
            
            # 결과 검증
            self.assertEqual(result, "테스트 출력")
            mock_instance.generate_report.assert_called_once_with(self.test_data)
            mock_instance.output_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()