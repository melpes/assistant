# -*- coding: utf-8 -*-
"""
수동 거래 입력 도구 테스트
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from src.financial_tools.input_tools import (
    add_expense, add_income, update_transaction, batch_add_transactions,
    get_transaction_templates, apply_transaction_template,
    save_transaction_template, delete_transaction_template,
    get_autocomplete_suggestions
)

class TestInputTools(unittest.TestCase):
    """수동 거래 입력 도구 테스트 클래스"""
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    @patch('src.financial_tools.input_tools.TransactionRepository')
    def test_add_expense(self, mock_repo, mock_ingester):
        """add_expense 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.add_expense.return_value = {
            'transaction_id': 'test_id',
            'transaction_date': date(2024, 7, 15),
            'description': '테스트 지출',
            'amount': 10000,
            'transaction_type': 'expense',
            'category': '식비',
            'payment_method': '현금'
        }
        
        # 함수 호출
        result = add_expense(
            date='2024-07-15',
            amount=10000,
            description='테스트 지출',
            category='식비',
            payment_method='현금'
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction']['transaction_id'], 'test_id')
        self.assertEqual(result['transaction']['description'], '테스트 지출')
        mock_ingester_instance.add_expense.assert_called_once()
        mock_repo.return_value.create.assert_called_once()
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    @patch('src.financial_tools.input_tools.TransactionRepository')
    def test_add_income(self, mock_repo, mock_ingester):
        """add_income 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.add_income.return_value = {
            'transaction_id': 'test_id',
            'transaction_date': date(2024, 7, 15),
            'description': '테스트 수입',
            'amount': 50000,
            'transaction_type': 'income',
            'category': '급여',
            'payment_method': '계좌입금'
        }
        
        # 함수 호출
        result = add_income(
            date='2024-07-15',
            amount=50000,
            description='테스트 수입',
            category='급여',
            payment_method='계좌입금'
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction']['transaction_id'], 'test_id')
        self.assertEqual(result['transaction']['description'], '테스트 수입')
        mock_ingester_instance.add_income.assert_called_once()
        mock_repo.return_value.create.assert_called_once()
    
    @patch('src.financial_tools.input_tools.TransactionRepository')
    def test_update_transaction(self, mock_repo):
        """update_transaction 함수 테스트"""
        # 목 설정
        mock_transaction = MagicMock()
        mock_transaction.to_dict.return_value = {
            'transaction_id': 'test_id',
            'category': '식비',
            'payment_method': '현금',
            'memo': '업데이트 테스트'
        }
        mock_repo.return_value.get_by_transaction_id.return_value = mock_transaction
        
        # 함수 호출
        result = update_transaction(
            transaction_id='test_id',
            category='식비',
            memo='업데이트 테스트'
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction']['transaction_id'], 'test_id')
        self.assertEqual(result['transaction']['memo'], '업데이트 테스트')
        mock_repo.return_value.update.assert_called_once_with(mock_transaction)
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    @patch('src.financial_tools.input_tools.TransactionRepository')
    def test_batch_add_transactions(self, mock_repo, mock_ingester):
        """batch_add_transactions 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.batch_add_transactions.return_value = [
            {
                'transaction_id': 'test_id1',
                'transaction_date': date(2024, 7, 15),
                'description': '테스트 지출 1',
                'amount': 10000,
                'transaction_type': 'expense'
            },
            {
                'transaction_id': 'test_id2',
                'transaction_date': date(2024, 7, 15),
                'description': '테스트 지출 2',
                'amount': 20000,
                'transaction_type': 'expense'
            }
        ]
        
        # 함수 호출
        result = batch_add_transactions([
            {
                'date': '2024-07-15',
                'description': '테스트 지출 1',
                'amount': 10000,
                'transaction_type': 'expense'
            },
            {
                'date': '2024-07-15',
                'description': '테스트 지출 2',
                'amount': 20000,
                'transaction_type': 'expense'
            }
        ])
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(len(result['transactions']), 2)
        self.assertEqual(result['count'], 2)
        mock_ingester_instance.batch_add_transactions.assert_called_once()
        self.assertEqual(mock_repo.return_value.create.call_count, 2)
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    def test_get_transaction_templates(self, mock_ingester):
        """get_transaction_templates 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.get_templates.return_value = {
            'template1': {
                'description': '점심식사',
                'category': '식비',
                'payment_method': '현금'
            },
            'template2': {
                'description': '교통비',
                'category': '교통비',
                'payment_method': '체크카드결제'
            }
        }
        
        # 함수 호출
        result = get_transaction_templates('expense')
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(len(result['templates']), 2)
        self.assertEqual(result['count'], 2)
        mock_ingester_instance.get_templates.assert_called_once_with('expense')
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    @patch('src.financial_tools.input_tools.TransactionRepository')
    def test_apply_transaction_template(self, mock_repo, mock_ingester):
        """apply_transaction_template 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.get_templates.return_value = {
            'template1': {
                'description': '점심식사',
                'category': '식비',
                'payment_method': '현금'
            }
        }
        mock_ingester_instance.apply_template.return_value = {
            'transaction_id': 'test_id',
            'transaction_date': date(2024, 7, 15),
            'description': '점심식사',
            'amount': 10000,
            'transaction_type': 'expense',
            'category': '식비',
            'payment_method': '현금'
        }
        
        # 함수 호출
        result = apply_transaction_template(
            template_name='template1',
            date='2024-07-15',
            amount=10000
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction']['transaction_id'], 'test_id')
        self.assertEqual(result['transaction']['description'], '점심식사')
        mock_ingester_instance.apply_template.assert_called_once()
        mock_repo.return_value.create.assert_called_once()
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    def test_save_transaction_template(self, mock_ingester):
        """save_transaction_template 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.save_template.return_value = True
        
        # 함수 호출
        result = save_transaction_template(
            name='template1',
            description='점심식사',
            category='식비',
            payment_method='현금'
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['template']['name'], 'template1')
        self.assertEqual(result['template']['description'], '점심식사')
        mock_ingester_instance.save_template.assert_called_once()
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    def test_delete_transaction_template(self, mock_ingester):
        """delete_transaction_template 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.get_templates.return_value = {'template1': {}}
        mock_ingester_instance.delete_template.return_value = True
        
        # 함수 호출
        result = delete_transaction_template('template1')
        
        # 검증
        self.assertTrue(result['success'])
        mock_ingester_instance.delete_template.assert_called_once_with('template1', 'expense')
    
    @patch('src.financial_tools.input_tools.ManualIngester')
    def test_get_autocomplete_suggestions(self, mock_ingester):
        """get_autocomplete_suggestions 함수 테스트"""
        # 목 설정
        mock_ingester_instance = mock_ingester.return_value
        mock_ingester_instance.get_autocomplete_suggestions.return_value = {
            'category': '식비',
            'payment_method': '현금',
            'exact_match': True,
            'similar_descriptions': []
        }
        
        # 함수 호출
        result = get_autocomplete_suggestions('점심식사')
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['suggestions']['category'], '식비')
        self.assertTrue(result['suggestions']['exact_match'])
        mock_ingester_instance.get_autocomplete_suggestions.assert_called_once_with('점심식사', 'expense')

if __name__ == '__main__':
    unittest.main()