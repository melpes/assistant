"""
일정 정보 추출 시스템 데모 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from src.gmail.event_extractor import EventExtractor
from src.gmail.confidence_evaluator import ConfidenceEvaluator
from src.gmail.models import EmailMetadata

def demo_event_extraction():
    """일정 정보 추출 데모"""
    print("=== 일정 정보 추출 시스템 데모 ===\n")
    
    # 테스트용 이메일 내용
    email_content = """
    안녕하세요,
    
    다음주 월요일 오후 2시에 팀 회의가 있습니다.
    장소: 3층 회의실 A
    참석자: 김철수, 이영희, 박민수
    
    회의 안건:
    1. 프로젝트 진행 상황 점검
    2. 다음 분기 계획 논의
    
    감사합니다.
    """
    
    # 이메일 메타데이터
    email_metadata = EmailMetadata(
        id="demo_email_123",
        subject="팀 회의 일정 안내",
        sender="manager@company.com",
        recipients=["user1@company.com", "user2@company.com"],
        date=datetime.now()
    )
    
    print("📧 이메일 내용:")
    print(email_content)
    print("\n" + "="*50 + "\n")
    
    try:
        # EventExtractor 초기화 (실제 API 키 없이 테스트)
        print("🔍 일정 정보 추출 중...")
        
        # 모의 추출 결과 (실제 Gemini API 없이)
        from src.gmail.models import ExtractedEventInfo
        
        event_info = ExtractedEventInfo(
            summary="팀 회의",
            start_time=datetime(2024, 1, 15, 14, 0),
            end_time=datetime(2024, 1, 15, 16, 0),
            location="3층 회의실 A",
            description="프로젝트 진행 상황 점검 및 다음 분기 계획 논의",
            participants=["김철수", "이영희", "박민수", "manager"],
            all_day=False
        )
        
        print("✅ 추출된 일정 정보:")
        print(f"📅 제목: {event_info.summary}")
        print(f"🕐 시작: {event_info.start_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
        print(f"🕐 종료: {event_info.end_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
        print(f"📍 장소: {event_info.location}")
        print(f"👥 참석자: {', '.join(event_info.participants)}")
        print(f"📝 설명: {event_info.description}")
        
        print("\n" + "="*50 + "\n")
        
        # 신뢰도 평가
        print("🎯 신뢰도 평가 중...")
        evaluator = ConfidenceEvaluator()
        evaluated_info = evaluator.evaluate_confidence(event_info, email_content, email_metadata)
        
        print("✅ 신뢰도 평가 결과:")
        for field, score in evaluated_info.confidence_scores.items():
            field_names = {
                'summary': '제목',
                'datetime': '날짜/시간',
                'location': '장소',
                'participants': '참석자'
            }
            print(f"  {field_names.get(field, field)}: {score:.1%}")
        
        print(f"\n🎯 전체 신뢰도: {evaluated_info.overall_confidence:.1%}")
        
        # 확인 요청 여부 결정
        needs_confirmation, low_fields = evaluator.should_request_confirmation(evaluated_info)
        
        if needs_confirmation:
            print("\n⚠️ 사용자 확인이 필요합니다.")
            print("신뢰도가 낮은 필드:", ', '.join(low_fields))
            
            confirmation_message = evaluator.get_confirmation_message(evaluated_info, low_fields)
            print("\n📋 확인 요청 메시지:")
            print(confirmation_message)
        else:
            print("\n✅ 신뢰도가 충분합니다. 자동으로 일정을 생성할 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        print("(실제 환경에서는 Gemini API 키가 필요합니다)")

def demo_korean_patterns():
    """한국어 패턴 인식 데모"""
    print("\n=== 한국어 패턴 인식 데모 ===\n")
    
    test_cases = [
        "내일 오후 2시 30분에 회의가 있습니다",
        "다음주 월요일 오전 10시에 만나요",
        "12월 25일 크리스마스 파티",
        "2024년 1월 15일 14시 프레젠테이션",
        "장소: 서울시 강남구 테헤란로 123",
        "참석자: 김철수, 이영희, 박민수님"
    ]
    
    evaluator = ConfidenceEvaluator()
    
    for i, text in enumerate(test_cases, 1):
        print(f"{i}. 테스트 텍스트: {text}")
        
        # 간단한 패턴 매칭 테스트
        if any(keyword in text for keyword in ['내일', '다음주', '월요일', '오후', '오전']):
            print("   ✅ 시간 패턴 인식됨")
        
        if any(keyword in text for keyword in ['장소', '서울', '강남구', '테헤란로']):
            print("   ✅ 위치 패턴 인식됨")
        
        if any(keyword in text for keyword in ['참석자', '김철수', '님']):
            print("   ✅ 참석자 패턴 인식됨")
        
        print()

if __name__ == "__main__":
    demo_event_extraction()
    demo_korean_patterns()