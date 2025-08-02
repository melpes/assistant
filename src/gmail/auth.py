"""
Gmail API 인증 모듈

이 모듈은 Gmail API를 사용하기 위한 OAuth 2.0 인증 흐름을 구현합니다.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# 로깅 설정
logger = logging.getLogger(__name__)

class GmailAuthService:
    """Gmail API 인증을 처리하는 클래스"""
    
    def __init__(
        self,
        scopes: Optional[List[str]] = None,
        token_path: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Gmail API 인증 서비스 초기화
        
        Args:
            scopes: 요청할 권한 범위 목록
            token_path: 토큰 파일 경로
            credentials_path: 인증 정보 파일 경로
        """
        self.scopes = scopes or ["https://www.googleapis.com/auth/gmail.modify"]
        self.token_path = token_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "gmail_token.json")
        self.credentials_path = credentials_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")
        self._credentials = None
        self._service = None
        
        logger.debug(f"GmailAuthService 초기화: token_path={self.token_path}, credentials_path={self.credentials_path}")
    
    def get_credentials(self, force_refresh: bool = False) -> Credentials:
        """
        Gmail API 인증 자격 증명 가져오기
        
        Args:
            force_refresh: 강제로 토큰을 갱신할지 여부
            
        Returns:
            유효한 Credentials 객체
            
        Raises:
            FileNotFoundError: 인증 정보 파일이 없는 경우
            ValueError: 인증 정보가 유효하지 않은 경우
        """
        if self._credentials and not force_refresh:
            if self._credentials.valid:
                return self._credentials
            elif self._credentials.expired and self._credentials.refresh_token:
                logger.info("토큰이 만료되어 갱신합니다.")
                self._credentials.refresh(Request())
                self._save_token(self._credentials)
                return self._credentials
        
        # 토큰 파일에서 자격 증명 로드 시도
        if os.path.exists(self.token_path):
            logger.info(f"토큰 파일에서 자격 증명을 로드합니다: {self.token_path}")
            with open(self.token_path, 'r') as token:
                token_data = json.load(token)
                self._credentials = Credentials.from_authorized_user_info(token_data, self.scopes)
            
            # 토큰이 만료되었고 갱신 토큰이 있는 경우 갱신
            if self._credentials.expired and self._credentials.refresh_token:
                logger.info("토큰이 만료되어 갱신합니다.")
                self._credentials.refresh(Request())
                self._save_token(self._credentials)
            
            if self._credentials.valid:
                return self._credentials
        
        # 새로운 인증 플로우 시작
        logger.info("새로운 인증 플로우를 시작합니다.")
        self._credentials = self._start_auth_flow()
        return self._credentials
    
    def _start_auth_flow(self) -> Credentials:
        """
        새로운 인증 플로우 시작
        
        Returns:
            새로운 Credentials 객체
            
        Raises:
            FileNotFoundError: 인증 정보 파일이 없는 경우
            ValueError: 인증 플로우 실패 시
        """
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"인증 정보 파일을 찾을 수 없습니다: {self.credentials_path}")
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.scopes)
            credentials = flow.run_local_server(port=0)
            
            # 토큰 저장
            self._save_token(credentials)
            return credentials
        except Exception as e:
            logger.error(f"인증 플로우 실패: {str(e)}")
            raise ValueError(f"인증 플로우 실패: {str(e)}")
    
    def _save_token(self, creds: Credentials) -> None:
        """
        자격 증명을 토큰 파일에 저장
        
        Args:
            creds: 저장할 Credentials 객체
        """
        # 토큰 파일 디렉토리가 없으면 생성
        token_dir = os.path.dirname(self.token_path)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir)
        
        # 토큰 저장
        token_data = json.loads(creds.to_json())
        with open(self.token_path, 'w') as token:
            json.dump(token_data, token, indent=2)
        
        logger.info(f"토큰이 저장되었습니다: {self.token_path}")
    
    def revoke_token(self) -> bool:
        """
        현재 토큰을 취소하고 토큰 파일을 삭제
        
        Returns:
            성공 여부
        """
        if self._credentials:
            try:
                # 토큰 취소 요청
                Request().post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': self._credentials.token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
                
                # 토큰 파일 삭제
                if os.path.exists(self.token_path):
                    os.remove(self.token_path)
                
                self._credentials = None
                self._service = None
                logger.info("토큰이 취소되었습니다.")
                return True
            except Exception as e:
                logger.error(f"토큰 취소 실패: {str(e)}")
                return False
        
        # 토큰 파일만 삭제
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            logger.info("토큰 파일이 삭제되었습니다.")
            return True
        
        return False
    
    def is_authenticated(self) -> bool:
        """
        현재 인증 상태 확인
        
        Returns:
            인증 상태
        """
        try:
            creds = self.get_credentials()
            return creds and creds.valid
        except Exception:
            return False
    
    def get_service(self) -> Resource:
        """
        Gmail API 서비스 객체 가져오기
        
        Returns:
            Gmail API 서비스 객체
            
        Raises:
            ValueError: 인증되지 않은 경우
        """
        if self._service:
            return self._service
        
        creds = self.get_credentials()
        if not creds or not creds.valid:
            raise ValueError("유효한 인증 정보가 없습니다. 먼저 인증을 수행하세요.")
        
        self._service = build('gmail', 'v1', credentials=creds)
        return self._service