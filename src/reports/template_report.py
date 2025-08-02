# -*- coding: utf-8 -*-
"""
템플릿 기반 리포트 생성기

사용자 정의 템플릿을 기반으로 리포트를 생성합니다.
"""

import os
import re
import json
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable

from src.reports.base_report_generator import BaseReportGenerator

# 로거 설정
logger = logging.getLogger(__name__)


class TemplateReport(BaseReportGenerator):
    """
    템플릿 기반 리포트 생성기
    
    사용자 정의 템플릿을 기반으로 리포트를 생성합니다.
    """
    
    # 템플릿 변수 패턴 (예: {{variable}})
    VARIABLE_PATTERN = r'{{([\w\.\[\]]+)}}'
    
    # 조건부 블록 패턴 (예: {% if condition %}...{% endif %})
    CONDITION_START_PATTERN = r'{%\s*if\s+([\w\.\[\]]+)\s*%}'
    CONDITION_END_PATTERN = r'{%\s*endif\s*%}'
    
    # 반복 블록 패턴 (예: {% for item in items %}...{% endfor %})
    LOOP_START_PATTERN = r'{%\s*for\s+([\w]+)\s+in\s+([\w\.\[\]]+)\s*%}'
    LOOP_END_PATTERN = r'{%\s*endfor\s*%}'
    
    def __init__(self, template_path: Optional[str] = None, template_content: Optional[str] = None):
        """
        템플릿 리포트 생성기 초기화
        
        Args:
            template_path: 템플릿 파일 경로 (선택)
            template_content: 템플릿 내용 (선택)
        """
        super().__init__()
        self.template_path = template_path
        self.template_content = template_content
        self.template = None
        self.filters = {}
        
        # 기본 필터 등록
        self.register_filter('format_date', self._format_date)
        self.register_filter('format_amount', self._format_amount)
    
    def load_template(self, template_path: Optional[str] = None) -> str:
        """
        템플릿 파일을 로드합니다.
        
        Args:
            template_path: 템플릿 파일 경로 (선택)
            
        Returns:
            str: 템플릿 내용
        """
        path = template_path or self.template_path
        
        if not path:
            raise ValueError("템플릿 경로가 지정되지 않았습니다.")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
        
        return self.template_content
    
    def set_template_content(self, content: str) -> None:
        """
        템플릿 내용을 직접 설정합니다.
        
        Args:
            content: 템플릿 내용
        """
        self.template_content = content
    
    def register_filter(self, name: str, func: Callable) -> None:
        """
        템플릿 필터를 등록합니다.
        
        Args:
            name: 필터 이름
            func: 필터 함수
        """
        self.filters[name] = func
    
    def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        템플릿 기반 리포트를 생성합니다.
        
        Args:
            data: 리포트 데이터
            
        Returns:
            Dict[str, Any]: 리포트 데이터
        """
        # 템플릿 로드
        if not self.template_content:
            if self.template_path:
                self.load_template()
            else:
                raise ValueError("템플릿 내용이나 경로가 지정되지 않았습니다.")
        
        # 리포트 데이터 설정
        self.report_data = {
            "content": self._render_template(self.template_content, data),
            "data": data,
            "generated_at": datetime.now().isoformat(),
            "template": self.template_path or "custom_template"
        }
        
        return self.report_data
    
    def _output_console(self) -> str:
        """
        콘솔 출력 형식으로 변환합니다.
        
        Returns:
            str: 콘솔 출력용 문자열
        """
        if "content" in self.report_data:
            return self.report_data["content"]
        
        return super()._output_console()
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        템플릿을 렌더링합니다.
        
        Args:
            template: 템플릿 문자열
            data: 데이터
            
        Returns:
            str: 렌더링된 문자열
        """
        # 조건부 블록 처리
        template = self._process_conditional_blocks(template, data)
        
        # 반복 블록 처리
        template = self._process_loop_blocks(template, data)
        
        # 변수 치환
        template = self._replace_variables(template, data)
        
        return template
    
    def _process_conditional_blocks(self, template: str, data: Dict[str, Any]) -> str:
        """
        조건부 블록을 처리합니다.
        
        Args:
            template: 템플릿 문자열
            data: 데이터
            
        Returns:
            str: 처리된 템플릿 문자열
        """
        pattern = f"{self.CONDITION_START_PATTERN}(.*?){self.CONDITION_END_PATTERN}"
        matches = list(re.finditer(pattern, template, re.DOTALL))
        
        # 뒤에서부터 처리 (중첩 블록 처리를 위해)
        for match in reversed(matches):
            condition_var = match.group(1)
            content = match.group(2)
            
            # 조건 변수 값 가져오기
            condition_value = self._get_variable_value(condition_var, data)
            
            # 조건에 따라 내용 포함 여부 결정
            if condition_value:
                template = template[:match.start()] + content + template[match.end():]
            else:
                template = template[:match.start()] + template[match.end():]
        
        return template
    
    def _process_loop_blocks(self, template: str, data: Dict[str, Any]) -> str:
        """
        반복 블록을 처리합니다.
        
        Args:
            template: 템플릿 문자열
            data: 데이터
            
        Returns:
            str: 처리된 템플릿 문자열
        """
        pattern = f"{self.LOOP_START_PATTERN}(.*?){self.LOOP_END_PATTERN}"
        matches = list(re.finditer(pattern, template, re.DOTALL))
        
        # 뒤에서부터 처리 (중첩 블록 처리를 위해)
        for match in reversed(matches):
            item_var = match.group(1)
            items_var = match.group(2)
            content = match.group(3)
            
            # 반복 대상 목록 가져오기
            items = self._get_variable_value(items_var, data)
            
            if not items or not isinstance(items, (list, tuple)):
                template = template[:match.start()] + template[match.end():]
                continue
            
            # 각 항목에 대해 내용 생성
            result = []
            for item in items:
                # 임시 컨텍스트 생성
                temp_data = data.copy()
                temp_data[item_var] = item
                
                # 내용 렌더링
                item_content = self._replace_variables(content, temp_data)
                result.append(item_content)
            
            # 결과 병합
            template = template[:match.start()] + "".join(result) + template[match.end():]
        
        return template
    
    def _replace_variables(self, template: str, data: Dict[str, Any]) -> str:
        """
        템플릿 변수를 치환합니다.
        
        Args:
            template: 템플릿 문자열
            data: 데이터
            
        Returns:
            str: 치환된 템플릿 문자열
        """
        def replace_var(match):
            var_expr = match.group(1)
            
            # 필터 처리 (예: variable|filter)
            if '|' in var_expr:
                var_name, filter_name = var_expr.split('|', 1)
                var_name = var_name.strip()
                filter_name = filter_name.strip()
                
                value = self._get_variable_value(var_name, data)
                
                # 필터 적용
                if filter_name in self.filters:
                    return str(self.filters[filter_name](value))
                else:
                    logger.warning(f"정의되지 않은 필터: {filter_name}")
                    return str(value)
            else:
                # 일반 변수
                value = self._get_variable_value(var_expr, data)
                return str(value) if value is not None else ""
        
        return re.sub(self.VARIABLE_PATTERN, replace_var, template)
    
    def _get_variable_value(self, var_expr: str, data: Dict[str, Any]) -> Any:
        """
        변수 표현식에서 값을 가져옵니다.
        
        Args:
            var_expr: 변수 표현식 (예: user.name, items[0].title)
            data: 데이터
            
        Returns:
            Any: 변수 값
        """
        # 배열 인덱스 처리 (예: items[0])
        array_pattern = r'(\w+)\[(\d+)\]'
        while re.search(array_pattern, var_expr):
            var_expr = re.sub(array_pattern, r'\1.\2', var_expr)
        
        # 점 표기법 처리 (예: user.name)
        parts = var_expr.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif isinstance(value, (list, tuple)) and part.isdigit():
                index = int(part)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return None
            else:
                return None
        
        return value