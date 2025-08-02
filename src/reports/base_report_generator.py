# -*- coding: utf-8 -*-
"""
기본 리포트 생성기 추상 클래스

모든 리포트 생성기의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Union, TextIO
import os
import json
import csv
import logging

# 로거 설정
logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """
    기본 리포트 생성기 추상 클래스
    
    모든 리포트 생성기의 기본 인터페이스를 정의합니다.
    """
    
    # 출력 형식 상수
    FORMAT_CONSOLE = "console"
    FORMAT_JSON = "json"
    FORMAT_CSV = "csv"
    
    def __init__(self):
        """리포트 생성기 초기화"""
        self.report_data = {}
    
    @abstractmethod
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        리포트 데이터를 생성합니다.
        
        Args:
            data: 분석 결과 데이터
            
        Returns:
            Dict[str, Any]: 리포트 데이터
        """
        pass
    
    def output_report(self, output_format: str = FORMAT_CONSOLE, 
                     output_file: Optional[str] = None) -> Union[str, None]:
        """
        리포트를 지정된 형식으로 출력합니다.
        
        Args:
            output_format: 출력 형식 (console, json, csv)
            output_file: 출력 파일 경로 (선택)
            
        Returns:
            Union[str, None]: 출력 문자열 또는 None
        """
        if not self.report_data:
            logger.error("리포트 데이터가 없습니다. generate_report()를 먼저 호출하세요.")
            return None
        
        if output_format == self.FORMAT_CONSOLE:
            return self._output_console()
        elif output_format == self.FORMAT_JSON:
            return self._output_json(output_file)
        elif output_format == self.FORMAT_CSV:
            return self._output_csv(output_file)
        else:
            logger.error(f"지원하지 않는 출력 형식: {output_format}")
            return None
    
    def _output_console(self) -> str:
        """
        콘솔 출력 형식으로 변환합니다.
        
        Returns:
            str: 콘솔 출력용 문자열
        """
        # 기본 구현은 JSON을 예쁘게 출력
        return json.dumps(self.report_data, indent=2, ensure_ascii=False)
    
    def _output_json(self, output_file: Optional[str] = None) -> str:
        """
        JSON 형식으로 출력합니다.
        
        Args:
            output_file: 출력 파일 경로 (선택)
            
        Returns:
            str: JSON 문자열
        """
        json_str = json.dumps(self.report_data, indent=2, ensure_ascii=False)
        
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"JSON 리포트가 {output_file}에 저장되었습니다.")
        
        return json_str
    
    def _output_csv(self, output_file: Optional[str] = None) -> str:
        """
        CSV 형식으로 출력합니다.
        
        Args:
            output_file: 출력 파일 경로 (선택)
            
        Returns:
            str: CSV 문자열
        """
        # JSON을 평탄화하여 CSV로 변환
        flat_data = self._flatten_dict(self.report_data)
        
        # CSV 문자열 생성
        output = []
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(flat_data.keys())
                writer.writerow(flat_data.values())
                output = f"CSV 리포트가 {output_file}에 저장되었습니다."
                logger.info(output)
        else:
            # 메모리에 CSV 생성
            import io
            output_buffer = io.StringIO()
            writer = csv.writer(output_buffer)
            writer.writerow(flat_data.keys())
            writer.writerow(flat_data.values())
            output = output_buffer.getvalue()
            output_buffer.close()
        
        return output
    
    def _flatten_dict(self, nested_dict: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """
        중첩된 딕셔너리를 평탄화합니다.
        
        Args:
            nested_dict: 중첩된 딕셔너리
            prefix: 키 접두사
            
        Returns:
            Dict[str, Any]: 평탄화된 딕셔너리
        """
        flat_dict = {}
        
        for key, value in nested_dict.items():
            new_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                flat_dict.update(self._flatten_dict(value, f"{new_key}_"))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flat_dict.update(self._flatten_dict(item, f"{new_key}_{i}_"))
                    else:
                        flat_dict[f"{new_key}_{i}"] = item
            else:
                flat_dict[new_key] = value
        
        return flat_dict
    
    def _format_date(self, date_obj: Union[date, datetime, str]) -> str:
        """
        날짜를 포맷팅합니다.
        
        Args:
            date_obj: 날짜 객체 또는 문자열
            
        Returns:
            str: 포맷팅된 날짜 문자열
        """
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.fromisoformat(date_obj)
            except ValueError:
                return date_obj
        
        if isinstance(date_obj, (date, datetime)):
            return date_obj.strftime("%Y-%m-%d")
        
        return str(date_obj)
    
    def _format_amount(self, amount: Union[int, float, str]) -> str:
        """
        금액을 포맷팅합니다.
        
        Args:
            amount: 금액
            
        Returns:
            str: 포맷팅된 금액 문자열
        """
        if isinstance(amount, str):
            # 이미 포맷팅된 문자열인 경우
            if '원' in amount:
                return amount
            try:
                amount = float(amount.replace(',', ''))
            except ValueError:
                return amount
        
        return f"{amount:,}원"