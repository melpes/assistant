"""
Gmail API 인증 예제

이 스크립트는 Gmail API 인증 및 서비스 관리자 사용 방법을 보여줍니다.
"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.gmail.auth import GmailAuthService
from src.gmail.service import GmailServiceManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Gmail API 인증 및 서비스 관리자 테스트"""
    try:
        # 인증 서비스 생성
        auth_service = GmailAuthService()
        
        # 인증 상태 확인
        if not auth_service.is_authenticated():
            logger.info("인증되지 않았습니다. 인증 플로우를 시작합니다.")
            auth_service.get_credentials()
        
        # 인증 상태 다시 확인
        if auth_service.is_authenticated():
            logger.info("인증에 성공했습니다.")
        else:
            logger.error("인증에 실패했습니다.")
            return
        
        # Gmail 서비스 관리자 생성
        gmail_service = GmailServiceManager(auth_service)
        
        # 이메일 감시 시작
        gmail_service.start_watching()
        
        # 읽지 않은 이메일 확인
        unread_emails = gmail_service.check_unread_emails(max_results=5)
        logger.info(f"읽지 않은 이메일 수: {len(unread_emails)}")
        
        # 읽지 않은 이메일 정보 출력
        for i, email in enumerate(unread_emails):
            logger.info(f"이메일 {i+1}:")
            logger.info(f"  제목: {email['subject']}")
            logger.info(f"  보낸 사람: {email['from']}")
            logger.info(f"  받는 사람: {email['to']}")
            logger.info(f"  날짜: {email['date']}")
            logger.info(f"  스니펫: {email['snippet']}")
            logger.info("---")
        
        # 이메일 감시 중지
        gmail_service.stop_watching()
        
        logger.info("Gmail API 인증 및 서비스 관리자 테스트가 완료되었습니다.")
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()