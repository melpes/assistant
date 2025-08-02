"""
추출된 일정 정보의 신뢰도를 평가하는 ConfidenceEvaluator 클래스
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .models import ExtractedEventInfo, EmailMetadata


class ConfidenceEvaluator:
    """추출된 정보의 신뢰도를 평가하고 확인 요청 여부를 결정하는 클래스"""
    
    def __init__(self, 
                 default_threshold: float = 0.7,
                 field_thresholds: Optional[Dict[str, float]] = None):
        """
        Args:
            default_threshold: 기본 신뢰도 임계값
            field_thresholds: 필드별 신뢰도 임계값
        """
        self.logger = logging.getLogger(__name__)
        self.default_threshold = default_threshold
        self.field_thresholds = field_thresholds or {
            'summary': 0.6,
            'datetime': 0.8,
            'location': 0.5,
            'participants': 0.4
        }
        
        # 신뢰도 평가를 위한 키워드 및 패턴
        self.high_confidence_keywords = {
            'summary': ['회의', '미팅', '만남', '약속', '모임', '세미나', '워크샵', '컨퍼런스', '발표'],
            'location': ['회의실', '사무실', '카페', '식당', '빌딩', '층', '호', '역', '구', '동'],
            'participants': ['님', '씨', '대표', '팀장', '부장', '과장', '차장', '사장', '이사']
        }
        
        self.medium_confidence_keywords = {
            'summary': ['일정', '스케줄', '계획', '행사', '이벤트'],
            'location': ['장소', '위치', '주소', '에서'],
            'participants': ['참석자', '참가자', '참여자', '초대']
        }
        
        # 날짜/시간 신뢰도 평가 패턴
        self.datetime_patterns = {
            'high': [
                r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일\s*\d{1,2}시',  # 2024년 1월 15일 14시
                r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # 2024-01-15 14:00
                r'오전\s*\d{1,2}시\s*\d{1,2}분',  # 오전 2시 30분
                r'오후\s*\d{1,2}시\s*\d{1,2}분',  # 오후 2시 30분
            ],
            'medium': [
                r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',  # 2024년 1월 15일
                r'\d{1,2}월\s*\d{1,2}일\s*\d{1,2}시',  # 1월 15일 14시
                r'오전\s*\d{1,2}시',  # 오전 2시
                r'오후\s*\d{1,2}시',  # 오후 2시
            ],
            'low': [
                r'\d{1,2}월\s*\d{1,2}일',  # 1월 15일
                r'내일', r'모레', r'다음주', r'다음달'
            ]
        }
    
    def evaluate_confidence(self, 
                          event_info: ExtractedEventInfo, 
                          email_content: str,
                          email_metadata: Optional[EmailMetadata] = None) -> ExtractedEventInfo:
        """
        추출된 일정 정보의 신뢰도를 종합적으로 평가
        
        Args:
            event_info: 추출된 일정 정보
            email_content: 원본 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            신뢰도가 업데이트된 일정 정보
        """
        try:
            self.logger.info("신뢰도 평가 시작")
            
            # 각 필드별 신뢰도 재계산
            confidence_scores = {}
            
            # 제목 신뢰도 평가
            confidence_scores['summary'] = self._evaluate_summary_confidence(
                event_info.summary, email_content, email_metadata
            )
            
            # 날짜/시간 신뢰도 평가
            confidence_scores['datetime'] = self._evaluate_datetime_confidence(
                event_info.start_time, event_info.end_time, event_info.all_day, email_content
            )
            
            # 위치 신뢰도 평가
            confidence_scores['location'] = self._evaluate_location_confidence(
                event_info.location, email_content
            )
            
            # 참석자 신뢰도 평가
            confidence_scores['participants'] = self._evaluate_participants_confidence(
                event_info.participants, email_content, email_metadata
            )
            
            # 전체 신뢰도 계산
            overall_confidence = self._calculate_weighted_confidence(confidence_scores)
            
            # 컨텍스트 기반 신뢰도 조정
            overall_confidence = self._adjust_confidence_by_context(
                overall_confidence, event_info, email_content, email_metadata
            )
            
            # 결과 업데이트
            event_info.confidence_scores = confidence_scores
            event_info.overall_confidence = overall_confidence
            
            self.logger.info(f"신뢰도 평가 완료 - 전체: {overall_confidence:.2f}")
            return event_info
            
        except Exception as e:
            self.logger.error(f"신뢰도 평가 중 오류 발생: {str(e)}")
            event_info.overall_confidence = 0.0
            return event_info
    
    def should_request_confirmation(self, event_info: ExtractedEventInfo) -> Tuple[bool, List[str]]:
        """
        사용자 확인이 필요한지 결정
        
        Args:
            event_info: 추출된 일정 정보
            
        Returns:
            (확인 필요 여부, 확인이 필요한 필드 목록)
        """
        needs_confirmation = False
        low_confidence_fields = []
        
        # 전체 신뢰도가 임계값 이하인 경우
        if event_info.overall_confidence < self.default_threshold:
            needs_confirmation = True
        
        # 각 필드별 신뢰도 확인
        for field, score in event_info.confidence_scores.items():
            threshold = self.field_thresholds.get(field, self.default_threshold)
            if score < threshold:
                low_confidence_fields.append(field)
                needs_confirmation = True
        
        # 필수 정보 누락 확인
        if not event_info.summary or not event_info.start_time:
            needs_confirmation = True
            if not event_info.summary:
                low_confidence_fields.append('summary')
            if not event_info.start_time:
                low_confidence_fields.append('datetime')
        
        return needs_confirmation, list(set(low_confidence_fields))
    
    def get_confirmation_message(self, event_info: ExtractedEventInfo, low_confidence_fields: List[str]) -> str:
        """
        사용자 확인 요청 메시지 생성
        
        Args:
            event_info: 추출된 일정 정보
            low_confidence_fields: 신뢰도가 낮은 필드 목록
            
        Returns:
            확인 요청 메시지
        """
        message_parts = ["다음 일정 정보를 확인해주세요:\n"]
        
        # 추출된 정보 표시
        message_parts.append(f"📅 제목: {event_info.summary or '(확인 필요)'}")
        
        if event_info.start_time:
            if event_info.all_day:
                message_parts.append(f"🕐 날짜: {event_info.start_time.strftime('%Y년 %m월 %d일')} (종일)")
            else:
                message_parts.append(f"🕐 시작: {event_info.start_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
                if event_info.end_time:
                    message_parts.append(f"🕐 종료: {event_info.end_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
        else:
            message_parts.append("🕐 날짜/시간: (확인 필요)")
        
        if event_info.location:
            message_parts.append(f"📍 장소: {event_info.location}")
        
        if event_info.participants:
            participants_str = ', '.join(event_info.participants[:5])
            if len(event_info.participants) > 5:
                participants_str += f" 외 {len(event_info.participants) - 5}명"
            message_parts.append(f"👥 참석자: {participants_str}")
        
        # 신뢰도가 낮은 필드 강조
        if low_confidence_fields:
            field_names = {
                'summary': '제목',
                'datetime': '날짜/시간',
                'location': '장소',
                'participants': '참석자'
            }
            low_fields = [field_names.get(field, field) for field in low_confidence_fields]
            message_parts.append(f"\n⚠️ 다음 정보의 정확성을 특히 확인해주세요: {', '.join(low_fields)}")
        
        message_parts.append(f"\n🎯 전체 신뢰도: {event_info.overall_confidence:.1%}")
        message_parts.append("\n이 정보가 정확한가요? (예/아니오)")
        
        return '\n'.join(message_parts)
    
    def _evaluate_summary_confidence(self, 
                                   summary: str, 
                                   email_content: str,
                                   email_metadata: Optional[EmailMetadata]) -> float:
        """
        제목 신뢰도 평가
        
        Args:
            summary: 추출된 제목
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            제목 신뢰도 점수
        """
        if not summary:
            return 0.0
        
        score = 0.5  # 기본 점수
        
        # 고신뢰도 키워드 확인
        for keyword in self.high_confidence_keywords['summary']:
            if keyword in summary:
                score += 0.2
                break
        
        # 중간신뢰도 키워드 확인
        for keyword in self.medium_confidence_keywords['summary']:
            if keyword in summary:
                score += 0.1
                break
        
        # 이메일 제목과의 일치도 확인
        if email_metadata and email_metadata.subject:
            if summary in email_metadata.subject or email_metadata.subject in summary:
                score += 0.2
        
        # 길이 기반 조정
        if len(summary) < 5:
            score -= 0.2
        elif len(summary) > 50:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_datetime_confidence(self, 
                                    start_time: Optional[datetime],
                                    end_time: Optional[datetime],
                                    all_day: bool,
                                    email_content: str) -> float:
        """
        날짜/시간 신뢰도 평가
        
        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            all_day: 종일 여부
            email_content: 이메일 내용
            
        Returns:
            날짜/시간 신뢰도 점수
        """
        if not start_time:
            return 0.0
        
        score = 0.3  # 기본 점수 (날짜가 있으면)
        
        # 패턴 매칭으로 신뢰도 평가
        for confidence_level, patterns in self.datetime_patterns.items():
            for pattern in patterns:
                if re.search(pattern, email_content):
                    if confidence_level == 'high':
                        score += 0.5
                    elif confidence_level == 'medium':
                        score += 0.3
                    else:  # low
                        score += 0.1
                    break
            if score > 0.3:  # 패턴을 찾았으면 중단
                break
        
        # 구체적인 시간이 있으면 추가 점수
        if not all_day:
            score += 0.2
        
        # 종료 시간이 있으면 추가 점수
        if end_time:
            score += 0.1
            # 시작 시간보다 늦으면 추가 점수
            if end_time > start_time:
                score += 0.1
        
        # 미래 날짜인지 확인
        now = datetime.now()
        if start_time > now:
            score += 0.1
        elif start_time < now - timedelta(days=1):  # 과거 날짜면 감점
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_location_confidence(self, location: Optional[str], email_content: str) -> float:
        """
        위치 신뢰도 평가
        
        Args:
            location: 추출된 위치
            email_content: 이메일 내용
            
        Returns:
            위치 신뢰도 점수
        """
        if not location:
            return 0.0
        
        score = 0.4  # 기본 점수
        
        # 고신뢰도 키워드 확인
        for keyword in self.high_confidence_keywords['location']:
            if keyword in location:
                score += 0.3
                break
        
        # 중간신뢰도 키워드 확인
        for keyword in self.medium_confidence_keywords['location']:
            if keyword in location:
                score += 0.2
                break
        
        # 주소 형태 확인
        address_patterns = [
            r'\d+층',  # N층
            r'\d+호',  # N호
            r'\w+구\s+\w+동',  # 구 동
            r'\w+로\s+\d+',  # 로 번지
            r'\w+역',  # 역
        ]
        
        for pattern in address_patterns:
            if re.search(pattern, location):
                score += 0.2
                break
        
        # 길이 기반 조정
        if len(location) < 3:
            score -= 0.2
        elif len(location) > 100:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_participants_confidence(self, 
                                        participants: List[str],
                                        email_content: str,
                                        email_metadata: Optional[EmailMetadata]) -> float:
        """
        참석자 신뢰도 평가
        
        Args:
            participants: 추출된 참석자 목록
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            참석자 신뢰도 점수
        """
        if not participants:
            return 0.0
        
        score = 0.3  # 기본 점수
        
        # 참석자 수에 따른 점수
        if len(participants) == 1:
            score += 0.1
        elif len(participants) <= 5:
            score += 0.3
        elif len(participants) <= 10:
            score += 0.2
        else:
            score += 0.1  # 너무 많으면 신뢰도 낮음
        
        # 이메일 메타데이터와의 일치도 확인
        if email_metadata:
            metadata_emails = set()
            if email_metadata.sender:
                metadata_emails.add(email_metadata.sender)
            metadata_emails.update(email_metadata.recipients)
            metadata_emails.update(email_metadata.cc)
            
            # 참석자가 이메일 관련자와 일치하는지 확인
            matching_count = 0
            for participant in participants:
                for email in metadata_emails:
                    if participant in email or email in participant:
                        matching_count += 1
                        break
            
            if matching_count > 0:
                score += 0.2 * (matching_count / len(participants))
        
        # 한국어 이름 패턴 확인
        korean_name_pattern = r'[가-힣]{2,4}'
        korean_names = sum(1 for p in participants if re.match(korean_name_pattern, p))
        if korean_names > 0:
            score += 0.1 * (korean_names / len(participants))
        
        # 직책 키워드 확인
        for participant in participants:
            for keyword in self.high_confidence_keywords['participants']:
                if keyword in participant:
                    score += 0.1
                    break
        
        return min(1.0, max(0.0, score))
    
    def _calculate_weighted_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """
        가중 평균으로 전체 신뢰도 계산
        
        Args:
            confidence_scores: 필드별 신뢰도 점수
            
        Returns:
            전체 신뢰도 점수
        """
        # 가중치 설정 (제목과 날짜/시간이 가장 중요)
        weights = {
            'summary': 0.35,
            'datetime': 0.40,
            'location': 0.15,
            'participants': 0.10
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field, score in confidence_scores.items():
            weight = weights.get(field, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _adjust_confidence_by_context(self, 
                                    base_confidence: float,
                                    event_info: ExtractedEventInfo,
                                    email_content: str,
                                    email_metadata: Optional[EmailMetadata]) -> float:
        """
        컨텍스트를 고려한 신뢰도 조정
        
        Args:
            base_confidence: 기본 신뢰도
            event_info: 추출된 일정 정보
            email_content: 이메일 내용
            email_metadata: 이메일 메타데이터
            
        Returns:
            조정된 신뢰도 점수
        """
        adjusted_confidence = base_confidence
        
        # 이메일 제목에 일정 관련 키워드가 있으면 신뢰도 증가
        if email_metadata and email_metadata.subject:
            meeting_keywords = ['회의', '미팅', '만남', '약속', '모임', '일정', '스케줄']
            if any(keyword in email_metadata.subject for keyword in meeting_keywords):
                adjusted_confidence += 0.1
        
        # 이메일 내용의 길이 고려
        content_length = len(email_content)
        if content_length < 50:  # 너무 짧으면 신뢰도 감소
            adjusted_confidence -= 0.1
        elif content_length > 2000:  # 너무 길면 신뢰도 감소
            adjusted_confidence -= 0.05
        
        # 필수 정보 완성도 확인
        essential_fields = ['summary', 'start_time']
        missing_essential = sum(1 for field in essential_fields 
                              if not getattr(event_info, field, None))
        
        if missing_essential > 0:
            adjusted_confidence -= 0.2 * missing_essential
        
        # 일관성 확인
        if event_info.start_time and event_info.end_time:
            if event_info.end_time <= event_info.start_time:
                adjusted_confidence -= 0.2  # 종료 시간이 시작 시간보다 이르면 감점
        
        return min(1.0, max(0.0, adjusted_confidence))