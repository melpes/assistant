# -*- coding: utf-8 -*-
"""
리포트 스케줄러

정기적인 리포트 생성을 예약하고 관리합니다.
"""

import os
import json
import logging
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable

from src.reports.base_report_generator import BaseReportGenerator
from src.repositories.config_repository import ConfigRepository

# 로거 설정
logger = logging.getLogger(__name__)


class ReportScheduler:
    """
    리포트 스케줄러
    
    정기적인 리포트 생성을 예약하고 관리합니다.
    """
    
    # 스케줄 유형
    SCHEDULE_DAILY = "daily"
    SCHEDULE_WEEKLY = "weekly"
    SCHEDULE_MONTHLY = "monthly"
    
    def __init__(self, config_repository: ConfigRepository):
        """
        리포트 스케줄러 초기화
        
        Args:
            config_repository: 설정 저장소
        """
        self.config_repository = config_repository
        self.scheduled_reports = {}
        self.running = False
        self.scheduler_thread = None
    
    def add_scheduled_report(self, report_id: str, report_generator: BaseReportGenerator,
                           report_data_provider: Callable[[], Dict[str, Any]],
                           schedule_type: str, schedule_params: Dict[str, Any],
                           output_format: str = BaseReportGenerator.FORMAT_JSON,
                           output_dir: str = "reports") -> bool:
        """
        예약된 리포트를 추가합니다.
        
        Args:
            report_id: 리포트 ID
            report_generator: 리포트 생성기
            report_data_provider: 리포트 데이터 제공 함수
            schedule_type: 스케줄 유형 (daily, weekly, monthly)
            schedule_params: 스케줄 매개변수
            output_format: 출력 형식
            output_dir: 출력 디렉토리
            
        Returns:
            bool: 성공 여부
        """
        if report_id in self.scheduled_reports:
            logger.warning(f"이미 존재하는 리포트 ID: {report_id}")
            return False
        
        # 스케줄 설정 검증
        if not self._validate_schedule(schedule_type, schedule_params):
            logger.error(f"잘못된 스케줄 설정: {schedule_type}, {schedule_params}")
            return False
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 예약된 리포트 정보 저장
        self.scheduled_reports[report_id] = {
            "report_generator": report_generator,
            "report_data_provider": report_data_provider,
            "schedule_type": schedule_type,
            "schedule_params": schedule_params,
            "output_format": output_format,
            "output_dir": output_dir,
            "last_run": None,
            "next_run": self._calculate_next_run(schedule_type, schedule_params)
        }
        
        # 설정 저장소에 저장
        self._save_schedule_config()
        
        # 스케줄러에 작업 등록
        self._schedule_report(report_id)
        
        logger.info(f"리포트 스케줄 추가됨: {report_id}, 다음 실행: {self.scheduled_reports[report_id]['next_run']}")
        return True
    
    def remove_scheduled_report(self, report_id: str) -> bool:
        """
        예약된 리포트를 제거합니다.
        
        Args:
            report_id: 리포트 ID
            
        Returns:
            bool: 성공 여부
        """
        if report_id not in self.scheduled_reports:
            logger.warning(f"존재하지 않는 리포트 ID: {report_id}")
            return False
        
        # 스케줄러에서 작업 제거
        schedule.clear(report_id)
        
        # 예약된 리포트 정보 제거
        del self.scheduled_reports[report_id]
        
        # 설정 저장소에 저장
        self._save_schedule_config()
        
        logger.info(f"리포트 스케줄 제거됨: {report_id}")
        return True
    
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
        if report_id not in self.scheduled_reports:
            logger.warning(f"존재하지 않는 리포트 ID: {report_id}")
            return False
        
        report_info = self.scheduled_reports[report_id]
        
        # 스케줄 설정 업데이트
        if schedule_type is not None:
            new_schedule_params = schedule_params or report_info["schedule_params"]
            
            if not self._validate_schedule(schedule_type, new_schedule_params):
                logger.error(f"잘못된 스케줄 설정: {schedule_type}, {new_schedule_params}")
                return False
            
            report_info["schedule_type"] = schedule_type
            report_info["schedule_params"] = new_schedule_params
            report_info["next_run"] = self._calculate_next_run(schedule_type, new_schedule_params)
            
            # 스케줄러에서 작업 제거 후 다시 등록
            schedule.clear(report_id)
            self._schedule_report(report_id)
        
        # 출력 형식 업데이트
        if output_format is not None:
            report_info["output_format"] = output_format
        
        # 출력 디렉토리 업데이트
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
            report_info["output_dir"] = output_dir
        
        # 설정 저장소에 저장
        self._save_schedule_config()
        
        logger.info(f"리포트 스케줄 업데이트됨: {report_id}, 다음 실행: {report_info['next_run']}")
        return True
    
    def get_scheduled_reports(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 예약된 리포트 정보를 반환합니다.
        
        Returns:
            Dict[str, Dict[str, Any]]: 예약된 리포트 정보
        """
        result = {}
        
        for report_id, report_info in self.scheduled_reports.items():
            # 객체 참조를 제외한 정보만 복사
            result[report_id] = {
                "schedule_type": report_info["schedule_type"],
                "schedule_params": report_info["schedule_params"],
                "output_format": report_info["output_format"],
                "output_dir": report_info["output_dir"],
                "last_run": report_info.get("last_run"),
                "next_run": report_info.get("next_run")
            }
        
        return result
    
    def start(self) -> None:
        """
        스케줄러를 시작합니다.
        """
        if self.running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        # 저장된 스케줄 설정 로드
        self._load_schedule_config()
        
        # 모든 리포트 스케줄 등록
        for report_id in self.scheduled_reports:
            self._schedule_report(report_id)
        
        # 스케줄러 스레드 시작
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("리포트 스케줄러가 시작되었습니다.")
    
    def stop(self) -> None:
        """
        스케줄러를 중지합니다.
        """
        if not self.running:
            logger.warning("스케줄러가 실행 중이 아닙니다.")
            return
        
        # 스케줄러 중지
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1.0)
        
        # 모든 작업 제거
        schedule.clear()
        
        logger.info("리포트 스케줄러가 중지되었습니다.")
    
    def run_report_now(self, report_id: str) -> bool:
        """
        지정된 리포트를 즉시 실행합니다.
        
        Args:
            report_id: 리포트 ID
            
        Returns:
            bool: 성공 여부
        """
        if report_id not in self.scheduled_reports:
            logger.warning(f"존재하지 않는 리포트 ID: {report_id}")
            return False
        
        # 리포트 실행
        self._generate_report(report_id)
        
        logger.info(f"리포트가 즉시 실행되었습니다: {report_id}")
        return True
    
    def _run_scheduler(self) -> None:
        """
        스케줄러 스레드 실행 함수
        """
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def _schedule_report(self, report_id: str) -> None:
        """
        리포트를 스케줄러에 등록합니다.
        
        Args:
            report_id: 리포트 ID
        """
        report_info = self.scheduled_reports[report_id]
        schedule_type = report_info["schedule_type"]
        schedule_params = report_info["schedule_params"]
        
        # 스케줄 유형에 따라 작업 등록
        job = schedule.every()
        
        if schedule_type == self.SCHEDULE_DAILY:
            time_str = schedule_params.get("time", "00:00")
            job.day.at(time_str)
        
        elif schedule_type == self.SCHEDULE_WEEKLY:
            day = schedule_params.get("day", "monday")
            time_str = schedule_params.get("time", "00:00")
            
            if day == "monday":
                job.monday.at(time_str)
            elif day == "tuesday":
                job.tuesday.at(time_str)
            elif day == "wednesday":
                job.wednesday.at(time_str)
            elif day == "thursday":
                job.thursday.at(time_str)
            elif day == "friday":
                job.friday.at(time_str)
            elif day == "saturday":
                job.saturday.at(time_str)
            elif day == "sunday":
                job.sunday.at(time_str)
        
        elif schedule_type == self.SCHEDULE_MONTHLY:
            day = schedule_params.get("day", 1)
            time_str = schedule_params.get("time", "00:00")
            
            # 매월 특정 일에 실행
            # (schedule 라이브러리는 매월 특정 일 실행을 직접 지원하지 않아 커스텀 로직 필요)
            job.day.at(time_str).do(self._check_monthly_schedule, report_id=report_id, day=day)
            return
        
        # 작업 등록
        job.do(self._generate_report, report_id=report_id).tag(report_id)
    
    def _check_monthly_schedule(self, report_id: str, day: int) -> None:
        """
        매월 특정 일 스케줄 확인
        
        Args:
            report_id: 리포트 ID
            day: 실행할 날짜
        """
        today = datetime.now().day
        
        # 오늘이 지정된 날짜인 경우 리포트 생성
        if today == day:
            self._generate_report(report_id)
    
    def _generate_report(self, report_id: str) -> None:
        """
        리포트를 생성합니다.
        
        Args:
            report_id: 리포트 ID
        """
        try:
            report_info = self.scheduled_reports[report_id]
            
            # 리포트 데이터 가져오기
            data = report_info["report_data_provider"]()
            
            # 리포트 생성
            report_generator = report_info["report_generator"]
            report_generator.generate_report(data)
            
            # 출력 파일 경로 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{report_id}_{timestamp}"
            
            if report_info["output_format"] == BaseReportGenerator.FORMAT_JSON:
                output_filename += ".json"
            elif report_info["output_format"] == BaseReportGenerator.FORMAT_CSV:
                output_filename += ".csv"
            else:
                output_filename += ".txt"
            
            output_path = os.path.join(report_info["output_dir"], output_filename)
            
            # 리포트 출력
            report_generator.output_report(
                output_format=report_info["output_format"],
                output_file=output_path
            )
            
            # 실행 정보 업데이트
            report_info["last_run"] = datetime.now().isoformat()
            report_info["next_run"] = self._calculate_next_run(
                report_info["schedule_type"],
                report_info["schedule_params"]
            )
            
            # 설정 저장소에 저장
            self._save_schedule_config()
            
            logger.info(f"리포트가 생성되었습니다: {report_id}, 파일: {output_path}")
        
        except Exception as e:
            logger.error(f"리포트 생성 중 오류 발생: {report_id}, {str(e)}")
    
    def _validate_schedule(self, schedule_type: str, schedule_params: Dict[str, Any]) -> bool:
        """
        스케줄 설정을 검증합니다.
        
        Args:
            schedule_type: 스케줄 유형
            schedule_params: 스케줄 매개변수
            
        Returns:
            bool: 유효성 여부
        """
        if schedule_type == self.SCHEDULE_DAILY:
            # 시간 형식 검증
            time_str = schedule_params.get("time", "00:00")
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    return False
            except ValueError:
                return False
        
        elif schedule_type == self.SCHEDULE_WEEKLY:
            # 요일 검증
            valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            day = schedule_params.get("day", "monday")
            if day not in valid_days:
                return False
            
            # 시간 형식 검증
            time_str = schedule_params.get("time", "00:00")
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    return False
            except ValueError:
                return False
        
        elif schedule_type == self.SCHEDULE_MONTHLY:
            # 날짜 검증
            day = schedule_params.get("day", 1)
            if not (1 <= day <= 31):
                return False
            
            # 시간 형식 검증
            time_str = schedule_params.get("time", "00:00")
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    return False
            except ValueError:
                return False
        
        else:
            # 지원하지 않는 스케줄 유형
            return False
        
        return True
    
    def _calculate_next_run(self, schedule_type: str, schedule_params: Dict[str, Any]) -> str:
        """
        다음 실행 시간을 계산합니다.
        
        Args:
            schedule_type: 스케줄 유형
            schedule_params: 스케줄 매개변수
            
        Returns:
            str: 다음 실행 시간 (ISO 형식)
        """
        now = datetime.now()
        next_run = None
        
        if schedule_type == self.SCHEDULE_DAILY:
            # 시간 파싱
            time_str = schedule_params.get("time", "00:00")
            hour, minute = map(int, time_str.split(":"))
            
            # 오늘 실행 시간
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 이미 지난 경우 내일로 설정
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif schedule_type == self.SCHEDULE_WEEKLY:
            # 요일 및 시간 파싱
            day_str = schedule_params.get("day", "monday")
            time_str = schedule_params.get("time", "00:00")
            hour, minute = map(int, time_str.split(":"))
            
            # 요일 매핑
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            target_weekday = day_map[day_str]
            
            # 이번 주 실행 시간
            days_ahead = target_weekday - now.weekday()
            if days_ahead < 0 or (days_ahead == 0 and now.hour > hour or (now.hour == hour and now.minute >= minute)):
                days_ahead += 7
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        
        elif schedule_type == self.SCHEDULE_MONTHLY:
            # 날짜 및 시간 파싱
            day = schedule_params.get("day", 1)
            time_str = schedule_params.get("time", "00:00")
            hour, minute = map(int, time_str.split(":"))
            
            # 이번 달 실행 시간
            try:
                next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            except ValueError:
                # 해당 월에 없는 날짜인 경우 (예: 2월 30일)
                # 다음 달 1일로 설정 후 계산
                if now.month == 12:
                    next_month = now.replace(year=now.year + 1, month=1, day=1)
                else:
                    next_month = now.replace(month=now.month + 1, day=1)
                
                try:
                    next_run = next_month.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                except ValueError:
                    # 다음 달에도 없는 날짜인 경우 재귀적으로 계산
                    next_schedule_params = schedule_params.copy()
                    return self._calculate_next_run(schedule_type, next_schedule_params)
            
            # 이미 지난 경우 다음 달로 설정
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    try:
                        next_run = next_run.replace(month=now.month + 1)
                    except ValueError:
                        # 다음 달에 해당 날짜가 없는 경우 (예: 1월 31일 -> 2월 28일)
                        if now.month == 12:
                            next_month = now.replace(year=now.year + 1, month=1, day=1)
                        else:
                            next_month = now.replace(month=now.month + 1, day=1)
                        
                        # 다음 달의 마지막 날
                        if next_month.month == 12:
                            last_day = (next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1)).day
                        else:
                            last_day = (next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1)).day
                        
                        # 실제 날짜와 요청 날짜 중 작은 값 사용
                        actual_day = min(day, last_day)
                        next_run = next_month.replace(day=actual_day, hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_run.isoformat() if next_run else now.isoformat()
    
    def _save_schedule_config(self) -> None:
        """
        스케줄 설정을 저장소에 저장합니다.
        """
        config_data = {}
        
        for report_id, report_info in self.scheduled_reports.items():
            # 객체 참조를 제외한 정보만 저장
            config_data[report_id] = {
                "schedule_type": report_info["schedule_type"],
                "schedule_params": report_info["schedule_params"],
                "output_format": report_info["output_format"],
                "output_dir": report_info["output_dir"],
                "last_run": report_info.get("last_run"),
                "next_run": report_info.get("next_run")
            }
        
        try:
            self.config_repository.set_config("report_schedules", json.dumps(config_data))
            logger.debug("리포트 스케줄 설정이 저장되었습니다.")
        except Exception as e:
            logger.error(f"리포트 스케줄 설정 저장 중 오류 발생: {str(e)}")
    
    def _load_schedule_config(self) -> None:
        """
        저장소에서 스케줄 설정을 로드합니다.
        """
        try:
            config_json = self.config_repository.get_config("report_schedules")
            
            if config_json:
                config_data = json.loads(config_json)
                
                # 기존 스케줄 정보 업데이트
                for report_id, report_config in config_data.items():
                    if report_id in self.scheduled_reports:
                        # 기존 리포트 정보 업데이트
                        report_info = self.scheduled_reports[report_id]
                        report_info["schedule_type"] = report_config["schedule_type"]
                        report_info["schedule_params"] = report_config["schedule_params"]
                        report_info["output_format"] = report_config["output_format"]
                        report_info["output_dir"] = report_config["output_dir"]
                        report_info["last_run"] = report_config.get("last_run")
                        report_info["next_run"] = report_config.get("next_run")
                
                logger.debug("리포트 스케줄 설정이 로드되었습니다.")
        
        except Exception as e:
            logger.error(f"리포트 스케줄 설정 로드 중 오류 발생: {str(e)}")