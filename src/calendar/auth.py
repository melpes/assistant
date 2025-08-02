"""
Google 캘린더 인증 서비스

이 모듈은 Google API 인증을 처리하는 서비스 클래스를 제공합니다.
"""
import os
import json
import time
import logging
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

from ..config import BASE_DIR
from .utils import retry, format_error_message
from .exceptions import (
    AuthenticationError,
    NetworkError,
    PermissionDeniedError,
    APIQuotaExceededError,
    TokenExpiredError,
    ServerError
)

# 로깅 설정
logger = logging.getLogger(__name__)


class GoogleAuthService:
    """Google API 인증을 처리하는 서비스 클래스"""
    
    def __init__(
        self,
        scopes: List[str] = None,
        token_path: str = None,
        credentials_path: str = None
    ):
        """
        GoogleAuthService 초기화
        
        Args:
            scopes: 요청할 권한 범위 목록
            token_path: 토큰 파일 경로 (기본값: 프로젝트 루트의 token.json)
            credentials_path: 인증 정보 파일 경로 (기본값: 프로젝트 루트의 credentials.json)
        """
        self.scopes = scopes or ["https://www.googleapis.com/auth/calendar"]
        self.token_path = token_path or os.path.join(BASE_DIR, 'token.json')
        self.credentials_path = credentials_path or os.path.join(BASE_DIR, 'credentials.json')
        self._credentials = None
    
    @retry(max_tries=3, delay=2.0, backoff_factor=2.0)
    def get_credentials(self, force_refresh: bool = False) -> Credentials:
        """
        Google API 인증 자격 증명을 가져옵니다.
        
        Args:
            force_refresh: 강제로 토큰을 갱신할지 여부
            
        Returns:
            유효한 Credentials 객체
            
        Raises:
            AuthenticationError: 인증 실패 시
            NetworkError: 네트워크 연결 문제 발생 시
            PermissionDeniedError: 권한 부족 시
        """
        # 이미 유효한 자격 증명이 있고 강제 갱신이 아니면 캐시된 자격 증명 반환
        if self._credentials and self._credentials.valid and not force_refresh:
            return self._credentials
        
        try:
            creds = None
            
            # 토큰 파일이 존재하면 로드
            if os.path.exists(self.token_path):
                try:
                    logger.info(f"토큰 파일 로드 중: {self.token_path}")
                    creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
                except (ValueError, json.JSONDecodeError) as e:
                    # 토큰 파일이 손상된 경우 처리
                    logger.warning(f"토큰 파일이 손상되었습니다: {e}")
                    creds = None
            
            # 자격 증명이 없거나 유효하지 않은 경우
            if not creds or not creds.valid:
                # 만료된 토큰이 있고 갱신 토큰이 있으면 갱신 시도
                if creds and creds.expired and creds.refresh_token:
                    try:
                        logger.info("만료된 토큰 갱신 시도 중...")
                        creds.refresh(Request())
                        logger.info("토큰이 성공적으로 갱신되었습니다.")
                    except Exception as e:
                        logger.warning(f"토큰 갱신 실패: {e}")
                        # 갱신 실패 시 새로운 인증 플로우 시작
                        creds = self._start_auth_flow()
                else:
                    # 토큰이 없거나 갱신할 수 없는 경우 새로운 인증 플로우 시작
                    logger.info("새로운 인증 플로우 시작...")
                    creds = self._start_auth_flow()
                
                # 토큰 저장
                self._save_token(creds)
            
            self._credentials = creds
            return creds
            
        except HttpError as e:
            if e.status_code == 401:
                logger.error(f"인증 오류 (401): {e}")
                raise TokenExpiredError("인증 토큰이 만료되었습니다", e)
            elif e.status_code == 403:
                logger.error(f"권한 오류 (403): {e}")
                raise PermissionDeniedError("Google API 접근 권한이 없습니다", e)
            elif e.status_code == 429:
                logger.error(f"할당량 초과 (429): {e}")
                raise APIQuotaExceededError("Google API 할당량이 초과되었습니다", e)
            elif 500 <= e.status_code < 600:
                logger.error(f"서버 오류 ({e.status_code}): {e}")
                raise ServerError(f"Google 서버 오류 (코드: {e.status_code})", e)
            else:
                logger.error(f"인증 중 HTTP 오류: {e}")
                raise AuthenticationError(f"인증 중 오류가 발생했습니다: {e}", e)
        except ConnectionError as e:
            logger.error(f"네트워크 연결 오류: {e}")
            raise NetworkError("네트워크 연결에 문제가 발생했습니다", e)
        except Exception as e:
            error_msg = format_error_message(e, "인증 중 예상치 못한 오류가 발생했습니다")
            logger.error(f"인증 실패: {error_msg}")
            raise AuthenticationError(error_msg, e)
    
    def _start_auth_flow(self) -> Credentials:
        """
        새로운 인증 플로우를 시작합니다.
        
        Returns:
            새로운 Credentials 객체
            
        Raises:
            AuthenticationError: 인증 실패 시
        """
        try:
            if not os.path.exists(self.credentials_path):
                error_msg = (
                    f"인증 정보 파일을 찾을 수 없습니다: {self.credentials_path}\n"
                    "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 "
                    "credentials.json 파일을 프로젝트 루트에 저장해주세요."
                )
                logger.error(error_msg)
                raise AuthenticationError(error_msg)
            
            logger.info("Google 계정 인증이 필요합니다. 브라우저 창이 열리면 로그인해주세요.")
            print("Google 계정 인증이 필요합니다. 브라우저 창이 열리면 로그인해주세요.")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                return flow.run_local_server(port=0)
            except ConnectionError as e:
                logger.error(f"인증 서버 연결 실패: {e}")
                raise NetworkError("인증 서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요.", e)
            
        except AuthenticationError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            error_msg = f"인증 플로우 시작 중 오류가 발생했습니다: {e}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg, e)
    
    def _save_token(self, creds: Credentials) -> None:
        """
        자격 증명을 토큰 파일에 저장합니다.
        
        Args:
            creds: 저장할 Credentials 객체
        """
        try:
            # 토큰 디렉토리가 없으면 생성
            token_dir = os.path.dirname(self.token_path)
            if token_dir and not os.path.exists(token_dir):
                os.makedirs(token_dir, exist_ok=True)
                
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
            logger.info(f"인증 토큰이 {self.token_path}에 저장되었습니다.")
        except PermissionError as e:
            error_msg = f"토큰 파일에 쓰기 권한이 없습니다: {self.token_path}"
            logger.error(f"{error_msg}: {e}")
            print(f"{error_msg}. 관리자 권한으로 실행하거나 다른 경로를 지정해주세요.")
        except Exception as e:
            error_msg = f"토큰 저장 중 오류가 발생했습니다: {e}"
            logger.error(error_msg)
            print(error_msg)
    
    def revoke_token(self) -> bool:
        """
        현재 토큰을 취소하고 토큰 파일을 삭제합니다.
        
        Returns:
            성공 여부
        """
        try:
            if os.path.exists(self.token_path):
                logger.info(f"토큰 파일 삭제 중: {self.token_path}")
                os.remove(self.token_path)
                self._credentials = None
                logger.info("토큰이 성공적으로 취소되었습니다.")
                print("토큰이 성공적으로 취소되었습니다.")
                return True
            logger.info(f"토큰 파일이 존재하지 않습니다: {self.token_path}")
            return False
        except PermissionError as e:
            error_msg = f"토큰 파일 삭제 권한이 없습니다: {self.token_path}"
            logger.error(f"{error_msg}: {e}")
            print(f"{error_msg}. 관리자 권한으로 실행해주세요.")
            return False
        except Exception as e:
            error_msg = f"토큰 취소 중 오류가 발생했습니다: {e}"
            logger.error(error_msg)
            print(error_msg)
            return False
    
    @retry(max_tries=2, delay=1.0)
    def is_authenticated(self) -> bool:
        """
        현재 인증 상태를 확인합니다.
        
        Returns:
            인증 상태 (True: 인증됨, False: 인증되지 않음)
        """
        try:
            logger.info("인증 상태 확인 중...")
            creds = self.get_credentials()
            is_valid = creds and creds.valid
            logger.info(f"인증 상태: {'유효함' if is_valid else '유효하지 않음'}")
            return is_valid
        except NetworkError as e:
            logger.warning(f"인증 상태 확인 중 네트워크 오류: {e}")
            return False
        except Exception as e:
            logger.warning(f"인증 상태 확인 중 오류 발생: {e}")
            return False