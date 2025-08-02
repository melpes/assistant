"""
이메일에서 일정 관련 정보를 추출하는 EventExtractor 클래스
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

import google.generativeai as genai
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

from .models import ExtractedEventInfo, EmailMetadata
from ..config import GOOGLE_API_KEY


class EventExtractor:
    """이메일에서 일정 관련 정보를 추출하는 클래스"""
    
    def __init__(self, model_name: str = "gemini-1.5-pro-latest"):
        """
        Args:
            model_name: 사용할 Gemini 모델명
        """
        self.logger = logging.getLogger(__name__)
        
        # Gemini API 설정
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model_name)
        
        # 한국어 날짜/시간 패턴
        self.korean_date_patterns = [
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})-(\d{1,2})',
        ]
        
        self.korean_time_patterns = [
            r'(\d{1,2})시\s*(\d{1,2})분',
            r'(\d{1,2})시',
            r'오전\s*(\d{1,2})시\s*(\d{1,2})분',
            r'오후\s*(\d{1,2})시\s*(\d{1,2})분',
            r'오전\s*(\d{1,2})시',
            r'오후\s*(\d{1,2})시',
            r'(\d{1,2}):(\d{2})',
        ]
        
        # 위치 관련 키워드
        self.location_keywords = [
            '장소', '위치', '주소', '에서', '에서의', '회의실', '카페', '식당',
            '사무실', '빌딩', '층', '호', '구', '동', '로', '길', '역',
            '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종'
        ]
        
        # 참석자 관련 키워드
        self.participant_keywords = [
            '참석자', '참가자', '참여자', '초대', '함께', '와', '과', '님',
            '씨', '대표', '팀장', '부장', '과장', '차장', '사장', '이사'
        ]
    
    def extract_event_info(self, email_content: str, email_metadata: EmailMetadata = None) -> ExtractedEventInfo:
        """
        이메일 내용에서 일정 정보 추출
        
        Args:
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            추출된 일정 정보
        """
        try:
            self.logger.info("이메일에서 일정 정보 추출 시작")
            
            # Gemini를 사용한 구조화된 정보 추출
            structured_info = self._extract_with_gemini(email_content, email_metadata)
            
            # 개별 정보 추출 및 검증
            event_info = ExtractedEventInfo()
            
            # 제목 추출
            event_info.summary = self._extract_summary(email_content, email_metadata, structured_info)
            
            # 날짜/시간 추출
            start_time, end_time, all_day = self._extract_datetime(email_content, structured_info)
            event_info.start_time = start_time
            event_info.end_time = end_time
            event_info.all_day = all_day
            
            # 위치 정보 추출
            event_info.location = self._extract_location(email_content, structured_info)
            
            # 참석자 정보 추출
            event_info.participants = self._extract_participants(email_content, email_metadata, structured_info)
            
            # 설명 추출
            event_info.description = self._extract_description(email_content, structured_info)
            
            # 신뢰도 점수 계산
            event_info.confidence_scores = self._calculate_individual_confidence_scores(event_info, email_content)
            event_info.overall_confidence = self._calculate_overall_confidence(event_info.confidence_scores)
            
            self.logger.info(f"일정 정보 추출 완료 - 전체 신뢰도: {event_info.overall_confidence:.2f}")
            return event_info
            
        except Exception as e:
            self.logger.error(f"일정 정보 추출 중 오류 발생: {str(e)}")
            return ExtractedEventInfo()
    
    def _extract_with_gemini(self, email_content: str, email_metadata: EmailMetadata = None) -> Dict[str, Any]:
        """
        Gemini를 사용하여 구조화된 일정 정보 추출
        
        Args:
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            구조화된 일정 정보
        """
        try:
            # 프롬프트 구성
            prompt = self._build_extraction_prompt(email_content, email_metadata)
            
            # Gemini API 호출
            response = self.model.generate_content(prompt)
            
            # JSON 응답 파싱
            response_text = response.text.strip()
            
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = response_text
            
            try:
                structured_info = json.loads(json_text)
                return structured_info
            except json.JSONDecodeError:
                self.logger.warning("Gemini 응답을 JSON으로 파싱할 수 없음")
                return {}
                
        except Exception as e:
            self.logger.error(f"Gemini를 사용한 정보 추출 중 오류: {str(e)}")
            return {}
    
    def _build_extraction_prompt(self, email_content: str, email_metadata: EmailMetadata = None) -> str:
        """
        일정 정보 추출을 위한 프롬프트 구성
        
        Args:
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            구성된 프롬프트
        """
        metadata_info = ""
        if email_metadata:
            metadata_info = f"""
