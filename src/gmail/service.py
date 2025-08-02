"""
Gmail 서비스 관리자 모듈

이 모듈은 Gmail API를 사용하여 이메일을 감지하고 관리하는 기능을 제공합니다.
"""

import time
import logging
import threading
import queue
from typing import List, Dict, Any, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
import base64
import json
import os
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import re

from googleapiclient.errors import HttpError
from googleapiclient.discovery import Resource

from .auth import GmailAuthService

# 로깅 설정
logger = logging.getLogger(__name__)

class GmailServiceManager:
    """Gmail API를 사용하여 이메일을 감지하고 관리하는 클래스"""
    
    def __init__(self, auth_service: Optional[GmailAuthService] = None, polling_interval: int = 60):
        """
        Gmail 서비스 관리자 초기화
        
        Args:
            auth_service: Gmail API 인증 서비스
            polling_interval: 폴링 간격(초)
        """
        self.auth_service = auth_service or GmailAuthService()
        self.polling_interval = polling_interval
        self._service = None
        self._last_check_time = None
        self._watching = False
        self._watch_thread = None
        self._stop_event = threading.Event()
        self._email_queue = queue.Queue()
        self._email_handlers = []
        self._filters_cache = {}
        self._labels_cache = {}
        self._processing_queue = queue.Queue()  # 이메일 처리 대기열
        self._processing_thread = None  # 이메일 처리 스레드
        self._processing = False  # 이메일 처리 상태
        
        logger.debug(f"GmailServiceManager 초기화: polling_interval={polling_interval}")
    
    def start_watching(self) -> bool:
        """
        이메일 감시 시작
        
        Returns:
            성공 여부
        """
        if self._watching:
            logger.info("이미 이메일 감시 중입니다.")
            return True
        
        self._watching = True
        self._last_check_time = datetime.now()
        self._stop_event.clear()
        
        # 감시 스레드 시작
        self._watch_thread = threading.Thread(target=self._watch_emails, daemon=True)
        self._watch_thread.start()
        
        logger.info("이메일 감시를 시작합니다.")
        return True
    
    def stop_watching(self) -> bool:
        """
        이메일 감시 중지
        
        Returns:
            성공 여부
        """
        if not self._watching:
            logger.info("이메일 감시 중이 아닙니다.")
            return True
        
        self._watching = False
        self._stop_event.set()
        
        # 스레드가 종료될 때까지 대기
        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=5.0)
        
        logger.info("이메일 감시를 중지했습니다.")
        return True
        
    def start_processing(self) -> bool:
        """
        이메일 처리 대기열 처리 시작
        
        Returns:
            성공 여부
        """
        if self._processing:
            logger.info("이미 이메일 처리 중입니다.")
            return True
        
        self._processing = True
        self._stop_event.clear()
        
        # 처리 스레드 시작
        self._processing_thread = threading.Thread(target=self._process_email_queue, daemon=True)
        self._processing_thread.start()
        
        logger.info("이메일 처리를 시작합니다.")
        return True
    
    def stop_processing(self) -> bool:
        """
        이메일 처리 대기열 처리 중지
        
        Returns:
            성공 여부
        """
        if not self._processing:
            logger.info("이메일 처리 중이 아닙니다.")
            return True
        
        self._processing = False
        self._stop_event.set()
        
        # 스레드가 종료될 때까지 대기
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)
        
        logger.info("이메일 처리를 중지했습니다.")
        return True
        
    def register_email_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        이메일 처리 핸들러 등록
        
        Args:
            handler: 이메일 처리 핸들러 함수
        """
        if handler not in self._email_handlers:
            self._email_handlers.append(handler)
            logger.debug(f"이메일 처리 핸들러가 등록되었습니다. 현재 핸들러 수: {len(self._email_handlers)}")
    
    def unregister_email_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        이메일 처리 핸들러 등록 해제
        
        Args:
            handler: 이메일 처리 핸들러 함수
        """
        if handler in self._email_handlers:
            self._email_handlers.remove(handler)
            logger.debug(f"이메일 처리 핸들러가 등록 해제되었습니다. 현재 핸들러 수: {len(self._email_handlers)}")
    
    def _watch_emails(self) -> None:
        """
        이메일 감시 스레드 함수
        """
        logger.info("이메일 감시 스레드가 시작되었습니다.")
        
        while self._watching and not self._stop_event.is_set():
            try:
                # 보관 처리된 이메일 확인
                archived_emails = self.check_archived_emails()
                for email in archived_emails:
                    self._process_email(email)
                
                # 다음 폴링까지 대기
                self._stop_event.wait(self.polling_interval)
            except Exception as e:
                logger.error(f"이메일 감시 중 오류 발생: {str(e)}")
                # 오류 발생 시 짧은 대기 후 재시도
                self._stop_event.wait(10)
        
        logger.info("이메일 감시 스레드가 종료되었습니다.")
        
    def watch_for_unread_emails(self, interval: int = 300) -> bool:
        """
        읽지 않은 이메일 감시 시작
        
        Args:
            interval: 폴링 간격(초)
            
        Returns:
            성공 여부
        """
        if self._watching:
            logger.info("이미 이메일 감시 중입니다.")
            return True
        
        # 폴링 간격 설정
        self.polling_interval = interval
        
        # 감시 스레드 시작
        self._watching = True
        self._last_check_time = datetime.now()
        self._stop_event.clear()
        
        self._watch_thread = threading.Thread(target=self._watch_unread_emails, daemon=True)
        self._watch_thread.start()
        
        logger.info(f"읽지 않은 이메일 감시를 시작합니다. 폴링 간격: {interval}초")
        return True
        
    def _watch_unread_emails(self) -> None:
        """
        읽지 않은 이메일 감시 스레드 함수
        """
        logger.info("읽지 않은 이메일 감시 스레드가 시작되었습니다.")
        
        while self._watching and not self._stop_event.is_set():
            try:
                # 읽지 않은 이메일 확인
                unread_emails = self.check_unread_emails()
                for email in unread_emails:
                    self._process_email(email)
                
                # 다음 폴링까지 대기
                self._stop_event.wait(self.polling_interval)
            except Exception as e:
                logger.error(f"읽지 않은 이메일 감시 중 오류 발생: {str(e)}")
                # 오류 발생 시 짧은 대기 후 재시도
                self._stop_event.wait(10)
        
        logger.info("읽지 않은 이메일 감시 스레드가 종료되었습니다.")
    
    def _process_email(self, email: Dict[str, Any]) -> None:
        """
        이메일 처리
        
        Args:
            email: 처리할 이메일 정보
        """
        # 이메일 큐에 추가
        self._email_queue.put(email)
        
        # 처리 대기열에 추가
        self._processing_queue.put(email)
        
        # 등록된 핸들러에 이메일 전달
        for handler in self._email_handlers:
            try:
                handler(email)
            except Exception as e:
                logger.error(f"이메일 핸들러 실행 중 오류 발생: {str(e)}")
    
    def _process_email_queue(self) -> None:
        """
        이메일 처리 대기열 처리 스레드 함수
        """
        logger.info("이메일 처리 스레드가 시작되었습니다.")
        
        while self._processing and not self._stop_event.is_set():
            try:
                # 대기열에서 이메일 가져오기
                try:
                    email = self._processing_queue.get(block=True, timeout=1.0)
                except queue.Empty:
                    continue
                
                # 이메일 처리
                try:
                    logger.info(f"이메일 처리 중: {email.get('id', 'unknown')}")
                    # 여기에 이메일 처리 로직 추가
                    
                    # 처리 완료 표시
                    self._processing_queue.task_done()
                except Exception as e:
                    logger.error(f"이메일 처리 중 오류 발생: {str(e)}")
                    # 오류 발생 시에도 처리 완료 표시
                    self._processing_queue.task_done()
            except Exception as e:
                logger.error(f"이메일 처리 스레드에서 오류 발생: {str(e)}")
        
        logger.info("이메일 처리 스레드가 종료되었습니다.")
    
    def get_email_from_queue(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        이메일 큐에서 이메일 가져오기
        
        Args:
            timeout: 대기 시간(초), None이면 무한 대기
            
        Returns:
            이메일 정보 또는 None(타임아웃 시)
        """
        try:
            return self._email_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None
            
    def get_queue_size(self) -> int:
        """
        이메일 처리 대기열 크기 가져오기
        
        Returns:
            대기열 크기
        """
        return self._processing_queue.qsize()
        
    def clear_queue(self) -> None:
        """
        이메일 처리 대기열 비우기
        """
        while not self._processing_queue.empty():
            try:
                self._processing_queue.get_nowait()
                self._processing_queue.task_done()
            except queue.Empty:
                break
    
    def check_archived_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        보관 처리된 이메일 확인
        
        Args:
            max_results: 최대 결과 수
            
        Returns:
            보관 처리된 이메일 목록
        """
        try:
            service = self._get_service()
            
            # 보관 처리된 이메일 검색 (INBOX 라벨이 없고 TRASH가 아닌 이메일)
            query = "-in:inbox -in:trash"
            if self._last_check_time:
                # 마지막 확인 시간 이후의 이메일만 검색
                time_str = self._last_check_time.strftime("%Y/%m/%d")
                query += f" after:{time_str}"
            
            results = service.users().messages().list(
                userId="me", q=query, maxResults=max_results).execute()
            
            messages = results.get("messages", [])
            if not messages:
                logger.info("보관 처리된 새 이메일이 없습니다.")
                return []
            
            # 이메일 상세 정보 가져오기
            emails = []
            for message in messages:
                email = self._get_email_details(message["id"])
                if email:
                    emails.append(email)
            
            logger.info(f"보관 처리된 이메일 {len(emails)}개를 찾았습니다.")
            return emails
        except HttpError as error:
            logger.error(f"보관 처리된 이메일 확인 중 오류 발생: {str(error)}")
            return []
    
    def check_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        읽지 않은 이메일 확인
        
        Args:
            max_results: 최대 결과 수
            
        Returns:
            읽지 않은 이메일 목록
        """
        try:
            service = self._get_service()
            
            # 읽지 않은 이메일 검색
            query = "is:unread"
            
            results = service.users().messages().list(
                userId="me", q=query, maxResults=max_results).execute()
            
            messages = results.get("messages", [])
            if not messages:
                logger.info("읽지 않은 이메일이 없습니다.")
                return []
            
            # 이메일 상세 정보 가져오기
            emails = []
            for message in messages:
                email = self._get_email_details(message["id"])
                if email:
                    emails.append(email)
            
            logger.info(f"읽지 않은 이메일 {len(emails)}개를 찾았습니다.")
            return emails
        except HttpError as error:
            logger.error(f"읽지 않은 이메일 확인 중 오류 발생: {str(error)}")
            return []
    
    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        이메일 검색
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            
        Returns:
            검색 결과 이메일 목록
        """
        try:
            service = self._get_service()
            
            results = service.users().messages().list(
                userId="me", q=query, maxResults=max_results).execute()
            
            messages = results.get("messages", [])
            if not messages:
                logger.info(f"검색 쿼리 '{query}'에 해당하는 이메일이 없습니다.")
                return []
            
            # 이메일 상세 정보 가져오기
            emails = []
            for message in messages:
                email = self._get_email_details(message["id"])
                if email:
                    emails.append(email)
            
            logger.info(f"검색 쿼리 '{query}'에 해당하는 이메일 {len(emails)}개를 찾았습니다.")
            return emails
        except HttpError as error:
            logger.error(f"이메일 검색 중 오류 발생: {str(error)}")
            return []
    
    def apply_label(self, email_ids: List[str], label_name: str) -> bool:
        """
        이메일에 라벨 적용
        
        Args:
            email_ids: 이메일 ID 목록
            label_name: 적용할 라벨 이름
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 라벨 ID 가져오기
            label_id = self._get_or_create_label(label_name)
            if not label_id:
                logger.error(f"라벨 '{label_name}'을 가져오거나 생성할 수 없습니다.")
                return False
            
            # 각 이메일에 라벨 적용
            for email_id in email_ids:
                service.users().messages().modify(
                    userId="me",
                    id=email_id,
                    body={"addLabelIds": [label_id]}
                ).execute()
            
            logger.info(f"이메일 {len(email_ids)}개에 라벨 '{label_name}'을 적용했습니다.")
            return True
        except HttpError as error:
            logger.error(f"라벨 적용 중 오류 발생: {str(error)}")
            return False
            
    def remove_label(self, email_ids: List[str], label_name: str) -> bool:
        """
        이메일에서 라벨 제거
        
        Args:
            email_ids: 이메일 ID 목록
            label_name: 제거할 라벨 이름
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 라벨 ID 가져오기
            label_id = self._get_label_id(label_name)
            if not label_id:
                logger.error(f"라벨 '{label_name}'을 찾을 수 없습니다.")
                return False
            
            # 각 이메일에서 라벨 제거
            for email_id in email_ids:
                service.users().messages().modify(
                    userId="me",
                    id=email_id,
                    body={"removeLabelIds": [label_id]}
                ).execute()
            
            logger.info(f"이메일 {len(email_ids)}개에서 라벨 '{label_name}'을 제거했습니다.")
            return True
        except HttpError as error:
            logger.error(f"라벨 제거 중 오류 발생: {str(error)}")
            return False
            
    def get_labels(self) -> List[Dict[str, Any]]:
        """
        라벨 목록 가져오기
        
        Returns:
            라벨 목록
        """
        try:
            # 캐시된 라벨이 있으면 반환
            if self._labels_cache:
                return list(self._labels_cache.values())
            
            service = self._get_service()
            
            # 라벨 목록 가져오기
            result = service.users().labels().list(userId="me").execute()
            labels = result.get("labels", [])
            
            # 라벨 캐시 업데이트
            self._labels_cache = {label["id"]: label for label in labels}
            
            logger.info(f"라벨 {len(labels)}개를 가져왔습니다.")
            return labels
        except HttpError as error:
            logger.error(f"라벨 목록 가져오기 중 오류 발생: {str(error)}")
            return []
            
    def create_label(self, label_name: str, label_color: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        라벨 생성
        
        Args:
            label_name: 라벨 이름
            label_color: 라벨 색상 (선택 사항)
            
        Returns:
            생성된 라벨 ID
        """
        try:
            service = self._get_service()
            
            # 라벨 본문 구성
            label_body = {"name": label_name}
            if label_color:
                label_body["color"] = label_color
            
            # 라벨 생성
            result = service.users().labels().create(
                userId="me",
                body=label_body
            ).execute()
            
            label_id = result.get("id")
            
            # 라벨 캐시 업데이트
            self._labels_cache[label_id] = result
            
            logger.info(f"라벨 '{label_name}'이 생성되었습니다. ID: {label_id}")
            return label_id
        except HttpError as error:
            logger.error(f"라벨 생성 중 오류 발생: {str(error)}")
            return None
            
    def update_label(self, label_id: str, label_name: Optional[str] = None, 
                    label_color: Optional[Dict[str, str]] = None) -> bool:
        """
        라벨 수정
        
        Args:
            label_id: 라벨 ID
            label_name: 새 라벨 이름 (선택 사항)
            label_color: 새 라벨 색상 (선택 사항)
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 현재 라벨 정보 가져오기
            current_label = self.get_label(label_id)
            if not current_label:
                logger.error(f"라벨 ID: {label_id}를 찾을 수 없습니다.")
                return False
            
            # 라벨 본문 구성
            label_body = {}
            if label_name:
                label_body["name"] = label_name
            if label_color:
                label_body["color"] = label_color
            
            # 라벨 수정
            result = service.users().labels().patch(
                userId="me",
                id=label_id,
                body=label_body
            ).execute()
            
            # 라벨 캐시 업데이트
            self._labels_cache[label_id] = result
            
            logger.info(f"라벨 ID: {label_id}가 수정되었습니다.")
            return True
        except HttpError as error:
            logger.error(f"라벨 수정 중 오류 발생: {str(error)}")
            return False
            
    def delete_label(self, label_id: str) -> bool:
        """
        라벨 삭제
        
        Args:
            label_id: 라벨 ID
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 라벨 삭제
            service.users().labels().delete(
                userId="me", id=label_id).execute()
            
            # 라벨 캐시에서 제거
            if label_id in self._labels_cache:
                del self._labels_cache[label_id]
            
            logger.info(f"라벨 ID: {label_id}가 삭제되었습니다.")
            return True
        except HttpError as error:
            logger.error(f"라벨 삭제 중 오류 발생: {str(error)}")
            return False
            
    def get_label(self, label_id: str) -> Optional[Dict[str, Any]]:
        """
        라벨 정보 가져오기
        
        Args:
            label_id: 라벨 ID
            
        Returns:
            라벨 정보
        """
        try:
            # 캐시된 라벨이 있으면 반환
            if label_id in self._labels_cache:
                return self._labels_cache[label_id]
            
            service = self._get_service()
            
            # 라벨 정보 가져오기
            label_info = service.users().labels().get(
                userId="me", id=label_id).execute()
            
            # 라벨 캐시 업데이트
            self._labels_cache[label_id] = label_info
            
            return label_info
        except HttpError as error:
            logger.error(f"라벨 정보 가져오기 중 오류 발생: {str(error)}")
            return None
            
    def _get_label_id(self, label_name: str) -> Optional[str]:
        """
        라벨 이름으로 라벨 ID 가져오기
        
        Args:
            label_name: 라벨 이름
            
        Returns:
            라벨 ID
        """
        try:
            # 라벨 목록 가져오기
            labels = self.get_labels()
            
            # 라벨 이름으로 ID 찾기
            for label in labels:
                if label["name"] == label_name:
                    return label["id"]
            
            return None
        except Exception as e:
            logger.error(f"라벨 ID 가져오기 중 오류 발생: {str(e)}")
            return None
    
    def archive_emails(self, email_ids: List[str]) -> bool:
        """
        이메일 보관 처리
        
        Args:
            email_ids: 이메일 ID 목록
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 각 이메일에서 INBOX 라벨 제거
            for email_id in email_ids:
                service.users().messages().modify(
                    userId="me",
                    id=email_id,
                    body={"removeLabelIds": ["INBOX"]}
                ).execute()
            
            logger.info(f"이메일 {len(email_ids)}개를 보관 처리했습니다.")
            return True
        except HttpError as error:
            logger.error(f"이메일 보관 처리 중 오류 발생: {str(error)}")
            return False
    
    def delete_emails(self, email_ids: List[str]) -> bool:
        """
        이메일 삭제
        
        Args:
            email_ids: 이메일 ID 목록
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 각 이메일 삭제 (휴지통으로 이동)
            for email_id in email_ids:
                service.users().messages().trash(
                    userId="me",
                    id=email_id
                ).execute()
            
            logger.info(f"이메일 {len(email_ids)}개를 삭제했습니다.")
            return True
        except HttpError as error:
            logger.error(f"이메일 삭제 중 오류 발생: {str(error)}")
            return False
    
    def create_filter(self, filter_criteria: Dict[str, Any], actions: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        이메일 필터 생성
        
        Args:
            filter_criteria: 필터 조건
            actions: 필터 적용 시 수행할 작업 (선택 사항)
            
        Returns:
            생성된 필터 ID
        """
        try:
            service = self._get_service()
            
            # 필터 본문 구성
            filter_body = {"criteria": filter_criteria}
            if actions:
                filter_body["action"] = actions
            
            # 필터 생성
            result = service.users().settings().filters().create(
                userId="me",
                body=filter_body
            ).execute()
            
            filter_id = result.get("id")
            logger.info(f"필터가 생성되었습니다. ID: {filter_id}")
            
            # 필터 캐시 갱신
            self._filters_cache = {}
            
            return filter_id
        except HttpError as error:
            logger.error(f"필터 생성 중 오류 발생: {str(error)}")
            return None
            
    def get_filters(self) -> List[Dict[str, Any]]:
        """
        필터 목록 가져오기
        
        Returns:
            필터 목록
        """
        try:
            # 캐시된 필터가 있으면 반환
            if self._filters_cache:
                return list(self._filters_cache.values())
            
            service = self._get_service()
            
            # 필터 목록 가져오기
            result = service.users().settings().filters().list(userId="me").execute()
            filters = result.get("filter", [])
            
            # 필터 캐시 업데이트
            self._filters_cache = {f["id"]: f for f in filters}
            
            logger.info(f"필터 {len(filters)}개를 가져왔습니다.")
            return filters
        except HttpError as error:
            logger.error(f"필터 목록 가져오기 중 오류 발생: {str(error)}")
            return []
            
    def get_filter(self, filter_id: str) -> Optional[Dict[str, Any]]:
        """
        필터 정보 가져오기
        
        Args:
            filter_id: 필터 ID
            
        Returns:
            필터 정보
        """
        try:
            # 캐시된 필터가 있으면 반환
            if filter_id in self._filters_cache:
                return self._filters_cache[filter_id]
            
            service = self._get_service()
            
            # 필터 정보 가져오기
            filter_info = service.users().settings().filters().get(
                userId="me", id=filter_id).execute()
            
            # 필터 캐시 업데이트
            self._filters_cache[filter_id] = filter_info
            
            return filter_info
        except HttpError as error:
            logger.error(f"필터 정보 가져오기 중 오류 발생: {str(error)}")
            return None
            
    def delete_filter(self, filter_id: str) -> bool:
        """
        필터 삭제
        
        Args:
            filter_id: 필터 ID
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 필터 삭제
            service.users().settings().filters().delete(
                userId="me", id=filter_id).execute()
            
            # 필터 캐시에서 제거
            if filter_id in self._filters_cache:
                del self._filters_cache[filter_id]
            
            logger.info(f"필터 ID: {filter_id}가 삭제되었습니다.")
            return True
        except HttpError as error:
            logger.error(f"필터 삭제 중 오류 발생: {str(error)}")
            return False
    
    def _get_service(self) -> Resource:
        """
        Gmail API 서비스 객체 가져오기
        
        Returns:
            Gmail API 서비스 객체
        """
        if not self._service:
            self._service = self.auth_service.get_service()
        return self._service
    
    def _get_email_details(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        이메일 상세 정보 가져오기
        
        Args:
            email_id: 이메일 ID
            
        Returns:
            이메일 상세 정보
        """
        try:
            service = self._get_service()
            
            # 이메일 메시지 가져오기
            message = service.users().messages().get(
                userId="me", id=email_id).execute()
            
            # 헤더 정보 추출
            headers = {}
            for header in message["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
            
            # 이메일 정보 구성
            email_info = {
                "id": message["id"],
                "threadId": message["threadId"],
                "labelIds": message.get("labelIds", []),
                "snippet": message.get("snippet", ""),
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "date": headers.get("date", ""),
                "raw_message": message
            }
            
            return email_info
        except HttpError as error:
            logger.error(f"이메일 상세 정보 가져오기 중 오류 발생: {str(error)}")
            return None
    
    def update_filter(self, filter_id: str, filter_criteria: Optional[Dict[str, Any]] = None, 
                     actions: Optional[Dict[str, Any]] = None) -> bool:
        """
        필터 수정
        
        Args:
            filter_id: 필터 ID
            filter_criteria: 필터 조건 (선택 사항)
            actions: 필터 적용 시 수행할 작업 (선택 사항)
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 현재 필터 정보 가져오기
            current_filter = self.get_filter(filter_id)
            if not current_filter:
                logger.error(f"필터 ID: {filter_id}를 찾을 수 없습니다.")
                return False
            
            # 필터 본문 구성
            filter_body = {}
            if filter_criteria:
                filter_body["criteria"] = filter_criteria
            if actions:
                filter_body["action"] = actions
            
            # 필터 수정 (Gmail API는 필터 수정을 직접 지원하지 않으므로 삭제 후 재생성)
            self.delete_filter(filter_id)
            new_filter_id = self.create_filter(
                filter_criteria or current_filter.get("criteria", {}),
                actions or current_filter.get("action", {})
            )
            
            if new_filter_id:
                logger.info(f"필터 ID: {filter_id}가 수정되었습니다. 새 ID: {new_filter_id}")
                return True
            else:
                logger.error(f"필터 수정 실패: {filter_id}")
                return False
        except HttpError as error:
            logger.error(f"필터 수정 중 오류 발생: {str(error)}")
            return False
    
    def get_email_ids_from_queue(self) -> List[str]:
        """
        이메일 처리 대기열에서 이메일 ID 목록 추출
        
        Returns:
            이메일 ID 목록
        """
        email_ids = []
        temp_queue = queue.Queue()
        
        # 대기열에서 모든 이메일을 가져와서 ID 추출
        while not self._processing_queue.empty():
            try:
                email = self._processing_queue.get_nowait()
                email_ids.append(email.get("id", ""))
                temp_queue.put(email)
            except queue.Empty:
                break
        
        # 이메일을 다시 대기열에 넣기
        while not temp_queue.empty():
            try:
                email = temp_queue.get_nowait()
                self._processing_queue.put(email)
            except queue.Empty:
                break
        
        return email_ids
    
    def add_email_to_queue(self, email: Dict[str, Any]) -> None:
        """
        이메일을 처리 대기열에 추가
        
        Args:
            email: 추가할 이메일 정보
        """
        self._processing_queue.put(email)
        logger.debug(f"이메일이 처리 대기열에 추가되었습니다: {email.get('id', 'unknown')}")
    
    def _get_or_create_label(self, label_name: str) -> Optional[str]:
        """
        라벨 ID 가져오기 또는 생성하기
        
        Args:
            label_name: 라벨 이름
            
        Returns:
            라벨 ID
        """
        try:
            service = self._get_service()
            
            # 라벨 목록 가져오기
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            
            # 기존 라벨 찾기
            for label in labels:
                if label["name"] == label_name:
                    return label["id"]
            
            # 라벨이 없으면 생성
            label = service.users().labels().create(
                userId="me",
                body={"name": label_name}
            ).execute()
            
            return label["id"]
        except HttpError as error:
            logger.error(f"라벨 가져오기 또는 생성 중 오류 발생: {str(error)}")
            return None