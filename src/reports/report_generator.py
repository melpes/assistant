# -*- coding: utf-8 -*-
"""
리포트 생성 시스템

다양한 리포트 생성기를 통합하고 관리합니다.
"""

import os
import json
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Type

from src.reports.base_report_generator import BaseReportGenerator
from src.reports.financial_summary_report import FinancialSummaryReport
from src.reports.transaction_detail_report import TransactionDetailReport
from src.reports.template_report import TemplateReport
from src.reports.report_scheduler import ReportScheduler
from src.repositories.config_repository import ConfigRepository

# 로거 설정
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    리포트 생성 시스템
    
    다양한 리포트 생성기를 통합하고 관리합니다.
    """
    
    # 리포트 유형 상수
    REPORT_FINANCIAL_SUMMARY = "financial_summary"
    REPORT_TRANSACTION_DETAIL = "transaction_detail"
    REPORT_TEMPLATE = "template"
    
    # 출력 형식 상수
    FORMAT_CONSOLE = BaseReportGenerator.FORMAT_CONSOLE
    FORMAT_JSON = BaseReportGenerator.FORMAT_JSON
    FORMAT_CSV = BaseReportGenerator.FORMAT_CSV
    
    def __init__(self, config_repository: ConfigRepository):
        """
        리포트 생성 시스템 초기화
        
        Args:
            config_repository: 설정 저장소
        """
        self.config_repository = config_repository
        self.report_templates = {}
        self.scheduler = ReportScheduler(config_repository)
        
        # 기본 템플릿 디렉토리
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        os.makedirs(self.template_dir, exist_ok=True)
        
        # 기본 출력 디렉토리
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 템플릿 로드
        self._load_templates()
    
    def create_report(self, report_type: str, data: Dict[str, Any], 
                    output_format: str = FORMAT_CONSOLE,
                    output_file: Optional[str] = None,
                    template_name: Optional[str] = None) -> Union[str, None]:
        """
        리포트를 생성합니다.
        
        Args:
            report_type: 리포트 유형
            data: 리포트 데이터
            output_format: 출력 형식
            output_file: 출력 파일 경로 (선택)
            template_name: 템플릿 이름 (템플릿 리포트인 경우)
            
        Returns:
            Union[str, None]: 출력 문자열 또는 None
        """
        # 리포트 생성기 생성
        report_generator = self._create_report_generator(report_type, template_name)
        
        if not report_generator:
            logger.error(f"지원하지 않는 리포트 유형: {report_type}")
            return None
        
        # 리포트 생성
        report_generator.generate_report(data)
        
        # 리포트 출력
        return report_generator.output_report(output_format, output_file)
    
    def schedule_report(self, report_id: str, report_type: str,
                      data_provider: Callable[[], Dict[str, Any]],
                      schedule_type: str, schedule_params: Dict[str, Any],
                      output_format: str = FORMAT_JSON,
                      output_dir: Optional[str] = None,
                      template_name: Optional[str] = None) -> bool:
        """
        리포트 생성을 예약합니다.
        
        Args:
            report_id: 리포트 ID
            report_type: 리포트 유형
            data_provider: 데이터 제공 함수
            schedule_type: 스케줄 유형
            schedule_params: 스케줄 매개변수
            output_format: 출력 형식
            output_dir: 출력 디렉토리 (선택)
            template_name: 템플릿 이름 (템플릿 리포트인 경우)
            
        Returns:
            bool: 성공 여부
        """
        # 리포트 생성기 생성
        report_generator = self._create_report_generator(report_type, template_name)
        
        if not report_generator:
            logger.error(f"지원하지 않는 리포트 유형: {report_type}")
            return False
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = os.path.join(self.output_dir, report_id)
        
        # 스케줄러에 리포트 추가
        return self.scheduler.add_scheduled_report(
            report_id=report_id,
            report_generator=report_generator,
            report_data_provider=data_provider,
            schedule_type=schedule_type,
            schedule_params=schedule_params,
            output_format=output_format,
            output_dir=output_dir
        )
    
    def get_scheduled_reports(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 예약된 리포트 정보를 반환합니다.
        
        Returns:
            Dict[str, Dict[str, Any]]: 예약된 리포트 정보
        """
        return self.scheduler.get_scheduled_reports()
    
    def update_scheduled_report(self, report_id: str, 
                              schedule_type: Optional[str] = None,
                              schedule_params: Optional[Dict[str, Any]] = None,
                              output_format: Optional[str] = None,
                              output_dir: Optional[str] = None) -> bool:
        """
        예약된 리포트를 업데이트합니다.
        
        Args:
            report_id: 리포트 ID
            schedule_type: 스케줄 유형 (선택)
            schedule_params: 스케줄 매개변수 (선택)
            output_format: 출력 형식 (선택)
            output_dir: 출력 디렉토리 (선택)
            
        Returns:
            bool: 성공 여부
        """
        return self.scheduler.update_scheduled_report(
            report_id=report_id,
            schedule_type=schedule_type,
            schedule_params=schedule_params,
            output_format=output_format,
            output_dir=output_dir
        )
    
    def remove_scheduled_report(self, report_id: str) -> bool:
        """
        예약된 리포트를 제거합니다.
        
        Args:
            report_id: 리포트 ID
            
        Returns:
            bool: 성공 여부
        """
        return self.scheduler.remove_scheduled_report(report_id)
    
    def run_report_now(self, report_id: str) -> bool:
        """
        지정된 리포트를 즉시 실행합니다.
        
        Args:
            report_id: 리포트 ID
            
        Returns:
            bool: 성공 여부
        """
        return self.scheduler.run_report_now(report_id)
    
    def start_scheduler(self) -> None:
        """
        스케줄러를 시작합니다.
        """
        self.scheduler.start()
    
    def stop_scheduler(self) -> None:
        """
        스케줄러를 중지합니다.
        """
        self.scheduler.stop()
    
    def add_template(self, template_name: str, template_content: str) -> bool:
        """
        템플릿을 추가합니다.
        
        Args:
            template_name: 템플릿 이름
            template_content: 템플릿 내용
            
        Returns:
            bool: 성공 여부
        """
        # 템플릿 파일 저장
        template_path = os.path.join(self.template_dir, f"{template_name}.template")
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # 템플릿 목록에 추가
            self.report_templates[template_name] = template_path
            
            # 템플릿 목록 저장
            self._save_templates()
            
            logger.info(f"템플릿이 추가되었습니다: {template_name}")
            return True
        
        except Exception as e:
            logger.error(f"템플릿 추가 중 오류 발생: {str(e)}")
            return False
    
    def remove_template(self, template_name: str) -> bool:
        """
        템플릿을 제거합니다.
        
        Args:
            template_name: 템플릿 이름
            
        Returns:
            bool: 성공 여부
        """
        if template_name not in self.report_templates:
            logger.warning(f"존재하지 않는 템플릿: {template_name}")
            return False
        
        template_path = self.report_templates[template_name]
        
        try:
            # 템플릿 파일 삭제
            if os.path.exists(template_path):
                os.remove(template_path)
            
            # 템플릿 목록에서 제거
            del self.report_templates[template_name]
            
            # 템플릿 목록 저장
            self._save_templates()
            
            logger.info(f"템플릿이 제거되었습니다: {template_name}")
            return True
        
        except Exception as e:
            logger.error(f"템플릿 제거 중 오류 발생: {str(e)}")
            return False
    
    def get_templates(self) -> Dict[str, str]:
        """
        모든 템플릿 정보를 반환합니다.
        
        Returns:
            Dict[str, str]: 템플릿 정보 (이름: 경로)
        """
        return self.report_templates.copy()
    
    def _create_report_generator(self, report_type: str, template_name: Optional[str] = None) -> Optional[BaseReportGenerator]:
        """
        리포트 유형에 맞는 생성기를 생성합니다.
        
        Args:
            report_type: 리포트 유형
            template_name: 템플릿 이름 (템플릿 리포트인 경우)
            
        Returns:
            Optional[BaseReportGenerator]: 리포트 생성기
        """
        if report_type == self.REPORT_FINANCIAL_SUMMARY:
            return FinancialSummaryReport()
        
        elif report_type == self.REPORT_TRANSACTION_DETAIL:
            return TransactionDetailReport()
        
        elif report_type == self.REPORT_TEMPLATE:
            if not template_name or template_name not in self.report_templates:
                logger.error(f"템플릿을 찾을 수 없습니다: {template_name}")
                return None
            
            template_path = self.report_templates[template_name]
            return TemplateReport(template_path=template_path)
        
        return None
    
    def _load_templates(self) -> None:
        """
        저장된 템플릿 목록을 로드합니다.
        """
        try:
            # 설정 저장소에서 템플릿 목록 로드
            templates_json = self.config_repository.get_config("report_templates")
            
            if templates_json:
                self.report_templates = json.loads(templates_json)
            
            # 템플릿 파일 존재 여부 확인
            for template_name, template_path in list(self.report_templates.items()):
                if not os.path.exists(template_path):
                    logger.warning(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
                    del self.report_templates[template_name]
            
            logger.debug(f"템플릿 목록이 로드되었습니다: {len(self.report_templates)}개")
        
        except Exception as e:
            logger.error(f"템플릿 목록 로드 중 오류 발생: {str(e)}")
            self.report_templates = {}
    
    def _save_templates(self) -> None:
        """
        템플릿 목록을 저장소에 저장합니다.
        """
        try:
            self.config_repository.set_config("report_templates", json.dumps(self.report_templates))
            logger.debug("템플릿 목록이 저장되었습니다.")
        except Exception as e:
            logger.error(f"템플릿 목록 저장 중 오류 발생: {str(e)}")