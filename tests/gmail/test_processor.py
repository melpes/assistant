"""
이메일 처리기 테스트 모듈

이 모듈은 EmailProcessor 클래스의 기능을 테스트합니다.
"""

import pytest
import base64
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.gmail.processor import EmailProcessor
from src.gmail.service import GmailServiceManager


class TestEmailProcessor:
    """EmailProcessor 클래스 테스트"""
    
    @pytest.fixture
    def mock_gmail_service_manager(self):
        """Gmail 서비스 관리자 모의 객체"""
        mock_manager = Mock(spec=GmailServiceManager)
        mock_service = Mock()
        mock_manager._get_service.return_value = mock_service
        return mock_manager
    
    @pytest.fixture
    def email_processor(self, mock_gmail_service_manager):
        """EmailProcessor 인스턴스"""
        return EmailProcessor(mock_gmail_service_manager)
    
    @pytest.fixture
    def sample_email_message(self):
        """샘플 이메일 메시지"""
        return {
            "id": "test_email_id",
            "threadId": "test_thread_id",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "테스트 이메일입니다",
            "sizeEstimate": 1024,
            "internalDate": "1640995200000",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "테스트 제목"},
                    {"name": "Date", "value": "Sat, 1 Jan 2022 00:00:00 +0000"},
                    {"name": "Message-ID", "value": "<test@example.com>"}
                ],
                "body": {
                    "data": base64.urlsafe_b64encode("테스트 이메일 내용입니다.".encode()).decode()
                }
            }
        }
    
    @pytest.fixture
    def multipart_email_message(self):
        """멀티파트 이메일 메시지"""
        return {
            "id": "multipart_email_id",
            "threadId": "multipart_thread_id",
            "labelIds": ["INBOX"],
            "snippet": "멀티파트 이메일",
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "멀티파트 테스트"}
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.urlsafe_b64encode("텍스트 내용".encode()).decode()
                        }
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": base64.urlsafe_b64encode("<p>HTML 내용</p>".encode()).decode()
                        }
                    },
                    {
                        "mimeType": "application/pdf",
                        "filename": "test.pdf",
                        "body": {
                            "attachmentId": "attachment_123",
                            "size": 2048
                        }
                    }
                ]
            }
        }
    
    def test_init(self, mock_gmail_service_manager):
        """EmailProcessor 초기화 테스트"""
        processor = EmailProcessor(mock_gmail_service_manager)
        
        assert processor.gmail_service_manager == mock_gmail_service_manager
        assert processor._service is None
    
    def test_get_email_content_success(self, email_processor, sample_email_message):
        """이메일 내용 가져오기 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.return_value = sample_email_message
        
        # 테스트 실행
        result = email_processor.get_email_content("test_email_id")
        
        # 검증
        assert result is not None
        assert result["raw_message"] == sample_email_message
        assert "테스트 이메일 내용입니다." in result["body"]
        
        # API 호출 검증
        mock_service.users().messages().get.assert_called_once_with(
            userId="me", id="test_email_id", format="full"
        )
    
    def test_get_email_content_http_error(self, email_processor):
        """이메일 내용 가져오기 HTTP 오류 테스트"""
        from googleapiclient.errors import HttpError
        
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.side_effect = HttpError(
            resp=Mock(status=404), content=b"Not found"
        )
        
        # 테스트 실행
        result = email_processor.get_email_content("nonexistent_id")
        
        # 검증
        assert result is None
    
    def test_extract_email_metadata(self, email_processor, sample_email_message):
        """이메일 메타데이터 추출 테스트"""
        email_content = {"raw_message": sample_email_message}
        
        # 테스트 실행
        metadata = email_processor.extract_email_metadata(email_content)
        
        # 검증
        assert metadata["id"] == "test_email_id"
        assert metadata["thread_id"] == "test_thread_id"
        assert metadata["subject"] == "테스트 제목"
        assert metadata["from"] == "sender@example.com"
        assert metadata["to"] == "recipient@example.com"
        assert "recipient@example.com" in metadata["recipients"]
        assert metadata["parsed_date"] is not None
    
    def test_extract_attachments_no_attachments(self, email_processor, sample_email_message):
        """첨부 파일 없는 이메일 테스트"""
        email_content = {"raw_message": sample_email_message}
        
        # 테스트 실행
        attachments = email_processor.extract_attachments(email_content)
        
        # 검증
        assert attachments == []
    
    def test_extract_attachments_with_attachments(self, email_processor, multipart_email_message):
        """첨부 파일 있는 이메일 테스트"""
        email_content = {"raw_message": multipart_email_message}
        
        # 테스트 실행
        attachments = email_processor.extract_attachments(email_content)
        
        # 검증
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "test.pdf"
        assert attachments[0]["mime_type"] == "application/pdf"
        assert attachments[0]["attachment_id"] == "attachment_123"
        assert attachments[0]["size"] == 2048
    
    def test_process_email_success(self, email_processor, sample_email_message):
        """이메일 처리 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.return_value = sample_email_message
        
        # 테스트 실행
        result = email_processor.process_email("test_email_id")
        
        # 검증
        assert result is not None
        assert result["id"] == "test_email_id"
        assert "metadata" in result
        assert "cleaned_text" in result
        assert "html_content" in result
        assert "attachments" in result
        assert "processed_at" in result
        
        # 메타데이터 검증
        assert result["metadata"]["subject"] == "테스트 제목"
        
        # 정제된 텍스트 검증
        assert "테스트 이메일 내용입니다." in result["cleaned_text"]
    
    def test_process_emails_batch(self, email_processor, sample_email_message):
        """이메일 일괄 처리 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.return_value = sample_email_message
        
        email_ids = ["email1", "email2", "email3"]
        
        # 테스트 실행
        results = email_processor.process_emails(email_ids)
        
        # 검증
        assert len(results) == 3
        for result in results:
            assert result["metadata"]["subject"] == "테스트 제목"
        
        # API 호출 횟수 검증
        assert mock_service.users().messages().get.call_count == 3
    
    def test_mark_as_read_success(self, email_processor):
        """이메일 읽음 표시 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().modify().execute.return_value = {}
        
        # 테스트 실행
        result = email_processor.mark_as_read("test_email_id")
        
        # 검증
        assert result is True
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me",
            id="test_email_id",
            body={"removeLabelIds": ["UNREAD"]}
        )
    
    def test_mark_as_unread_success(self, email_processor):
        """이메일 읽지 않음 표시 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().modify().execute.return_value = {}
        
        # 테스트 실행
        result = email_processor.mark_as_unread("test_email_id")
        
        # 검증
        assert result is True
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me",
            id="test_email_id",
            body={"addLabelIds": ["UNREAD"]}
        )
    
    def test_reply_to_email_success(self, email_processor, sample_email_message):
        """이메일 답장 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.return_value = sample_email_message
        mock_service.users().messages().send().execute.return_value = {"id": "reply_id"}
        
        # 테스트 실행
        result = email_processor.reply_to_email("test_email_id", "답장 내용입니다.")
        
        # 검증
        assert result is True
        mock_service.users().messages().send.assert_called_once()
        
        # 전송된 메시지 검증
        call_args = mock_service.users().messages().send.call_args
        assert call_args[1]["userId"] == "me"
        assert "raw" in call_args[1]["body"]
        assert "threadId" in call_args[1]["body"]
    
    def test_forward_email_success(self, email_processor, sample_email_message):
        """이메일 전달 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.return_value = sample_email_message
        mock_service.users().messages().send().execute.return_value = {"id": "forward_id"}
        
        # 테스트 실행
        result = email_processor.forward_email(
            "test_email_id", 
            ["forward@example.com"], 
            "전달 메시지입니다."
        )
        
        # 검증
        assert result is True
        mock_service.users().messages().send.assert_called_once()
    
    def test_clean_email_text(self, email_processor):
        """이메일 텍스트 정제 테스트"""
        # HTML 태그가 포함된 텍스트
        html_text = "<p>안녕하세요</p><br><strong>중요한 내용</strong>"
        
        # 테스트 실행
        cleaned = email_processor._clean_email_text(html_text)
        
        # 검증
        assert "<p>" not in cleaned
        assert "<br>" not in cleaned
        assert "<strong>" not in cleaned
        assert "안녕하세요" in cleaned
        assert "중요한 내용" in cleaned
    
    def test_process_html_content(self, email_processor):
        """HTML 내용 처리 테스트"""
        html_content = '''
        <html>
            <body>
                <p>안녕하세요</p>
                <a href="https://example.com">링크</a>
                <img src="image.jpg" alt="이미지">
            </body>
        </html>
        '''
        
        # 테스트 실행
        result = email_processor._process_html_content(html_content)
        
        # 검증
        assert "안녕하세요" in result["text"]
        assert "링크" in result["text"]
        assert "https://example.com" in result["links"]
        assert "image.jpg" in result["images"]
        assert result["raw_html"] == html_content
    
    def test_parse_recipients(self, email_processor):
        """수신자 목록 파싱 테스트"""
        to = "user1@example.com, User Two <user2@example.com>"
        cc = "user3@example.com"
        bcc = "user4@example.com"
        
        # 테스트 실행
        recipients = email_processor._parse_recipients(to, cc, bcc)
        
        # 검증
        assert "user1@example.com" in recipients
        assert "user2@example.com" in recipients
        assert "user3@example.com" in recipients
        assert "user4@example.com" in recipients
        assert len(recipients) == 4
    
    def test_decode_base64(self, email_processor):
        """Base64 디코딩 테스트"""
        # UTF-8 텍스트 인코딩
        original_text = "안녕하세요 테스트입니다"
        encoded_data = base64.urlsafe_b64encode(original_text.encode()).decode()
        
        # 테스트 실행
        decoded = email_processor._decode_base64(encoded_data)
        
        # 검증
        assert decoded == original_text
    
    def test_remove_email_signatures(self, email_processor):
        """이메일 서명 제거 테스트"""
        text_with_signature = """
        이메일 내용입니다.
        
        감사합니다.
        홍길동
        """
        
        # 테스트 실행
        cleaned = email_processor._remove_email_signatures(text_with_signature)
        
        # 검증
        assert "이메일 내용입니다." in cleaned
        assert "감사합니다." not in cleaned
        assert "홍길동" not in cleaned
    
    def test_remove_quoted_text(self, email_processor):
        """인용문 제거 테스트"""
        text_with_quotes = """
        새로운 내용입니다.
        
        > 이전 이메일 내용
        > 인용된 텍스트
        """
        
        # 테스트 실행
        cleaned = email_processor._remove_quoted_text(text_with_quotes)
        
        # 검증
        assert "새로운 내용입니다." in cleaned
        assert "> 이전 이메일 내용" not in cleaned
        assert "> 인용된 텍스트" not in cleaned
    
    def test_parse_email_date(self, email_processor):
        """이메일 날짜 파싱 테스트"""
        date_str = "Sat, 1 Jan 2022 12:00:00 +0900"
        
        # 테스트 실행
        parsed_date = email_processor._parse_email_date(date_str)
        
        # 검증
        assert parsed_date is not None
        assert isinstance(parsed_date, datetime)
        assert parsed_date.year == 2022
        assert parsed_date.month == 1
        assert parsed_date.day == 1
    
    def test_parse_email_message_multipart(self, email_processor, multipart_email_message):
        """멀티파트 이메일 메시지 파싱 테스트"""
        # 테스트 실행
        result = email_processor._parse_email_message(multipart_email_message)
        
        # 검증
        assert result["raw_message"] == multipart_email_message
        assert "텍스트 내용" in result["body"]
        assert "<p>HTML 내용</p>" in result["html_body"]
    
    def test_extract_email_body_single_part(self, email_processor):
        """단일 파트 이메일 본문 추출 테스트"""
        payload = {
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode("테스트 내용".encode()).decode()
            }
        }
        email_content = {"body": "", "html_body": ""}
        
        # 테스트 실행
        email_processor._extract_email_body(payload, email_content)
        
        # 검증
        assert "테스트 내용" in email_content["body"]
    
    def test_get_service_caching(self, email_processor):
        """서비스 객체 캐싱 테스트"""
        # 첫 번째 호출
        service1 = email_processor._get_service()
        
        # 두 번째 호출
        service2 = email_processor._get_service()
        
        # 검증 - 같은 객체여야 함
        assert service1 is service2
        
        # Gmail 서비스 관리자의 _get_service가 한 번만 호출되어야 함
        email_processor.gmail_service_manager._get_service.assert_called_once()
    
    def test_process_emails_batch_processing(self, email_processor, sample_email_message):
        """이메일 배치 처리 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        mock_service.users().messages().get().execute.return_value = sample_email_message
        
        email_ids = ["email1", "email2", "email3", "email4", "email5"]
        
        # 테스트 실행 (배치 크기 2)
        results = email_processor.process_emails(email_ids, batch_size=2)
        
        # 검증
        assert len(results) == 5
        for result in results:
            assert result["metadata"]["subject"] == "테스트 제목"
    
    def test_clean_special_characters(self, email_processor):
        """특수 문자 정제 테스트"""
        text_with_special = "안녕하세요\x00\x08\u200B테스트\r\n입니다\u2028"
        
        # 테스트 실행
        cleaned = email_processor._clean_special_characters(text_with_special)
        
        # 검증
        assert "\x00" not in cleaned
        assert "\x08" not in cleaned
        assert "\u200B" not in cleaned
        assert "\r\n" not in cleaned
        assert "안녕하세요" in cleaned
        assert "테스트" in cleaned
        assert "입니다" in cleaned
    
    def test_extract_text_from_html(self, email_processor):
        """HTML 텍스트 추출 개선 테스트"""
        html_content = """
        <html>
            <head><title>제목</title></head>
            <body>
                <script>alert('test');</script>
                <style>body { color: red; }</style>
                <h1>제목</h1>
                <p>첫 번째 단락</p>
                <div>두 번째 단락</div>
                <br>
                <ul>
                    <li>항목 1</li>
                    <li>항목 2</li>
                </ul>
            </body>
        </html>
        """
        
        # 테스트 실행
        text = email_processor._extract_text_from_html(html_content)
        
        # 검증
        assert "alert('test');" not in text  # 스크립트 제거
        assert "color: red;" not in text  # 스타일 제거
        assert "제목" in text
        assert "첫 번째 단락" in text
        assert "두 번째 단락" in text
        assert "항목 1" in text
        assert "항목 2" in text
    
    def test_extract_links_from_html(self, email_processor):
        """HTML 링크 추출 개선 테스트"""
        html_content = '''
        <a href="https://example.com">예제 사이트</a>
        <a href="mailto:test@example.com">이메일 보내기</a>
        <a href="tel:010-1234-5678">전화걸기</a>
        '''
        
        # 테스트 실행
        links = email_processor._extract_links_from_html(html_content)
        
        # 검증
        assert len(links) >= 2
        
        # 일반 링크 확인
        web_links = [link for link in links if link["type"] == "link"]
        assert any("https://example.com" in link["url"] for link in web_links)
        assert any("예제 사이트" in link["text"] for link in web_links)
        
        # 이메일 링크 확인
        email_links = [link for link in links if link["type"] == "email"]
        assert any("test@example.com" in link["url"] for link in email_links)
    
    def test_extract_images_from_html(self, email_processor):
        """HTML 이미지 추출 개선 테스트"""
        html_content = '''
        <img src="image1.jpg" alt="첫 번째 이미지">
        <img src="https://example.com/image2.png" alt="두 번째 이미지">
        <img src="image3.gif">
        '''
        
        # 테스트 실행
        images = email_processor._extract_images_from_html(html_content)
        
        # 검증
        assert len(images) == 3
        assert any("image1.jpg" in img["src"] for img in images)
        assert any("image2.png" in img["src"] for img in images)
        assert any("image3.gif" in img["src"] for img in images)
        assert any("첫 번째 이미지" in img["alt"] for img in images)
    
    def test_extract_tables_from_html(self, email_processor):
        """HTML 테이블 추출 테스트"""
        html_content = '''
        <table>
            <tr>
                <th>이름</th>
                <th>나이</th>
            </tr>
            <tr>
                <td>홍길동</td>
                <td>30</td>
            </tr>
            <tr>
                <td>김철수</td>
                <td>25</td>
            </tr>
        </table>
        '''
        
        # 테스트 실행
        tables = email_processor._extract_tables_from_html(html_content)
        
        # 검증
        assert len(tables) == 1
        table = tables[0]
        assert table["row_count"] == 3
        assert table["col_count"] == 2
        assert "이름" in table["rows"][0]
        assert "홍길동" in table["rows"][1]
        assert "김철수" in table["rows"][2]
    
    def test_extract_structured_content(self, email_processor):
        """구조화된 내용 추출 테스트"""
        html_content = '''
        <h1>주요 제목</h1>
        <h2>부제목</h2>
        <p>첫 번째 단락입니다.</p>
        <p>두 번째 단락입니다.</p>
        <ul>
            <li>순서 없는 목록 1</li>
            <li>순서 없는 목록 2</li>
        </ul>
        <ol>
            <li>순서 있는 목록 1</li>
            <li>순서 있는 목록 2</li>
        </ol>
        '''
        
        # 테스트 실행
        structured = email_processor._extract_structured_content(html_content)
        
        # 검증
        # 제목 확인
        assert len(structured["headings"]) == 2
        assert structured["headings"][0]["level"] == 1
        assert structured["headings"][0]["text"] == "주요 제목"
        assert structured["headings"][1]["level"] == 2
        assert structured["headings"][1]["text"] == "부제목"
        
        # 목록 확인
        assert len(structured["lists"]) == 2
        ul_list = next(l for l in structured["lists"] if l["type"] == "ul")
        ol_list = next(l for l in structured["lists"] if l["type"] == "ol")
        assert "순서 없는 목록 1" in ul_list["items"]
        assert "순서 있는 목록 1" in ol_list["items"]
        
        # 단락 확인
        assert len(structured["paragraphs"]) == 2
        assert "첫 번째 단락입니다." in structured["paragraphs"]
        assert "두 번째 단락입니다." in structured["paragraphs"]
    
    def test_get_email_statistics(self, email_processor):
        """이메일 통계 생성 테스트"""
        email_content = {
            "cleaned_text": "안녕하세요 테스트 이메일입니다.\n두 번째 줄입니다.",
            "attachments": [{"filename": "test.pdf"}, {"filename": "image.jpg"}],
            "html_content": {
                "raw_html": "<p>HTML 내용</p>",
                "links": [{"url": "https://example.com"}],
                "images": [{"src": "image.jpg"}]
            }
        }
        
        # 테스트 실행
        stats = email_processor.get_email_statistics(email_content)
        
        # 검증
        assert stats["word_count"] > 0
        assert stats["line_count"] == 2
        assert stats["attachment_count"] == 2
        assert stats["link_count"] == 1
        assert stats["image_count"] == 1
        assert stats["has_html"] is True
        assert "ko" in stats["languages_detected"]
    
    def test_detect_languages(self, email_processor):
        """언어 감지 테스트"""
        # 한국어 텍스트
        korean_text = "안녕하세요 반갑습니다"
        languages = email_processor._detect_languages(korean_text)
        assert "ko" in languages
        
        # 영어 텍스트
        english_text = "Hello world"
        languages = email_processor._detect_languages(english_text)
        assert "en" in languages
        
        # 혼합 텍스트
        mixed_text = "Hello 안녕하세요 world"
        languages = email_processor._detect_languages(mixed_text)
        assert "ko" in languages
        assert "en" in languages
    
    def test_extract_email_entities(self, email_processor):
        """이메일 엔티티 추출 테스트"""
        email_content = {
            "cleaned_text": """
            연락처: test@example.com
            전화번호: 010-1234-5678
            웹사이트: https://example.com
            날짜: 2023년 12월 25일
            시간: 오후 2:30
            """
        }
        
        # 테스트 실행
        entities = email_processor.extract_email_entities(email_content)
        
        # 검증
        assert "test@example.com" in entities["email_addresses"]
        assert any("010-1234-5678" in phone for phone in entities["phone_numbers"])
        assert "https://example.com" in entities["urls"]
        assert any("2023년 12월 25일" in date for date in entities["dates"])
        assert any("오후 2:30" in time for time in entities["times"])
    
    def test_get_attachment_content_success(self, email_processor):
        """첨부 파일 내용 가져오기 성공 테스트"""
        # Mock 설정
        mock_service = email_processor._get_service()
        test_content = b"test file content"
        encoded_content = base64.urlsafe_b64encode(test_content).decode()
        
        mock_service.users().messages().attachments().get().execute.return_value = {
            "data": encoded_content
        }
        
        # 테스트 실행
        result = email_processor.get_attachment_content("email_id", "attachment_id")
        
        # 검증
        assert result == test_content
        mock_service.users().messages().attachments().get.assert_called_once_with(
            userId="me",
            messageId="email_id",
            id="attachment_id"
        )
    
    @patch('os.makedirs')
    @patch('builtins.open', create=True)
    def test_save_attachment_success(self, mock_open, mock_makedirs, email_processor):
        """첨부 파일 저장 성공 테스트"""
        # Mock 설정
        test_content = b"test file content"
        email_processor.get_attachment_content = Mock(return_value=test_content)
        
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 테스트 실행
        result = email_processor.save_attachment(
            "email_id", "attachment_id", "test.txt", "/save/path"
        )
        
        # 검증
        assert result is True
        mock_makedirs.assert_called_once()
        mock_file.write.assert_called_once_with(test_content)


if __name__ == "__main__":
    pytest.main([__file__])