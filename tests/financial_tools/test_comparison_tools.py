# -*- coding: utf-8 -*-
"""
비교 분석 도구 테스트

비교 분석 도구 함수들에 대한 단위 테스트를 수행합니다.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
import json
ort sys

# 모듈 모킹
sys.modules['src.repositorock()
sys.modules['src.analyzers.comparison_analyz()
sys.modules['src.models'] = MagicMock()
sys.ome')

# 이제 모듈을 가져올 수 있습니다
from src.financial_tools.comparison_tools import (
    compare_periods,
    compare_months,
    compare_with_previous_perio,
    compare_with_previous_month,
    find_significant_changes
)


Case):
    """비교 분석 도구 테스트 클래스"""
    
    
        """테스트 설정"""
        # 테스트 데이터 설정
        self.mock_co
            'period1': {
                'start_date': '2023-01-01',
                'end_date': '2023-01-31',
                'days': 31,
                'transaction_count': 50,
    01'
            },
            'period2': {
                'sta,
                'end_date': '2023-02,
    
                'traount': 45,
                'yea23-02'
            },
            'summary_comparison': {
                'total1'00000.0,
                'total2': 900000.0,
                'diff': -100000.0,
                'diff_perce,
                'count1': 50,
                'count2': 45,
              iff': -5,
                'count_d,
                'avg1': 20000.0,
                'avg2': 20000.0,
                'avg_diff':0.0,
                'avg_diff_percentage': 0,
                'daily_avg1': 32258.06,
              .86,
                'daily_avg_diff': -
                'daily_avg_diff_perc -0.36
            },
            'category_comparison': [
                {
                    'category '식비',
                    'amount1'0.0,
                    'amount2': 28
                    'diff': -20000.0,
                    'diff_percen7,
                    'count1': 20,
                    'count2': 18,
                    'count_diff': -2,
                    'count_diff_percent: -10.0
                },
                {
                    'category': '교통',
              ,
                    'amount2': 12000
                 
                    'diff_percentage'0,
                    'count1': 10,
                    'count2': 12,
                    'count_diff': 2,
                    'count_diff_percentage': 20.0
                },
                {
                    'category': '쇼핑',
                    'amount1': 200000.0,
                  0.0,
                 0,
                    'diff_percentage'5.0,
                    'count1': 5,
                    'count2': 4,
                    'count_diff': -1,
                    'count_diff_percentage':20.0
                }
            ],
            'payment_method_comparis': [
                {
                   '신용카드',
                 0.0,
                    'amount2': 650000.0,
                    'diff': -50000.0,
                    'diff_percentage': -7.14,
                    'count1': 35,
                    'count2': 32,
                    'count_diff'
                    'count_diff_8.57
                },
                {
                 '현금',
              000.0,
                    'amount2': 250000.0,
                 0,
                    'diff_percentage': -16.67
                    'count1': 15,
                    'count2': 13,
                    'count_diff': -2,
                    'count_diff_percentage': 13.33
                }
            ],
            'daily_avg_comparison': {
                'daily_avg1': 32258.06,
                'd86,
                '2,
                'diff_percentage': -0.36,
                'period1_days': 31,
                'period2_days': 28
            }
        }
    
    @patch('src.financial_tools.c
    @patch('src.financial_tools.compa
    def test_compare_periods(self, mock_analyzer_cl):
        """기간 비교 트"""
        # 목 설정
        mock_repo = mock_repo_class.rlue
        mock_analyzer = mock_analyzer_clue
        mock_analyzer.compare_periods.r
        
        # 함수 호출
        result = compare_periods(
            period1_start="2023-01
            p",
         
    ",
            transaction_type="expense",
            group_by="category"
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['period1']['start_date']-01')
        self.assertEqual(result['period2']['start_date'], '2023-02-01')
        0000.0)
        self.as
        self.assertEqual(len(resu']), 2)
        self.assertEqual(len(result['to
        
        # 메서드 호출 검증
        mock_analyzer_class.assert_cao)
        mock_analyzer.compare_periods.a()
    
    @patc)
    @patalyzer')
    def tests):
        """월 비교 분석 테스트"""
        # 목 설정
        mock_repo = mock_repo_class.return_value
        mock_analyzer = mock_analyzer_class.return_value
        mock_analyzer.compare_months.return_value = se
        
        # 함수 호출
        onths(
            year1=2,
            month1=1,
            year2=2023,
    =2,
            transaction_type="expense",
            group_by="category"
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['period1']['year_month']')
        self.assertEqual(result['period2']['year_month'], '2023-02')
        
        # 메서드 호
        mock_analyzer_class.asse_repo)
        mock_analyzer.c)
    
    @patch('src.financiory')
    @patch('src.finan)
    def test_compare_with_previous_peri_class):
        """이전 기간 비교 분석 테스트"""
        #목 설정
        
        mock_value
        mock_analyzer.compare_with_previout
        
        # 함수 호출
        d(
            start_d01",
            end_date="2023-02-28",
            transaction_type="expense",
            group_by="category"
        )
      
        # 검증
        self.assertTrue(result['success'])
        
        # 메서드 호출 검증
        mock_ao)
        mock_analyzer.compare_with_previous_perie()
    
    @patch('src.financial_tools.comparison_tools.TransactionRepository')
    @pat)
    def test_cos):
        """이전 월 비교 분석 테스트"""
        # 목 설정
        mock_repo = mock_repo_clas
        mock_analyzer = mock_analyzer_cue
        mock_analyzer.compare_wesult
        
        함수 호출
        resu
            year=2023,
          month=2,
            transacense",
            group_by="category"
        )
        
        # 검증
        self.assertTrue(result['success'])
        
        # 메서드 호출 검증
        mock_a_repo)
        mock_analyzer.compare_with_previous_montnce()
    
    @patch('src.financial_tools.comparison_tools.TransactionRepository')
    @pat
    def test_filass):
        """주요 변동 사항 분석 테스트"""
        # 목 설정
        mock_repo = e
        mock_analyzer = mock_analyzer_ce
        mock_analyzer.compare_p
        
        # 함수 호출
        resuchanges(
            period1_start="2023-01-01",
        ",
            period2,
            period2_end="2023-02-28",
            transaction_type="expense",
            threshold_percentage=15.0,
         
    
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn('signifresult)
        self.a)
        self.assertIn('decreases', result['signinges'])
        
        # 메서드 호출 검증
        o)
        mock_ane()
    
    @patch('src.financial_tools.compari)
    @patch('src.financial_tools.compa
    def test_error_handling(self, mock_:
        """에러 처리 테스트"""
        # 목 설정
        mock_repo = mock_repo_class.re_value
        mock_analyzer = mock_arn_value
        m
        
        # 함수출
        result = compare_periods(
            period1_start="2023-01-01",
            period1_end="2023-01-31",
            period2_start="2023-02-01",
        ",
            transace",
            group_by="category"
        )
        
        # 검증
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('])


if __name__ == '__main__':
    unittest.main()