"""
이메일 처리기 모듈

이 모듈은 Gmail API를 통해 가져온 이메일의 내용을 처리하고 분석하는 기능을 제공합니다.
"""

import base64
import email
import html
import re
import logging
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import quopri
# import chardet  # 선택적 의존성
import json

from googleapiclient.errors import HttpError
from googleapiclient.discovery import Resource

from .service import GmailServiceManager

# 로깅 설정
logger = logging.getLogger(__name__)

class EmailProcessor:
    """이메일 내용을 가져와 처리하는 클래스"""
    
    def __init__(self, gmail_service_manager: GmailServiceManager):
        """
        이메일 처리기 초기화
        
        Args:
            gmail_service_manager: Gmail 서비스 관리자
        """
        self.gmail_service_manager = gmail_service_manager
        self._service = None
        logger.debug("EmailProcessor 초기화 완료")
    
    def process_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        이메일 처리
        
        Args:
            email_id: 처리할 이메일 ID
            
        Returns:
            처리된 이메일 내용
        """
        try:
            logger.info(f"이메일 처리 시작: {email_id}")
            
            # 이메일 내용 가져오기
            email_content = self.get_email_content(email_id)
            if not email_content:
                logger.error(f"이메일 내용을 가져올 수 없습니다: {email_id}")
                return None
            
            # 이메일 메타데이터 추출
            metadata = self.extract_email_metadata(email_content)
            
            # 이메일 본문 텍스트 정제
            cleaned_text = self._clean_email_text(email_content.get("body", ""))
            
            # HTML 내용 처리
            html_content = self._process_html_content(email_content.get("html_body", ""))
            
            # 첨부 파일 처리
            attachments = self.extract_attachments(email_content)
            
            # 처리된 이메일 정보 구성
            processed_email = {
                "id": email_id,
                "metadata": metadata,
                "cleaned_text": cleaned_text,
                "html_content": html_content,
                "attachments": attachments,
                "raw_content": email_content,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"이메일 처리 완료: {email_id}")
            return processed_email
            
        except Exception as e:
            logger.error(f"이메일 처리 중 오류 발생 ({email_id}): {str(e)}")
            return None
    
    def process_emails(self, email_ids: List[str], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        여러 이메일 일괄 처리
        
        Args:
            email_ids: 처리할 이메일 ID 목록
            batch_size: 배치 크기 (기본값: 10)
            
        Returns:
            처리된 이메일 내용 목록
        """
        processed_emails = []
        failed_emails = []
        
        logger.info(f"이메일 일괄 처리 시작: {len(email_ids)}개 (배치 크기: {batch_size})")
        
        # 배치 단위로 처리
        for i in range(0, len(email_ids), batch_size):
            batch = email_ids[i:i + batch_size]
            logger.debug(f"배치 처리 중: {i//batch_size + 1}/{(len(email_ids) + batch_size - 1)//batch_size}")
            
            for email_id in batch:
                try:
                    processed_email = self.process_email(email_id)
                    if processed_email:
                        processed_emails.append(processed_email)
                    else:
                        failed_emails.append(email_id)
                except Exception as e:
                    logger.error(f"이메일 처리 실패 ({email_id}): {str(e)}")
                    failed_emails.append(email_id)
        
        success_count = len(processed_emails)
        failure_count = len(failed_emails)
        
        logger.info(f"이메일 일괄 처리 완료: {success_count}개 성공, {failure_count}개 실패")
        
        if failed_emails:
            logger.warning(f"처리 실패한 이메일 ID: {failed_emails}")
        
        return processed_emails
    
    def get_email_content(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        이메일 내용 가져오기
        
        Args:
            email_id: 이메일 ID
            
        Returns:
            이메일 내용
        """
        try:
            service = self._get_service()
            
            # 이메일 메시지 가져오기 (전체 내용 포함)
            message = service.users().messages().get(
                userId="me", id=email_id, format="full").execute()
            
            # 이메일 내용 파싱
            email_content = self._parse_email_message(message)
            
            logger.debug(f"이메일 내용 가져오기 완료: {email_id}")
            return email_content
            
        except HttpError as error:
            logger.error(f"이메일 내용 가져오기 중 오류 발생 ({email_id}): {str(error)}")
            return None
    
    def extract_email_metadata(self, email_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        이메일 메타데이터 추출
        
        Args:
            email_content: 이메일 내용
            
        Returns:
            이메일 메타데이터
        """
        try:
            raw_message = email_content.get("raw_message", {})
            payload = raw_message.get("payload", {})
            headers = payload.get("headers", [])
            
            # 헤더 정보를 딕셔너리로 변환
            header_dict = {}
            for header in headers:
                header_dict[header["name"].lower()] = header["value"]
            
            # 메타데이터 구성
            metadata = {
                "id": raw_message.get("id", ""),
                "thread_id": raw_message.get("threadId", ""),
                "label_ids": raw_message.get("labelIds", []),
                "snippet": raw_message.get("snippet", ""),
                "subject": header_dict.get("subject", ""),
                "from": header_dict.get("from", ""),
                "to": header_dict.get("to", ""),
                "cc": header_dict.get("cc", ""),
                "bcc": header_dict.get("bcc", ""),
                "date": header_dict.get("date", ""),
                "message_id": header_dict.get("message-id", ""),
                "in_reply_to": header_dict.get("in-reply-to", ""),
                "references": header_dict.get("references", ""),
                "content_type": header_dict.get("content-type", ""),
                "size_estimate": raw_message.get("sizeEstimate", 0),
                "internal_date": raw_message.get("internalDate", "")
            }
            
            # 수신자 목록 파싱
            metadata["recipients"] = self._parse_recipients(
                metadata["to"], metadata["cc"], metadata["bcc"]
            )
            
            # 날짜 파싱
            metadata["parsed_date"] = self._parse_email_date(metadata["date"])
            
            logger.debug(f"이메일 메타데이터 추출 완료: {metadata['id']}")
            return metadata
            
        except Exception as e:
            logger.error(f"이메일 메타데이터 추출 중 오류 발생: {str(e)}")
            return {}
    
    def extract_attachments(self, email_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        이메일 첨부 파일 추출
        
        Args:
            email_content: 이메일 내용
            
        Returns:
            첨부 파일 목록
        """
        try:
            attachments = []
            raw_message = email_content.get("raw_message", {})
            
            # 첨부 파일 재귀적으로 찾기
            self._extract_attachments_recursive(raw_message.get("payload", {}), attachments)
            
            logger.debug(f"첨부 파일 추출 완료: {len(attachments)}개")
            return attachments
            
        except Exception as e:
            logger.error(f"첨부 파일 추출 중 오류 발생: {str(e)}")
            return []
    
    def mark_as_read(self, email_id: str) -> bool:
        """
        이메일을 읽음으로 표시
        
        Args:
            email_id: 이메일 ID
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # UNREAD 라벨 제거
            service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            
            logger.info(f"이메일을 읽음으로 표시: {email_id}")
            return True
            
        except HttpError as error:
            logger.error(f"이메일 읽음 표시 중 오류 발생 ({email_id}): {str(error)}")
            return False
    
    def mark_as_unread(self, email_id: str) -> bool:
        """
        이메일을 읽지 않음으로 표시
        
        Args:
            email_id: 이메일 ID
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # UNREAD 라벨 추가
            service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"addLabelIds": ["UNREAD"]}
            ).execute()
            
            logger.info(f"이메일을 읽지 않음으로 표시: {email_id}")
            return True
            
        except HttpError as error:
            logger.error(f"이메일 읽지 않음 표시 중 오류 발생 ({email_id}): {str(error)}")
            return False
    
    def reply_to_email(self, email_id: str, message: str, subject: Optional[str] = None) -> bool:
        """
        이메일에 답장
        
        Args:
            email_id: 원본 이메일 ID
            message: 답장 내용
            subject: 답장 제목 (선택 사항)
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 원본 이메일 정보 가져오기
            original_message = service.users().messages().get(
                userId="me", id=email_id).execute()
            
            # 원본 이메일 헤더 파싱
            headers = {}
            for header in original_message["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
            
            # 답장 이메일 구성
            reply_subject = subject or f"Re: {headers.get('subject', '')}"
            reply_to = headers.get("from", "")
            thread_id = original_message.get("threadId", "")
            
            # MIME 메시지 생성
            mime_message = MIMEText(message, "plain", "utf-8")
            mime_message["To"] = reply_to
            mime_message["Subject"] = reply_subject
            mime_message["In-Reply-To"] = headers.get("message-id", "")
            mime_message["References"] = headers.get("message-id", "")
            
            # 메시지 인코딩
            raw_message = base64.urlsafe_b64encode(
                mime_message.as_bytes()).decode("utf-8")
            
            # 답장 전송
            send_result = service.users().messages().send(
                userId="me",
                body={
                    "raw": raw_message,
                    "threadId": thread_id
                }
            ).execute()
            
            logger.info(f"이메일 답장 전송 완료: {email_id} -> {send_result.get('id')}")
            return True
            
        except HttpError as error:
            logger.error(f"이메일 답장 중 오류 발생 ({email_id}): {str(error)}")
            return False
    
    def _get_service(self) -> Resource:
        """
        Gmail API 서비스 객체 가져오기
        
        Returns:
            Gmail API 서비스 객체
        """
        if not self._service:
            self._service = self.gmail_service_manager._get_service()
        return self._service
    
    def _parse_email_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        이메일 메시지 파싱
        
        Args:
            message: Gmail API 메시지 객체
            
        Returns:
            파싱된 이메일 내용
        """
        try:
            payload = message.get("payload", {})
            
            # 이메일 내용 초기화
            email_content = {
                "raw_message": message,
                "body": "",
                "html_body": "",
                "attachments": []
            }
            
            # 이메일 본문 추출
            self._extract_email_body(payload, email_content)
            
            return email_content
            
        except Exception as e:
            logger.error(f"이메일 메시지 파싱 중 오류 발생: {str(e)}")
            return {"raw_message": message, "body": "", "html_body": "", "attachments": []}
    
    def _extract_email_body(self, payload: Dict[str, Any], email_content: Dict[str, Any]) -> None:
        """
        이메일 본문 추출 (재귀적)
        
        Args:
            payload: 이메일 페이로드
            email_content: 이메일 내용 딕셔너리
        """
        try:
            mime_type = payload.get("mimeType", "")
            
            # 단일 파트 메시지
            if "parts" not in payload:
                if mime_type == "text/plain":
                    body_data = payload.get("body", {}).get("data", "")
                    if body_data:
                        decoded_body = self._decode_base64(body_data)
                        email_content["body"] += decoded_body
                elif mime_type == "text/html":
                    body_data = payload.get("body", {}).get("data", "")
                    if body_data:
                        decoded_body = self._decode_base64(body_data)
                        email_content["html_body"] += decoded_body
            else:
                # 멀티파트 메시지
                for part in payload.get("parts", []):
                    self._extract_email_body(part, email_content)
                    
        except Exception as e:
            logger.error(f"이메일 본문 추출 중 오류 발생: {str(e)}")
    
    def _extract_attachments_recursive(self, payload: Dict[str, Any], 
                                     attachments: List[Dict[str, Any]]) -> None:
        """
        첨부 파일 재귀적 추출
        
        Args:
            payload: 이메일 페이로드
            attachments: 첨부 파일 목록
        """
        try:
            # 첨부 파일 확인
            if payload.get("filename"):
                attachment_info = {
                    "filename": payload["filename"],
                    "mime_type": payload.get("mimeType", ""),
                    "size": payload.get("body", {}).get("size", 0),
                    "attachment_id": payload.get("body", {}).get("attachmentId", "")
                }
                attachments.append(attachment_info)
            
            # 하위 파트 확인
            if "parts" in payload:
                for part in payload["parts"]:
                    self._extract_attachments_recursive(part, attachments)
                    
        except Exception as e:
            logger.error(f"첨부 파일 추출 중 오류 발생: {str(e)}")
    
    def _decode_base64(self, data: str) -> str:
        """
        Base64 데이터 디코딩
        
        Args:
            data: Base64 인코딩된 데이터
            
        Returns:
            디코딩된 텍스트
        """
        try:
            # URL-safe Base64 디코딩
            decoded_bytes = base64.urlsafe_b64decode(data + "===")
            
            # 문자 인코딩 감지 및 디코딩
            try:
                return decoded_bytes.decode("utf-8")
            except UnicodeDecodeError:
                # 다른 인코딩 시도
                for encoding in ["cp949", "euc-kr", "latin-1"]:
                    try:
                        return decoded_bytes.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                # 모든 인코딩 실패 시 오류 무시하고 디코딩
                return decoded_bytes.decode("utf-8", errors="ignore")
                
        except Exception as e:
            logger.error(f"Base64 디코딩 중 오류 발생: {str(e)}")
            return ""
    
    def _clean_email_text(self, text: str, remove_signatures: bool = True, 
                         remove_quotes: bool = True) -> str:
        """
        이메일 본문 텍스트 정제
        
        Args:
            text: 원본 텍스트
            remove_signatures: 서명 제거 여부 (기본값: True)
            remove_quotes: 인용문 제거 여부 (기본값: True)
            
        Returns:
            정제된 텍스트
        """
        try:
            if not text:
                return ""
            
            # HTML 태그 제거
            text = re.sub(r"<[^>]+>", "", text)
            
            # HTML 엔티티 디코딩
            text = html.unescape(text)
            
            # 특수 문자 정제
            text = self._clean_special_characters(text)
            
            # 과도한 공백 및 줄바꿈 정리
            text = re.sub(r"\n\s*\n", "\n\n", text)  # 연속된 빈 줄을 두 줄로 제한
            text = re.sub(r"[ \t]+", " ", text)  # 연속된 공백을 하나로
            text = re.sub(r"\n ", "\n", text)  # 줄 시작의 공백 제거
            
            # 앞뒤 공백 제거
            text = text.strip()
            
            # 이메일 서명 및 인용문 제거 (선택적)
            if remove_signatures:
                text = self._remove_email_signatures(text)
            if remove_quotes:
                text = self._remove_quoted_text(text)
            
            # 최종 정리
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"이메일 텍스트 정제 중 오류 발생: {str(e)}")
            return text if text else ""
    
    def _process_html_content(self, html_content: str) -> Dict[str, Any]:
        """
        HTML 내용 처리
        
        Args:
            html_content: HTML 내용
            
        Returns:
            처리된 HTML 정보
        """
        try:
            if not html_content:
                return {
                    "text": "", 
                    "links": [], 
                    "images": [], 
                    "tables": [],
                    "structured_content": {},
                    "raw_html": ""
                }
            
            # HTML에서 텍스트 추출 (개선된 방식)
            text_content = self._extract_text_from_html(html_content)
            
            # 링크 추출 (개선된 방식)
            links = self._extract_links_from_html(html_content)
            
            # 이미지 추출 (개선된 방식)
            images = self._extract_images_from_html(html_content)
            
            # 테이블 추출
            tables = self._extract_tables_from_html(html_content)
            
            # 구조화된 내용 추출 (제목, 목록 등)
            structured_content = self._extract_structured_content(html_content)
            
            return {
                "text": text_content,
                "links": links,
                "images": images,
                "tables": tables,
                "structured_content": structured_content,
                "raw_html": html_content
            }
            
        except Exception as e:
            logger.error(f"HTML 내용 처리 중 오류 발생: {str(e)}")
            return {
                "text": "", 
                "links": [], 
                "images": [], 
                "tables": [],
                "structured_content": {},
                "raw_html": html_content if html_content else ""
            }
    
    def _parse_recipients(self, to: str, cc: str, bcc: str) -> List[str]:
        """
        수신자 목록 파싱
        
        Args:
            to: To 필드
            cc: CC 필드
            bcc: BCC 필드
            
        Returns:
            수신자 이메일 주소 목록
        """
        try:
            recipients = []
            
            # 각 필드에서 이메일 주소 추출
            for field in [to, cc, bcc]:
                if field:
                    # 이메일 주소 패턴 매칭
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', field)
                    recipients.extend(emails)
            
            # 중복 제거
            return list(set(recipients))
            
        except Exception as e:
            logger.error(f"수신자 목록 파싱 중 오류 발생: {str(e)}")
            return []
    
    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """
        이메일 날짜 파싱
        
        Args:
            date_str: 날짜 문자열
            
        Returns:
            파싱된 datetime 객체
        """
        try:
            if not date_str:
                return None
            
            # 이메일 날짜 형식 파싱 시도
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
            
        except Exception as e:
            logger.error(f"이메일 날짜 파싱 중 오류 발생: {str(e)}")
            return None
    
    def _remove_email_signatures(self, text: str) -> str:
        """
        이메일 서명 제거
        
        Args:
            text: 원본 텍스트
            
        Returns:
            서명이 제거된 텍스트
        """
        try:
            # 일반적인 서명 패턴 제거
            patterns = [
                r"--\s*\n.*$",  # -- 로 시작하는 서명
                r"Best regards.*$",  # Best regards로 시작하는 서명
                r"Sincerely.*$",  # Sincerely로 시작하는 서명
                r"감사합니다.*$",  # 한국어 서명
                r"안녕히.*$"  # 한국어 인사
            ]
            
            for pattern in patterns:
                text = re.sub(pattern, "", text, flags=re.MULTILINE | re.DOTALL)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"이메일 서명 제거 중 오류 발생: {str(e)}")
            return text
    
    def _remove_quoted_text(self, text: str) -> str:
        """
        인용문 제거
        
        Args:
            text: 원본 텍스트
            
        Returns:
            인용문이 제거된 텍스트
        """
        try:
            # 일반적인 인용문 패턴 제거
            patterns = [
                r"^>.*$",  # > 로 시작하는 인용문
                r"On .* wrote:.*$",  # "On ... wrote:" 패턴
                r".*님이 작성:.*$",  # 한국어 인용문 패턴
                r"-----Original Message-----.*$"  # 원본 메시지 구분선
            ]
            
            lines = text.split("\n")
            filtered_lines = []
            
            for line in lines:
                is_quoted = False
                for pattern in patterns:
                    if re.match(pattern, line.strip(), re.MULTILINE | re.DOTALL):
                        is_quoted = True
                        break
                
                if not is_quoted:
                    filtered_lines.append(line)
            
            return "\n".join(filtered_lines).strip()
            
        except Exception as e:
            logger.error(f"인용문 제거 중 오류 발생: {str(e)}")
            return text
    
    def _clean_special_characters(self, text: str) -> str:
        """
        특수 문자 정제
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정제된 텍스트
        """
        try:
            # 제어 문자 제거 (탭과 줄바꿈 제외)
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # 특수 유니코드 문자 정리
            text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)  # 제로 폭 문자
            text = re.sub(r'[\u2028\u2029]', '\n', text)  # 줄 구분자를 일반 줄바꿈으로
            
            # 이메일에서 자주 나타나는 특수 문자 정리
            text = text.replace('\r\n', '\n')  # Windows 줄바꿈을 Unix 스타일로
            text = text.replace('\r', '\n')  # Mac 스타일 줄바꿈을 Unix 스타일로
            
            return text
            
        except Exception as e:
            logger.error(f"특수 문자 정제 중 오류 발생: {str(e)}")
            return text
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """
        HTML에서 텍스트 추출 (개선된 방식)
        
        Args:
            html_content: HTML 내용
            
        Returns:
            추출된 텍스트
        """
        try:
            # 스크립트와 스타일 태그 제거
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # 블록 레벨 요소들을 줄바꿈으로 변환
            block_elements = ['div', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr']
            for element in block_elements:
                html_content = re.sub(f'<{element}[^>]*>', '\n', html_content, flags=re.IGNORECASE)
                html_content = re.sub(f'</{element}>', '\n', html_content, flags=re.IGNORECASE)
            
            # 나머지 HTML 태그 제거
            text_content = re.sub(r'<[^>]+>', '', html_content)
            
            # HTML 엔티티 디코딩
            text_content = html.unescape(text_content)
            
            # 텍스트 정제
            text_content = self._clean_special_characters(text_content)
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)  # 연속된 빈 줄 정리
            text_content = re.sub(r'[ \t]+', ' ', text_content)  # 연속된 공백 정리
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"HTML 텍스트 추출 중 오류 발생: {str(e)}")
            return ""
    
    def _extract_links_from_html(self, html_content: str) -> List[Dict[str, str]]:
        """
        HTML에서 링크 추출 (개선된 방식)
        
        Args:
            html_content: HTML 내용
            
        Returns:
            링크 정보 목록
        """
        try:
            links = []
            
            # <a> 태그에서 링크 추출
            link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
            matches = re.findall(link_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for url, text in matches:
                # 링크 텍스트에서 HTML 태그 제거
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                
                links.append({
                    "url": url,
                    "text": clean_text,
                    "type": "link"
                })
            
            # 이메일 주소 추출
            email_pattern = r'mailto:([^"\'>\s]+)'
            email_matches = re.findall(email_pattern, html_content, re.IGNORECASE)
            
            for email_addr in email_matches:
                links.append({
                    "url": f"mailto:{email_addr}",
                    "text": email_addr,
                    "type": "email"
                })
            
            return links
            
        except Exception as e:
            logger.error(f"HTML 링크 추출 중 오류 발생: {str(e)}")
            return []
    
    def _extract_images_from_html(self, html_content: str) -> List[Dict[str, str]]:
        """
        HTML에서 이미지 추출 (개선된 방식)
        
        Args:
            html_content: HTML 내용
            
        Returns:
            이미지 정보 목록
        """
        try:
            images = []
            
            # <img> 태그에서 이미지 추출
            img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
            matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            for match in matches:
                src = match[0] if len(match) > 0 else ""
                alt = match[1] if len(match) > 1 else ""
                
                images.append({
                    "src": src,
                    "alt": alt,
                    "type": "image"
                })
            
            return images
            
        except Exception as e:
            logger.error(f"HTML 이미지 추출 중 오류 발생: {str(e)}")
            return []
    
    def _extract_tables_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        HTML에서 테이블 추출
        
        Args:
            html_content: HTML 내용
            
        Returns:
            테이블 정보 목록
        """
        try:
            tables = []
            
            # <table> 태그 찾기
            table_pattern = r'<table[^>]*>(.*?)</table>'
            table_matches = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for table_content in table_matches:
                # 행 추출
                row_pattern = r'<tr[^>]*>(.*?)</tr>'
                rows = re.findall(row_pattern, table_content, re.DOTALL | re.IGNORECASE)
                
                table_data = []
                for row in rows:
                    # 셀 추출
                    cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
                    cells = re.findall(cell_pattern, row, re.DOTALL | re.IGNORECASE)
                    
                    # 셀 텍스트 정제
                    clean_cells = []
                    for cell in cells:
                        clean_cell = re.sub(r'<[^>]+>', '', cell).strip()
                        clean_cell = html.unescape(clean_cell)
                        clean_cells.append(clean_cell)
                    
                    if clean_cells:
                        table_data.append(clean_cells)
                
                if table_data:
                    tables.append({
                        "rows": table_data,
                        "row_count": len(table_data),
                        "col_count": len(table_data[0]) if table_data else 0
                    })
            
            return tables
            
        except Exception as e:
            logger.error(f"HTML 테이블 추출 중 오류 발생: {str(e)}")
            return []
    
    def _extract_structured_content(self, html_content: str) -> Dict[str, Any]:
        """
        HTML에서 구조화된 내용 추출 (제목, 목록 등)
        
        Args:
            html_content: HTML 내용
            
        Returns:
            구조화된 내용 정보
        """
        try:
            structured = {
                "headings": [],
                "lists": [],
                "paragraphs": []
            }
            
            # 제목 추출
            heading_pattern = r'<h([1-6])[^>]*>(.*?)</h[1-6]>'
            headings = re.findall(heading_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for level, text in headings:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                clean_text = html.unescape(clean_text)
                structured["headings"].append({
                    "level": int(level),
                    "text": clean_text
                })
            
            # 목록 추출
            list_pattern = r'<(ul|ol)[^>]*>(.*?)</\1>'
            lists = re.findall(list_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for list_type, list_content in lists:
                # 목록 항목 추출
                item_pattern = r'<li[^>]*>(.*?)</li>'
                items = re.findall(item_pattern, list_content, re.DOTALL | re.IGNORECASE)
                
                clean_items = []
                for item in items:
                    clean_item = re.sub(r'<[^>]+>', '', item).strip()
                    clean_item = html.unescape(clean_item)
                    clean_items.append(clean_item)
                
                structured["lists"].append({
                    "type": list_type,
                    "items": clean_items
                })
            
            # 단락 추출
            paragraph_pattern = r'<p[^>]*>(.*?)</p>'
            paragraphs = re.findall(paragraph_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for paragraph in paragraphs:
                clean_paragraph = re.sub(r'<[^>]+>', '', paragraph).strip()
                clean_paragraph = html.unescape(clean_paragraph)
                if clean_paragraph:  # 빈 단락 제외
                    structured["paragraphs"].append(clean_paragraph)
            
            return structured
            
        except Exception as e:
            logger.error(f"구조화된 내용 추출 중 오류 발생: {str(e)}")
            return {"headings": [], "lists": [], "paragraphs": []}
    
    def get_email_statistics(self, email_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        이메일 통계 생성
        
        Args:
            email_content: 이메일 내용
            
        Returns:
            이메일 통계 정보
        """
        try:
            text = email_content.get("cleaned_text", "")
            attachments = email_content.get("attachments", [])
            html_content = email_content.get("html_content", {})
            
            # 기본 통계
            word_count = len(text.split()) if text else 0
            line_count = len(text.split('\n')) if text else 0
            char_count = len(text) if text else 0
            
            # 첨부 파일 통계
            attachment_count = len(attachments)
            
            # HTML 관련 통계
            link_count = len(html_content.get("links", []))
            image_count = len(html_content.get("images", []))
            has_html = bool(html_content.get("raw_html", ""))
            
            # 언어 감지
            languages_detected = self._detect_languages(text) if text else []
            
            return {
                "word_count": word_count,
                "line_count": line_count,
                "char_count": char_count,
                "attachment_count": attachment_count,
                "link_count": link_count,
                "image_count": image_count,
                "has_html": has_html,
                "languages_detected": languages_detected
            }
            
        except Exception as e:
            logger.error(f"이메일 통계 생성 중 오류 발생: {str(e)}")
            return {}
    
    def _detect_languages(self, text: str) -> List[str]:
        """
        텍스트에서 언어 감지
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감지된 언어 목록
        """
        try:
            if not text:
                return []
            
            languages = []
            
            # 한국어 문자 패턴 확인
            korean_pattern = re.compile(r'[가-힣]')
            if korean_pattern.search(text):
                languages.append("ko")
            
            # 영어 문자 패턴 확인
            english_pattern = re.compile(r'[a-zA-Z]')
            if english_pattern.search(text):
                languages.append("en")
            
            # 일본어 문자 패턴 확인
            japanese_pattern = re.compile(r'[ひらがなカタカナ]')
            if japanese_pattern.search(text):
                languages.append("ja")
            
            # 중국어 문자 패턴 확인
            chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
            if chinese_pattern.search(text):
                languages.append("zh")
            
            return languages
            
        except Exception as e:
            logger.error(f"언어 감지 중 오류 발생: {str(e)}")
            return []
    
    def extract_email_entities(self, email_content: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        이메일에서 엔티티 추출 (이메일 주소, 전화번호, URL, 날짜, 시간 등)
        
        Args:
            email_content: 이메일 내용
            
        Returns:
            추출된 엔티티 정보
        """
        try:
            text = email_content.get("cleaned_text", "")
            if not text:
                return {
                    "email_addresses": [],
                    "phone_numbers": [],
                    "urls": [],
                    "dates": [],
                    "times": []
                }
            
            entities = {
                "email_addresses": [],
                "phone_numbers": [],
                "urls": [],
                "dates": [],
                "times": []
            }
            
            # 이메일 주소 추출
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            entities["email_addresses"] = re.findall(email_pattern, text)
            
            # 전화번호 추출 (한국 형식)
            phone_patterns = [
                r'\b010-\d{4}-\d{4}\b',  # 010-1234-5678
                r'\b\d{3}-\d{4}-\d{4}\b',  # 02-1234-5678
                r'\b\d{2}-\d{3,4}-\d{4}\b'  # 031-123-4567
            ]
            for pattern in phone_patterns:
                entities["phone_numbers"].extend(re.findall(pattern, text))
            
            # URL 추출
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            entities["urls"] = re.findall(url_pattern, text)
            
            # 날짜 추출 (한국어 형식)
            date_patterns = [
                r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',  # 2023년 12월 25일
                r'\d{1,2}/\d{1,2}/\d{4}',  # 12/25/2023
                r'\d{4}-\d{1,2}-\d{1,2}'  # 2023-12-25
            ]
            for pattern in date_patterns:
                entities["dates"].extend(re.findall(pattern, text))
            
            # 시간 추출 (한국어 형식)
            time_patterns = [
                r'오전\s*\d{1,2}:\d{2}',  # 오전 9:30
                r'오후\s*\d{1,2}:\d{2}',  # 오후 2:30
                r'\d{1,2}:\d{2}',  # 14:30
                r'\d{1,2}시\s*\d{1,2}분'  # 2시 30분
            ]
            for pattern in time_patterns:
                entities["times"].extend(re.findall(pattern, text))
            
            # 중복 제거
            for key in entities:
                entities[key] = list(set(entities[key]))
            
            return entities
            
        except Exception as e:
            logger.error(f"이메일 엔티티 추출 중 오류 발생: {str(e)}")
            return {
                "email_addresses": [],
                "phone_numbers": [],
                "urls": [],
                "dates": [],
                "times": []
            }
    
    def get_attachment_content(self, email_id: str, attachment_id: str) -> Optional[bytes]:
        """
        첨부 파일 내용 가져오기
        
        Args:
            email_id: 이메일 ID
            attachment_id: 첨부 파일 ID
            
        Returns:
            첨부 파일 내용 (바이트)
        """
        try:
            service = self._get_service()
            
            # 첨부 파일 가져오기
            attachment = service.users().messages().attachments().get(
                userId="me",
                messageId=email_id,
                id=attachment_id
            ).execute()
            
            # Base64 디코딩
            data = attachment.get("data", "")
            if data:
                return base64.urlsafe_b64decode(data)
            
            return None
            
        except HttpError as error:
            logger.error(f"첨부 파일 내용 가져오기 중 오류 발생: {str(error)}")
            return None
    
    def save_attachment(self, email_id: str, attachment_id: str, filename: str, save_path: str) -> bool:
        """
        첨부 파일 저장
        
        Args:
            email_id: 이메일 ID
            attachment_id: 첨부 파일 ID
            filename: 파일명
            save_path: 저장 경로
            
        Returns:
            성공 여부
        """
        try:
            # 첨부 파일 내용 가져오기
            content = self.get_attachment_content(email_id, attachment_id)
            if not content:
                return False
            
            # 저장 디렉토리 생성
            os.makedirs(save_path, exist_ok=True)
            
            # 파일 저장
            file_path = os.path.join(save_path, filename)
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"첨부 파일 저장 완료: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"첨부 파일 저장 중 오류 발생: {str(e)}")
            return False
    
    def forward_email(self, email_id: str, recipients: List[str], message: Optional[str] = None) -> bool:
        """
        이메일 전달
        
        Args:
            email_id: 원본 이메일 ID
            recipients: 수신자 목록
            message: 전달 메시지 (선택 사항)
            
        Returns:
            성공 여부
        """
        try:
            service = self._get_service()
            
            # 원본 이메일 정보 가져오기
            original_message = service.users().messages().get(
                userId="me", id=email_id).execute()
            
            # 원본 이메일 헤더 파싱
            headers = {}
            for header in original_message["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
            
            # 전달 이메일 구성
            forward_subject = f"Fwd: {headers.get('subject', '')}"
            
            # MIME 메시지 생성
            mime_message = MIMEMultipart()
            mime_message["To"] = ", ".join(recipients)
            mime_message["Subject"] = forward_subject
            
            # 전달 메시지 추가
            if message:
                mime_message.attach(MIMEText(message, "plain", "utf-8"))
            
            # 원본 메시지 내용 추가
            original_content = self.get_email_content(email_id)
            if original_content:
                original_text = f"\n\n---------- Forwarded message ----------\n"
                original_text += f"From: {headers.get('from', '')}\n"
                original_text += f"Date: {headers.get('date', '')}\n"
                original_text += f"Subject: {headers.get('subject', '')}\n"
                original_text += f"To: {headers.get('to', '')}\n\n"
                original_text += original_content.get("body", "")
                
                mime_message.attach(MIMEText(original_text, "plain", "utf-8"))
            
            # 메시지 인코딩
            raw_message = base64.urlsafe_b64encode(
                mime_message.as_bytes()).decode("utf-8")
            
            # 전달 전송
            send_result = service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()
            
            logger.info(f"이메일 전달 완료: {email_id} -> {send_result.get('id')}")
            return True
            
        except HttpError as error:
            logger.error(f"이메일 전달 중 오류 발생 ({email_id}): {str(error)}")
            return False