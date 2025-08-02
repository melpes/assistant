# -*- coding: utf-8 -*-
"""
리포트 스케줄러 테스트

리포트 스케줄링 기능을 테스트합니다.
"""

import os
import json
import unittest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch

from src.reports.base_report_generator import BaseReportGenerator
from src.reports.report_scheduler import ReportScheduler


class TestReportScheduler(unittest.TestCase):
    """ReportScheduler 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 설정 저장소 모의 객체
        self.mock_config_repository = MagicMock()
        self.mock_config_repository.get_config.return_value = None
        
        # 리포트 스케줄러
        self.scheduler = ReportScheduler(self.mock_config_repository)
        
        # 테스트용 리포트 생성기
        self.mock_report_generator = MagicMock()
        self.mock_report_generator.generate_report.return_value = {"test": "data"}
        self.mock_report_generator.output_report.return_value = "test output"
        
        # 테스트용 데이터 제공 함수
        self.mock_data_provider = MagicMock()
        self.mock_data_provider.return_value = {"test": "data"}
    
    def test_add_scheduled_report_daily(self):
        """일간 스케줄 추가 테스트"""
        # 일간 스케줄 추가
        result = self.scheduler.add_scheduled_report(
            report_id="test_daily",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 결과 검증
        self.assertTrue(result)
        self.assertIn("test_daily", self.scheduler.scheduled_reports)
        self.assertEqual(
            self.scheduler.scheduled_reports["test_daily"]["schedule_type"],
            ReportScheduler.SCHEDULE_DAILY
        )
        self.assertEqual(
            self.scheduler.scheduled_reports["test_daily"]["schedule_params"]["time"],
            "12:00"
        )
    
    def test_add_scheduled_report_weekly(self):
        """주간 스케줄 추가 테스트"""
        # 주간 스케줄 추가
        result = self.scheduler.add_scheduled_report(
            report_id="test_weekly",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_WEEKLY,
            schedule_params={"day": "monday", "time": "09:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 결과 검증
        self.assertTrue(result)
        self.assertIn("test_weekly", self.scheduler.scheduled_reports)
        self.assertEqual(
            self.scheduler.scheduled_reports["test_weekly"]["schedule_type"],
            ReportScheduler.SCHEDULE_WEEKLY
        )
        self.assertEqual(
            self.scheduler.scheduled_reports["test_weekly"]["schedule_params"]["day"],
            "monday"
        )
    
    def test_add_scheduled_report_monthly(self):
        """월간 스케줄 추가 테스트"""
        # 월간 스케줄 추가
        result = self.scheduler.add_scheduled_report(
            report_id="test_monthly",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_MONTHLY,
            schedule_params={"day": 1, "time": "00:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 결과 검증
        self.assertTrue(result)
        self.assertIn("test_monthly", self.scheduler.scheduled_reports)
        self.assertEqual(
            self.scheduler.scheduled_reports["test_monthly"]["schedule_type"],
            ReportScheduler.SCHEDULE_MONTHLY
        )
        self.assertEqual(
            self.scheduler.scheduled_reports["test_monthly"]["schedule_params"]["day"],
            1
        )
    
    def test_validate_schedule(self):
        """스케줄 검증 테스트"""
        # 유효한 일간 스케줄
        self.assertTrue(self.scheduler._validate_schedule(
            ReportScheduler.SCHEDULE_DAILY,
            {"time": "12:00"}
        ))
        
        # 유효한 주간 스케줄
        self.assertTrue(self.scheduler._validate_schedule(
            ReportScheduler.SCHEDULE_WEEKLY,
            {"day": "monday", "time": "09:00"}
        ))
        
        # 유효한 월간 스케줄
        self.assertTrue(self.scheduler._validate_schedule(
            ReportScheduler.SCHEDULE_MONTHLY,
            {"day": 15, "time": "00:00"}
        ))
        
        # 잘못된 시간 형식
        self.assertFalse(self.scheduler._validate_schedule(
            ReportScheduler.SCHEDULE_DAILY,
            {"time": "25:00"}
        ))
        
        # 잘못된 요일
        self.assertFalse(self.scheduler._validate_schedule(
            ReportScheduler.SCHEDULE_WEEKLY,
            {"day": "invalid_day", "time": "09:00"}
        ))
        
        # 잘못된 날짜
        self.assertFalse(self.scheduler._validate_schedule(
            ReportScheduler.SCHEDULE_MONTHLY,
            {"day": 32, "time": "00:00"}
        ))
        
        # 지원하지 않는 스케줄 유형
        self.assertFalse(self.scheduler._validate_schedule(
            "invalid_type",
            {"time": "12:00"}
        ))
    
    def test_calculate_next_run(self):
        """다음 실행 시간 계산 테스트"""
        # 일간 스케줄
        next_run = self.scheduler._calculate_next_run(
            ReportScheduler.SCHEDULE_DAILY,
            {"time": "12:00"}
        )
        self.assertIsNotNone(next_run)
        
        # 주간 스케줄
        next_run = self.scheduler._calculate_next_run(
            ReportScheduler.SCHEDULE_WEEKLY,
            {"day": "monday", "time": "09:00"}
        )
        self.assertIsNotNone(next_run)
        
        # 월간 스케줄
        next_run = self.scheduler._calculate_next_run(
            ReportScheduler.SCHEDULE_MONTHLY,
            {"day": 1, "time": "00:00"}
        )
        self.assertIsNotNone(next_run)
    
    def test_remove_scheduled_report(self):
        """스케줄 제거 테스트"""
        # 스케줄 추가
        self.scheduler.add_scheduled_report(
            report_id="test_report",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 스케줄 제거
        with patch('schedule.clear') as mock_clear:
            result = self.scheduler.remove_scheduled_report("test_report")
            
            # 결과 검증
            self.assertTrue(result)
            self.assertNotIn("test_report", self.scheduler.scheduled_reports)
            mock_clear.assert_called_once_with("test_report")
    
    def test_update_scheduled_report(self):
        """스케줄 업데이트 테스트"""
        # 스케줄 추가
        self.scheduler.add_scheduled_report(
            report_id="test_report",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 스케줄 업데이트
        with patch('schedule.clear') as mock_clear:
            result = self.scheduler.update_scheduled_report(
                report_id="test_report",
                schedule_type=ReportScheduler.SCHEDULE_WEEKLY,
                schedule_params={"day": "friday", "time": "15:00"},
                output_format=BaseReportGenerator.FORMAT_CSV
            )
            
            # 결과 검증
            self.assertTrue(result)
            self.assertEqual(
                self.scheduler.scheduled_reports["test_report"]["schedule_type"],
                ReportScheduler.SCHEDULE_WEEKLY
            )
            self.assertEqual(
                self.scheduler.scheduled_reports["test_report"]["schedule_params"]["day"],
                "friday"
            )
            self.assertEqual(
                self.scheduler.scheduled_reports["test_report"]["output_format"],
                BaseReportGenerator.FORMAT_CSV
            )
            mock_clear.assert_called_once_with("test_report")
    
    def test_get_scheduled_reports(self):
        """스케줄 목록 조회 테스트"""
        # 스케줄 추가
        self.scheduler.add_scheduled_report(
            report_id="test_report1",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        self.scheduler.add_scheduled_report(
            report_id="test_report2",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_WEEKLY,
            schedule_params={"day": "monday", "time": "09:00"},
            output_format=BaseReportGenerator.FORMAT_CSV,
            output_dir="reports"
        )
        
        # 스케줄 목록 조회
        reports = self.scheduler.get_scheduled_reports()
        
        # 결과 검증
        self.assertEqual(len(reports), 2)
        self.assertIn("test_report1", reports)
        self.assertIn("test_report2", reports)
        self.assertEqual(reports["test_report1"]["schedule_type"], ReportScheduler.SCHEDULE_DAILY)
        self.assertEqual(reports["test_report2"]["schedule_type"], ReportScheduler.SCHEDULE_WEEKLY)
    
    @patch('threading.Thread')
    def test_start_stop(self, mock_thread):
        """스케줄러 시작/중지 테스트"""
        # 스케줄러 시작
        self.scheduler.start()
        
        # 결과 검증
        self.assertTrue(self.scheduler.running)
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        
        # 스케줄러 중지
        with patch('schedule.clear') as mock_clear:
            self.scheduler.stop()
            
            # 결과 검증
            self.assertFalse(self.scheduler.running)
            mock_clear.assert_called_once()
    
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_generate_report(self, mock_join, mock_makedirs):
        """리포트 생성 테스트"""
        # 경로 모의
        mock_join.return_value = "reports/test_report.json"
        
        # 스케줄 추가
        self.scheduler.add_scheduled_report(
            report_id="test_report",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 리포트 생성
        self.scheduler._generate_report("test_report")
        
        # 결과 검증
        self.mock_data_provider.assert_called_once()
        self.mock_report_generator.generate_report.assert_called_once_with({"test": "data"})
        self.mock_report_generator.output_report.assert_called_once()
        mock_makedirs.assert_called_once()
    
    def test_run_report_now(self):
        """리포트 즉시 실행 테스트"""
        # 스케줄 추가
        self.scheduler.add_scheduled_report(
            report_id="test_report",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 리포트 즉시 실행
        with patch.object(self.scheduler, '_generate_report') as mock_generate:
            result = self.scheduler.run_report_now("test_report")
            
            # 결과 검증
            self.assertTrue(result)
            mock_generate.assert_called_once_with("test_report")
    
    def test_save_load_config(self):
        """설정 저장/로드 테스트"""
        # 스케줄 추가
        self.scheduler.add_scheduled_report(
            report_id="test_report",
            report_generator=self.mock_report_generator,
            report_data_provider=self.mock_data_provider,
            schedule_type=ReportScheduler.SCHEDULE_DAILY,
            schedule_params={"time": "12:00"},
            output_format=BaseReportGenerator.FORMAT_JSON,
            output_dir="reports"
        )
        
        # 설정 저장
        self.scheduler._save_schedule_config()
        
        # 설정 저장소 호출 검증
        self.mock_config_repository.set_config.assert_called_once()
        args = self.mock_config_repository.set_config.call_args[0]
        self.assertEqual(args[0], "report_schedules")
        
        # 저장된 JSON 파싱
        saved_config = json.loads(args[1])
        self.assertIn("test_report", saved_config)
        self.assertEqual(saved_config["test_report"]["schedule_type"], ReportScheduler.SCHEDULE_DAILY)
        
        # 설정 로드 모의
        self.mock_config_repository.get_config.return_value = args[1]
        
        # 새 스케줄러 생성 및 설정 로드
        new_scheduler = ReportScheduler(self.mock_config_repository)
        new_scheduler.scheduled_reports = {
            "test_report": {
                "report_generator": self.mock_report_generator,
                "report_data_provider": self.mock_data_provider,
                "schedule_type": "old_type",
                "schedule_params": {},
                "output_format": "old_format",
                "output_dir": "old_dir"
            }
        }
        
        # 설정 로드
        new_scheduler._load_schedule_config()
        
        # 결과 검증
        self.assertEqual(
            new_scheduler.scheduled_reports["test_report"]["schedule_type"],
            ReportScheduler.SCHEDULE_DAILY
        )
        self.assertEqual(
            new_scheduler.scheduled_reports["test_report"]["schedule_params"]["time"],
            "12:00"
        )
        self.assertEqual(
            new_scheduler.scheduled_reports["test_report"]["output_format"],
            BaseReportGenerator.FORMAT_JSON
        )


if __name__ == '__main__':
    unittest.main()