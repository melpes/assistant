"""
ConfidenceEvaluator 클래스의 단위 테스트
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.gmail.confidence_evaluator import ConfidenceEvaluator
from src.gmail.models import ExtractedEventInfo, EmailMetadata


class TestConfidenceEvaluator:
    """ConfidenceEvaluator 클래스 테스트"""
    
    @pytest.fixture
    def evaluator(self):
        """ConfidenceEvaluator 인스턴스 생성"""
        return ConfidenceEvaluator()
    
    @pytest.fixture
    def sample_event_info(self):
        """테스트용 일정 정보"""
        return ExtractedEventInfo(
            summary="팀 회의",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=2),
            location="3층 회의실 A",
            participants=["김철수", "이영희", "박민수"],
            all_day=False
        )
    
    @pytest.fixture
    def sample_email_metadata(self):
        """테스트용 이메일 메타데이터"""
        return EmailMetadata(
            id="test_email_123",
            subject="팀 회의 일정 안내",
            sender="manager@company.com",
            recipients=["user1@company.com", "user2@company.com"],
            date=datetime.now()
        )
    
    def test_evaluate_confidence_complete_info(self, evaluator, sample_event_info, sample_email_metadata):
        """완전한 정보에 대한 신뢰도 평가 테스트"""
        email_content = """
        안녕하세요,
        
        내일 오후 2시에 팀 회의가 있습니다.
        장소: 3층 회의실 A
        참석자: 김철수, 이영희, 박민수
        
        감사합니다.
        """
        
        result = evaluator.evaluate_confidence(sample_event_info, email_content, sample_email_metadata)
        
        assert isinstance(result, ExtractedEventInfo)
        assert result.overall_confidence > 0.5
        assert 'summary' in result.confidence_scores
        assert 'datetime' in result.confidence_scores
        assert 'location' in result.confidence_scores
        assert 'participants' in result.confidence_scores
    
    def test_evaluate_summary_confidence_high(self, evaluator, sample_email_metadata):
        """제목 신뢰도 평가 - 높은 신뢰도"""
        summary = "팀 회의"
        email_content = "팀 회의 일정 안내"
        
        score = evaluator._evaluate_summary_confidence(summary, email_content, sample_email_metadata)
        
        assert 0.5 <= score <= 1.0
    
    def test_evaluate_summary_confidence_low(self, evaluator, sample_email_metadata):
        """제목 신뢰도 평가 - 낮은 신뢰도"""
        summary = "a"  # 너무 짧은 제목
        email_content = "일반적인 내용"
        
        score = evaluator._evaluate_summary_confidence(summary, email_content, sample_email_metadata)
        
        assert score < 0.5
    
    def test_evaluate_datetime_confidence_high(self, evaluator):
        """날짜/시간 신뢰도 평가 - 높은 신뢰도"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        email_content = "2024년 1월 15일 오후 2시 30분에 회의가 있습니다"
        
        score = evaluator._evaluate_datetime_confidence(start_time, end_time, False, email_content)
        
        assert score > 0.7
    
    def test_evaluate_datetime_confidence_no_time(self, evaluator):
        """날짜/시간 신뢰도 평가 - 시간 없음"""
        score = evaluator._evaluate_datetime_confidence(None, None, False, "일반적인 내용")
        
        assert score == 0.0
    
    def test_evaluate_location_confidence_high(self, evaluator):
        """위치 신뢰도 평가 - 높은 신뢰도"""
        location = "3층 회의실 A"
        email_content = "3층 회의실 A에서 만나요"
        
        score = evaluator._evaluate_location_confidence(location, email_content)
        
        assert score > 0.6
    
    def test_evaluate_location_confidence_no_location(self, evaluator):
        """위치 신뢰도 평가 - 위치 없음"""
        score = evaluator._evaluate_location_confidence(None, "일반적인 내용")
        
        assert score == 0.0
    
    def test_evaluate_participants_confidence_with_metadata(self, evaluator, sample_email_metadata):
        """참석자 신뢰도 평가 - 메타데이터 포함"""
        participants = ["manager", "user1", "user2"]
        email_content = "참석자: manager, user1, user2"
        
        score = evaluator._evaluate_participants_confidence(participants, email_content, sample_email_metadata)
        
        assert score > 0.3
    
    def test_evaluate_participants_confidence_no_participants(self, evaluator, sample_email_metadata):
        """참석자 신뢰도 평가 - 참석자 없음"""
        score = evaluator._evaluate_participants_confidence([], "일반적인 내용", sample_email_metadata)
        
        assert score == 0.0
    
    def test_should_request_confirmation_high_confidence(self, evaluator):
        """높은 신뢰도 - 확인 불필요"""
        event_info = ExtractedEventInfo(
            summary="팀 회의",
            start_time=datetime.now() + timedelta(days=1),
            overall_confidence=0.9,
            confidence_scores={
                'summary': 0.9,
                'datetime': 0.9,
                'location': 0.8,
                'participants': 0.7
            }
        )
        
        needs_confirmation, low_fields = evaluator.should_request_confirmation(event_info)
        
        assert not needs_confirmation
        assert len(low_fields) == 0
    
    def test_should_request_confirmation_low_confidence(self, evaluator):
        """낮은 신뢰도 - 확인 필요"""
        event_info = ExtractedEventInfo(
            summary="회의",
            start_time=datetime.now() + timedelta(days=1),
            overall_confidence=0.5,
            confidence_scores={
                'summary': 0.5,
                'datetime': 0.6,
                'location': 0.3,
                'participants': 0.2
            }
        )
        
        needs_confirmation, low_fields = evaluator.should_request_confirmation(event_info)
        
        assert needs_confirmation
        assert len(low_fields) > 0
        assert 'location' in low_fields
        assert 'participants' in low_fields
    
    def test_should_request_confirmation_missing_essential(self, evaluator):
        """필수 정보 누락 - 확인 필요"""
        event_info = ExtractedEventInfo(
            summary="",  # 제목 누락
            start_time=None,  # 시간 누락
            overall_confidence=0.8
        )
        
        needs_confirmation, low_fields = evaluator.should_request_confirmation(event_info)
        
        assert needs_confirmation
        assert 'summary' in low_fields
        assert 'datetime' in low_fields
    
    def test_get_confirmation_message(self, evaluator, sample_event_info):
        """확인 요청 메시지 생성 테스트"""
        low_confidence_fields = ['location', 'participants']
        
        message = evaluator.get_confirmation_message(sample_event_info, low_confidence_fields)
        
        assert isinstance(message, str)
        assert "확인해주세요" in message
        assert sample_event_info.summary in message
        assert "장소" in message or "참석자" in message
        assert "신뢰도" in message
    
    def test_calculate_weighted_confidence(self, evaluator):
        """가중 평균 신뢰도 계산 테스트"""
        confidence_scores = {
            'summary': 0.9,
            'datetime': 0.8,
            'location': 0.7,
            'participants': 0.6
        }
        
        result = evaluator._calculate_weighted_confidence(confidence_scores)
        
        assert 0 <= result <= 1
        # 제목과 날짜/시간의 가중치가 높으므로 0.8 이상 예상
        assert result > 0.75
    
    def test_adjust_confidence_by_context_meeting_subject(self, evaluator, sample_event_info):
        """컨텍스트 기반 신뢰도 조정 - 회의 제목"""
        email_metadata = EmailMetadata(subject="팀 회의 일정 안내")
        email_content = "내일 회의가 있습니다."
        
        adjusted = evaluator._adjust_confidence_by_context(
            0.7, sample_event_info, email_content, email_metadata
        )
        
        assert adjusted >= 0.7  # 회의 키워드로 인한 증가 (최소 유지)
    
    def test_adjust_confidence_by_context_short_content(self, evaluator, sample_event_info):
        """컨텍스트 기반 신뢰도 조정 - 짧은 내용"""
        email_content = "회의"  # 매우 짧은 내용
        
        adjusted = evaluator._adjust_confidence_by_context(
            0.7, sample_event_info, email_content, None
        )
        
        assert adjusted < 0.7  # 짧은 내용으로 인한 감소
    
    def test_adjust_confidence_by_context_missing_essential(self, evaluator):
        """컨텍스트 기반 신뢰도 조정 - 필수 정보 누락"""
        event_info = ExtractedEventInfo(summary="", start_time=None)
        email_content = "일반적인 내용"
        
        adjusted = evaluator._adjust_confidence_by_context(
            0.8, event_info, email_content, None
        )
        
        assert adjusted < 0.8  # 필수 정보 누락으로 인한 감소
        assert adjusted <= 0.4  # 두 개 필수 정보 누락으로 0.4 감소
    
    def test_adjust_confidence_by_context_invalid_time_range(self, evaluator):
        """컨텍스트 기반 신뢰도 조정 - 잘못된 시간 범위"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time - timedelta(hours=1)  # 종료가 시작보다 이름
        
        event_info = ExtractedEventInfo(
            summary="회의",
            start_time=start_time,
            end_time=end_time
        )
        
        adjusted = evaluator._adjust_confidence_by_context(
            0.8, event_info, "회의 내용", None
        )
        
        assert adjusted < 0.8  # 잘못된 시간 범위로 인한 감소
    
    def test_custom_thresholds(self):
        """사용자 정의 임계값 테스트"""
        custom_thresholds = {
            'summary': 0.8,
            'datetime': 0.9,
            'location': 0.6,
            'participants': 0.5
        }
        
        evaluator = ConfidenceEvaluator(
            default_threshold=0.8,
            field_thresholds=custom_thresholds
        )
        
        assert evaluator.default_threshold == 0.8
        assert evaluator.field_thresholds['summary'] == 0.8
        assert evaluator.field_thresholds['datetime'] == 0.9
    
    def test_error_handling(self, evaluator, sample_event_info):
        """오류 처리 테스트"""
        # 잘못된 입력으로 오류 발생 시뮬레이션
        with patch.object(evaluator, '_evaluate_summary_confidence', side_effect=Exception("Test error")):
            result = evaluator.evaluate_confidence(sample_event_info, "test content")
            
            assert result.overall_confidence == 0.0
    
    def test_korean_patterns_recognition(self, evaluator):
        """한국어 패턴 인식 테스트"""
        # 한국어 이름 패턴
        participants = ["김철수", "이영희", "박민수"]
        score = evaluator._evaluate_participants_confidence(participants, "참석자 목록", None)
        
        assert score > 0.3  # 한국어 이름 패턴 인식으로 점수 증가
        
        # 한국어 위치 패턴
        location = "서울시 강남구 테헤란로 123"
        score = evaluator._evaluate_location_confidence(location, "주소 정보")
        
        assert score > 0.4  # 한국어 주소 패턴 인식으로 점수 증가