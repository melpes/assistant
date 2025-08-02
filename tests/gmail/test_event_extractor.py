"""
EventExtractor 클래스의 단위 테스트
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.gmail.event_extractor import EventExtractor
from src.gmail.models import ExtractedEventInfo, EmailMetadata


class TestEventExtractor:
    """EventExtractor 클래스 테스트"""
    
    @pytest.fixture
    def extractor(self):
        """EventExtractor 인스턴스 생성"""
        with patch('src.gmail.event_extractor.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            return EventExtractor()
    
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
    
    def test_extract_event_info_basic(self, extractor, sample_email_metadata):
        """기본 일정 정보 추출 테스트"""
        email_content = """
        안녕하세요,
        
        다음주 월요일 오후 2시에 팀 회의가 있습니다.
        장소: 3층 회의실 A
        참석자: 김철수, 이영희, 박민수
        
        감사합니다.
        """
        
        # Gemini 응답 모킹
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "summary": "팀 회의",
            "start_time": "2024-01-15T14:00:00",
            "end_time": "2024-01-15T16:00:00",
            "location": "3층 회의실 A",
            "description": "팀 회의 일정",
            "participants": ["김철수", "이영희", "박민수"],
            "all_day": false,
            "confidence": {
                "summary": 0.9,
                "datetime": 0.8,
                "location": 0.8,
                "participants": 0.7
            }
        }
        ```'''
        
        extractor.model.generate_content.return_value = mock_response
        
        result = extractor.extract_event_info(email_content, sample_email_metadata)
        
        assert isinstance(result, ExtractedEventInfo)
        assert result.summary == "팀 회의"
        assert result.location == "3층 회의실 A"
        assert len(result.participants) > 0
        assert result.overall_confidence > 0
    
    def test_extract_datetime_with_patterns(self, extractor):
        """패턴 매칭을 통한 날짜/시간 추출 테스트"""
        test_cases = [
            ("2024년 1월 15일 14시", True),
            ("다음주 월요일 오후 2시", True),
            ("내일 오전 10시 30분", True),
            ("12월 25일", True),
            ("일반적인 텍스트", False),
        ]
        
        for content, should_extract in test_cases:
            start_time, end_time, all_day = extractor._extract_datetime_with_patterns(content)
            
            if should_extract:
                assert start_time is not None or content in ["일반적인 텍스트"]
            else:
                assert start_time is None
    
    def test_extract_location(self, extractor):
        """위치 정보 추출 테스트"""
        test_cases = [
            ("장소: 3층 회의실 A", "3층 회의실 A"),
            ("위치: 서울시 강남구", "서울시 강남구"),
            ("회의실: B동 201호", "B동 201호"),
            ("일반적인 텍스트", None),
        ]
        
        for content, expected in test_cases:
            structured_info = {}
            result = extractor._extract_location(content, structured_info)
            
            if expected:
                assert result is not None
                assert expected in result
            else:
                assert result is None
    
    def test_extract_participants(self, extractor, sample_email_metadata):
        """참석자 정보 추출 테스트"""
        email_content = "참석자: 김철수, 이영희, 박민수"
        structured_info = {"participants": ["김철수", "이영희"]}
        
        result = extractor._extract_participants(email_content, sample_email_metadata, structured_info)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "김철수" in result or "manager" in result  # 구조화된 정보 또는 메타데이터에서
    
    def test_extract_summary(self, extractor, sample_email_metadata):
        """제목 추출 테스트"""
        email_content = "팀 회의 일정에 대해 안내드립니다."
        structured_info = {"summary": "팀 회의"}
        
        result = extractor._extract_summary(email_content, sample_email_metadata, structured_info)
        
        assert result == "팀 회의"  # 구조화된 정보 우선
    
    def test_calculate_individual_confidence_scores(self, extractor):
        """개별 신뢰도 점수 계산 테스트"""
        event_info = ExtractedEventInfo(
            summary="팀 회의",
            start_time=datetime.now() + timedelta(days=1),
            location="3층 회의실",
            participants=["김철수", "이영희"]
        )
        
        email_content = "팀 회의 일정 안내"
        
        scores = extractor._calculate_individual_confidence_scores(event_info, email_content)
        
        assert isinstance(scores, dict)
        assert 'summary' in scores
        assert 'datetime' in scores
        assert 'location' in scores
        assert 'participants' in scores
        assert all(0 <= score <= 1 for score in scores.values())
    
    def test_calculate_overall_confidence(self, extractor):
        """전체 신뢰도 점수 계산 테스트"""
        confidence_scores = {
            'summary': 0.9,
            'datetime': 0.8,
            'location': 0.7,
            'participants': 0.6
        }
        
        result = extractor._calculate_overall_confidence(confidence_scores)
        
        assert 0 <= result <= 1
        assert result > 0.7  # 가중 평균이므로 높은 점수 예상
    
    def test_parse_datetime(self, extractor):
        """날짜/시간 파싱 테스트"""
        test_cases = [
            "2024-01-15T14:00:00",
            "2024-01-15 14:00:00",
            "invalid_date"
        ]
        
        for datetime_str in test_cases:
            result = extractor._parse_datetime(datetime_str)
            
            if "invalid" in datetime_str:
                assert result is None
            else:
                assert isinstance(result, datetime)
    
    def test_build_extraction_prompt(self, extractor, sample_email_metadata):
        """프롬프트 구성 테스트"""
        email_content = "팀 회의 일정 안내"
        
        prompt = extractor._build_extraction_prompt(email_content, sample_email_metadata)
        
        assert isinstance(prompt, str)
        assert "팀 회의 일정 안내" in prompt
        assert "JSON" in prompt
        assert sample_email_metadata.subject in prompt
    
    @patch('src.gmail.event_extractor.genai')
    def test_extract_with_gemini_success(self, mock_genai, extractor):
        """Gemini를 사용한 정보 추출 성공 테스트"""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "summary": "팀 회의",
            "start_time": "2024-01-15T14:00:00",
            "location": "회의실 A"
        }
        ```'''
        
        extractor.model.generate_content.return_value = mock_response
        
        result = extractor._extract_with_gemini("test content")
        
        assert isinstance(result, dict)
        assert result.get('summary') == "팀 회의"
        assert result.get('location') == "회의실 A"
    
    @patch('src.gmail.event_extractor.genai')
    def test_extract_with_gemini_json_error(self, mock_genai, extractor):
        """Gemini JSON 파싱 오류 테스트"""
        mock_response = Mock()
        mock_response.text = "invalid json response"
        
        extractor.model.generate_content.return_value = mock_response
        
        result = extractor._extract_with_gemini("test content")
        
        assert result == {}
    
    def test_korean_date_patterns(self, extractor):
        """한국어 날짜 패턴 테스트"""
        test_texts = [
            "2024년 1월 15일에 회의가 있습니다",
            "1월 15일 오후 2시",
            "12/25 크리스마스",
            "2024-01-15 일정"
        ]
        
        for text in test_texts:
            # 패턴이 매칭되는지 확인
            found_pattern = False
            for pattern in extractor.korean_date_patterns:
                import re
                if re.search(pattern, text):
                    found_pattern = True
                    break
            
            assert found_pattern, f"패턴을 찾을 수 없음: {text}"
    
    def test_korean_time_patterns(self, extractor):
        """한국어 시간 패턴 테스트"""
        test_texts = [
            "오후 2시 30분",
            "오전 10시",
            "14시 30분",
            "15:30"
        ]
        
        for text in test_texts:
            # 패턴이 매칭되는지 확인
            found_pattern = False
            for pattern in extractor.korean_time_patterns:
                import re
                if re.search(pattern, text):
                    found_pattern = True
                    break
            
            assert found_pattern, f"시간 패턴을 찾을 수 없음: {text}"
    
    def test_empty_email_content(self, extractor):
        """빈 이메일 내용 처리 테스트"""
        result = extractor.extract_event_info("")
        
        assert isinstance(result, ExtractedEventInfo)
        assert result.overall_confidence == 0.0
        assert not result.summary
        assert result.start_time is None
    
    def test_error_handling(self, extractor):
        """오류 처리 테스트"""
        # Gemini API 오류 시뮬레이션
        extractor.model.generate_content.side_effect = Exception("API Error")
        
        result = extractor.extract_event_info("test content")
        
        assert isinstance(result, ExtractedEventInfo)
        assert result.overall_confidence == 0.0