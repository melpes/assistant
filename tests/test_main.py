# -*- coding: utf-8 -*-
"""
메인 모듈 테스트
"""

import unittest
from unittest.mock import patch, mock_open

import main


class TestMain(unittest.TestCase):
    """메인 모듈 테스트 클래스"""
    
    @patch('main.run_general_agent')
    @patch('main.run_financial_agent')
    @patch('builtins.open', new_callable=mock_open, read_data="일정 추가해줘")
    def test_main_general_query(self, mock_file, mock_financial_agent, mock_general_agent):
        """일반 쿼리 테스트"""
        # Mock 설정
        mock_general_agent.return_value = "일반 에이전트 응답"
        
        # 함수 호출
        main.main()
        
        # 검증
        mock_file.assert_called_once_with("query.txt", "r", encoding="utf-8")
        mock_general_agent.assert_called_once()
        mock_financial_agent.assert_not_called()
    
    @patch('main.run_general_agent')
    @patch('main.run_financial_agent')
    @patch('builtins.open', new_callable=mock_open, read_data="지난달 지출 내역 보여줘")
    def test_main_financial_query(self, mock_file, mock_financial_agent, mock_general_agent):
        """금융 쿼리 테스트"""
        # Mock 설정
        mock_financial_agent.return_value = "금융 에이전트 응답"
        
        # 함수 호출
        main.main()
        
        # 검증
        mock_file.assert_called_once_with("query.txt", "r", encoding="utf-8")
        mock_financial_agent.assert_called_once()
        mock_general_agent.assert_not_called()
    
    @patch('main.GOOGLE_API_KEY', None)
    @patch('builtins.print')
    def test_main_invalid_api_key(self, mock_print):
        """유효하지 않은 API 키 테스트"""
        # 함수 호출
        main.main()
        
        # 검증
        mock_print.assert_any_call("오류: .env 파일에 GOOGLE_API_KEY를 설정해주세요.")
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('builtins.print')
    def test_main_file_not_found(self, mock_print, mock_open):
        """파일 없음 테스트"""
        # 함수 호출
        main.main()
        
        # 검증
        mock_print.assert_any_call("오류: query.txt 파일을 찾을 수 없습니다.")
    
    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('builtins.print')
    def test_main_empty_query(self, mock_print, mock_open):
        """빈 쿼리 테스트"""
        # 함수 호출
        main.main()
        
        # 검증
        mock_print.assert_any_call("오류: query.txt 파일이 비어있습니다.")


if __name__ == '__main__':
    unittest.main()