이메일 메타데이터:
- 제목: {email_metadata.subject}
- 발신자: {email_metadata.sender}
- 수신자: {', '.join(email_metadata.recipients)}
- 날짜: {email_metadata.date}
"""
        
        prompt = f"""
다음 이메일에서 일정/이벤트 관련 정보를 추출해주세요. 한국어 텍스트를 정확히 분석하여 구조화된 JSON 형태로 응답해주세요.

{metadata_info}

이메일 내용:
{email_content}

다음 JSON 형식으로 응답해주세요:

```json
{{
    "summary": "일정 제목 (회의명, 이벤트명 등)",
    "start_time": "시작 날짜/시간 (ISO 8601 형식, 예: 2024-01-15T14:00:00)",
    "end_time": "종료 날짜/시간 (ISO 8601 형식, 예: 2024-01-15T16:00:00)",
    "location": "장소/위치 정보",
    "description": "일정 설명/내용",
    "participants": ["참석자1", "참석자2"],
    "all_day": false,
    "confidence": {{
        "summary": 0.9,
        "datetime": 0.8,
        "location": 0.7,
        "participants": 0.6
    }}
}}
```

주의사항:
1. 한국어 날짜/시간 표현을 정확히 인식하세요 (예: "내일 오후 2시", "다음주 월요일", "12월 15일 14시")
2. 상대적 날짜 표현을 절대 날짜로 변환하세요
3. 정보가 명확하지 않으면 confidence 점수를 낮게 설정하세요
4. 일정과 관련없는 내용이면 모든 필드를 null 또는 빈 값으로 설정하세요
5. 시간대는 한국 시간(KST)으로 가정하세요
"""
        
        return prompt
    
    def _extract_summary(self, email_content: str, email_metadata: EmailMetadata, structured_info: Dict) -> str:
        """
        일정 제목 추출
        
        Args:
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            structured_info: Gemini에서 추출한 구조화된 정보
            
        Returns:
            추출된 제목
        """
        # Gemini 결과 우선 사용
        if structured_info.get('summary'):
            return structured_info['summary']
        
        # 이메일 제목에서 추출
        if email_metadata and email_metadata.subject:
            # 일정 관련 키워드가 포함된 경우 제목 사용
            meeting_keywords = ['회의', '미팅', '만남', '약속', '모임', '세미나', '워크샵', '컨퍼런스']
            if any(keyword in email_metadata.subject for keyword in meeting_keywords):
                return email_metadata.subject
        
        # 이메일 내용에서 제목 추출
        title_patterns = [
            r'제목[:\s]*(.+)',
            r'회의[:\s]*(.+)',
            r'미팅[:\s]*(.+)',
            r'일정[:\s]*(.+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, email_content)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_datetime(self, email_content: str, structured_info: Dict) -> Tuple[Optional[datetime], Optional[datetime], bool]:
        """
        날짜/시간 정보 추출
        
        Args:
            email_content: 이메일 내용
            structured_info: Gemini에서 추출한 구조화된 정보
            
        Returns:
            (시작시간, 종료시간, 종일여부)
        """
        try:
            # Gemini 결과 우선 사용
            if structured_info.get('start_time'):
                start_time = self._parse_datetime(structured_info['start_time'])
                end_time = None
                if structured_info.get('end_time'):
                    end_time = self._parse_datetime(structured_info['end_time'])
                all_day = structured_info.get('all_day', False)
                return start_time, end_time, all_day
            
            # 패턴 매칭으로 날짜/시간 추출
            return self._extract_datetime_with_patterns(email_content)
            
        except Exception as e:
            self.logger.error(f"날짜/시간 추출 중 오류: {str(e)}")
            return None, None, False
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        문자열을 datetime 객체로 변환
        
        Args:
            datetime_str: 날짜/시간 문자열
            
        Returns:
            변환된 datetime 객체
        """
        try:
            return date_parser.parse(datetime_str)
        except Exception:
            return None
    
    def _extract_datetime_with_patterns(self, email_content: str) -> Tuple[Optional[datetime], Optional[datetime], bool]:
        """
        패턴 매칭을 사용한 날짜/시간 추출
        
        Args:
            email_content: 이메일 내용
            
        Returns:
            (시작시간, 종료시간, 종일여부)
        """
        # 현재 시간 기준
        now = datetime.now()
        
        # 상대적 날짜 표현 처리
        relative_date = self._parse_relative_date(email_content, now)
        
        # 날짜 추출
        date_found = relative_date
        if not date_found:
            for pattern in self.korean_date_patterns:
                match = re.search(pattern, email_content)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups) == 3:  # 년월일
                            year, month, day = map(int, groups)
                            date_found = datetime(year, month, day)
                        elif len(groups) == 2:  # 월일
                            month, day = map(int, groups)
                            year = now.year
                            date_found = datetime(year, month, day)
                            # 과거 날짜면 내년으로 설정
                            if date_found < now:
                                date_found = date_found.replace(year=year + 1)
                        break
                    except ValueError:
                        continue
        
        # 시간 추출
        time_found = None
        for pattern in self.korean_time_patterns:
            match = re.search(pattern, email_content)
            if match:
                try:
                    groups = match.groups()
                    if '오후' in match.group(0) and len(groups) >= 1:
                        hour = int(groups[0])
                        if hour != 12:
                            hour += 12
                        minute = int(groups[1]) if len(groups) > 1 else 0
                        time_found = (hour, minute)
                    elif '오전' in match.group(0) and len(groups) >= 1:
                        hour = int(groups[0])
                        if hour == 12:
                            hour = 0
                        minute = int(groups[1]) if len(groups) > 1 else 0
                        time_found = (hour, minute)
                    elif len(groups) >= 1:
                        hour = int(groups[0])
                        minute = int(groups[1]) if len(groups) > 1 else 0
                        time_found = (hour, minute)
                    break
                except ValueError:
                    continue
        
        # 날짜와 시간 결합
        if date_found and time_found:
            start_time = date_found.replace(hour=time_found[0], minute=time_found[1])
            return start_time, None, False
        elif date_found:
            return date_found, None, True
        
        return None, None, False
    
    def _parse_relative_date(self, text: str, base_date: datetime) -> Optional[datetime]:
        """
        상대적 날짜 표현 파싱
        
        Args:
            text: 분석할 텍스트
            base_date: 기준 날짜
            
        Returns:
            파싱된 날짜
        """
        # 내일, 모레
        if '내일' in text:
            return base_date + timedelta(days=1)
        elif '모레' in text:
            return base_date + timedelta(days=2)
        
        # 다음주
        if '다음주' in text:
            days_ahead = 7 - base_date.weekday()  # 다음 월요일까지의 일수
            next_monday = base_date + timedelta(days=days_ahead)
            
            # 요일 지정이 있는지 확인
            weekdays = {
                '월요일': 0, '화요일': 1, '수요일': 2, '목요일': 3,
                '금요일': 4, '토요일': 5, '일요일': 6
            }
            
            for day_name, day_num in weekdays.items():
                if day_name in text:
                    return next_monday + timedelta(days=day_num)
            
            return next_monday  # 기본적으로 다음주 월요일
        
        # 다음달
        if '다음달' in text:
            if base_date.month == 12:
                return base_date.replace(year=base_date.year + 1, month=1, day=1)
            else:
                return base_date.replace(month=base_date.month + 1, day=1)
        
        return None
    
    def _extract_location(self, email_content: str, structured_info: Dict) -> Optional[str]:
        """
        위치 정보 추출
        
        Args:
            email_content: 이메일 내용
            structured_info: Gemini에서 추출한 구조화된 정보
            
        Returns:
            추출된 위치 정보
        """
        # Gemini 결과 우선 사용
        if structured_info.get('location'):
            return structured_info['location']
        
        # 패턴 매칭으로 위치 추출
        location_patterns = [
            r'장소[:\s]*(.+)',
            r'위치[:\s]*(.+)',
            r'주소[:\s]*(.+)',
            r'에서\s+(.+)',
            r'회의실[:\s]*(.+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, email_content)
            if match:
                location = match.group(1).strip()
                # 줄바꿈이나 특수문자 제거
                location = re.sub(r'[\n\r\t]', ' ', location)
                location = re.sub(r'\s+', ' ', location)
                return location[:100]  # 길이 제한
        
        return None
    
    def _extract_participants(self, email_content: str, email_metadata: EmailMetadata, structured_info: Dict) -> List[str]:
        """
        참석자 정보 추출
        
        Args:
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            structured_info: Gemini에서 추출한 구조화된 정보
            
        Returns:
            추출된 참석자 목록
        """
        participants = []
        
        # Gemini 결과 우선 사용
        if structured_info.get('participants'):
            participants.extend(structured_info['participants'])
        
        # 이메일 메타데이터에서 참석자 추출
        if email_metadata:
            if email_metadata.sender:
                participants.append(email_metadata.sender)
            participants.extend(email_metadata.recipients)
            participants.extend(email_metadata.cc)
        
        # 이메일 내용에서 참석자 추출
        participant_patterns = [
            r'참석자[:\s]*(.+)',
            r'참가자[:\s]*(.+)',
            r'참여자[:\s]*(.+)',
            r'초대[:\s]*(.+)',
        ]
        
        for pattern in participant_patterns:
            match = re.search(pattern, email_content)
            if match:
                participant_text = match.group(1).strip()
                # 쉼표나 공백으로 분리
                names = re.split(r'[,\s]+', participant_text)
                participants.extend([name.strip() for name in names if name.strip()])
        
        # 중복 제거 및 정리
        unique_participants = []
        for participant in participants:
            if participant and participant not in unique_participants:
                # 이메일 주소에서 이름 부분만 추출
                if '@' in participant:
                    name_part = participant.split('@')[0]
                    unique_participants.append(name_part)
                else:
                    unique_participants.append(participant)
        
        return unique_participants[:10]  # 최대 10명으로 제한
    
    def _extract_description(self, email_content: str, structured_info: Dict) -> Optional[str]:
        """
        일정 설명 추출
        
        Args:
            email_content: 이메일 내용
            structured_info: Gemini에서 추출한 구조화된 정보
            
        Returns:
            추출된 설명
        """
        # Gemini 결과 우선 사용
        if structured_info.get('description'):
            return structured_info['description']
        
        # 이메일 내용을 요약하여 설명으로 사용
        # 너무 긴 경우 앞부분만 사용
        description = email_content.strip()
        if len(description) > 500:
            description = description[:500] + "..."
        
        return description
    
    def _calculate_individual_confidence_scores(self, event_info: ExtractedEventInfo, email_content: str) -> Dict[str, float]:
        """
        각 필드별 신뢰도 점수 계산
        
        Args:
            event_info: 추출된 일정 정보
            email_content: 이메일 내용
            
        Returns:
            필드별 신뢰도 점수
        """
        scores = {}
        
        # 제목 신뢰도
        if event_info.summary:
            if any(keyword in event_info.summary for keyword in ['회의', '미팅', '만남', '약속']):
                scores['summary'] = 0.9
            else:
                scores['summary'] = 0.7
        else:
            scores['summary'] = 0.0
        
        # 날짜/시간 신뢰도
        if event_info.start_time:
            # 구체적인 시간이 있으면 높은 점수
            if not event_info.all_day:
                scores['datetime'] = 0.9
            else:
                scores['datetime'] = 0.7
        else:
            scores['datetime'] = 0.0
        
        # 위치 신뢰도
        if event_info.location:
            if any(keyword in event_info.location for keyword in self.location_keywords):
                scores['location'] = 0.8
            else:
                scores['location'] = 0.6
        else:
            scores['location'] = 0.0
        
        # 참석자 신뢰도
        if event_info.participants:
            if len(event_info.participants) > 1:
                scores['participants'] = 0.8
            else:
                scores['participants'] = 0.6
        else:
            scores['participants'] = 0.0
        
        return scores
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """
        전체 신뢰도 점수 계산
        
        Args:
            confidence_scores: 필드별 신뢰도 점수
            
        Returns:
            전체 신뢰도 점수
        """
        if not confidence_scores:
            return 0.0
        
        # 가중 평균 계산 (제목과 날짜/시간이 더 중요)
        weights = {
            'summary': 0.3,
            'datetime': 0.4,
            'location': 0.2,
            'participants': 0.1
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field, score in confidence_scores.items():
            weight = weights.get(field, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0