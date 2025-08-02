"""
Gmail 서비스 관리자 테스트
"""

import unittest
from unittest.mock import patch, MagicMock

from src.gmail.service import GmailServiceManager
from src.gmail.auth import GmailAuthService

class TestGmailServiceManager(unittest.TestCase):
    """Gmail 서비스 관리자 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 모의 인증 서비스 생성
        self.mock_auth_service = MagicMock(spec=GmailAuthService)
        self.mock_service = MagicMock()
        self.mock_auth_service.get_service.return_value = self.mock_service
        
        # Gmail 서비스 관리자 생성
        self.gmail_service = GmailServiceManager(self.mock_auth_service)
    
    def test_start_watching(self):
        """이메일 감시 시작 테스트"""
        # 이메일 감시 시작
        result = self.gmail_service.start_watching()
        
        # 검증
        self.assertTrue(result)
        self.assertTrue(self.gmail_service._watching)
        self.assertIsNotNone(self.gmail_service._last_check_time)
    
    def test_stop_watching(self):
        """이메일 감시 중지 테스트"""
        # 이메일 감시 시작
        self.gmail_service.start_watching()
        
        # 이메일 감시 중지
        result = self.gmail_service.stop_watching()
        
        # 검증
        self.assertTrue(result)
        self.assertFalse(self.gmail_service._watching)
    
    def test_check_archived_emails(self):
        """보관 처리된 이메일 확인 테스트"""
        # 모의 응답 설정
        mock_messages = [{"id": "msg1"}, {"id": "msg2"}]
        mock_list_response = {"messages": mock_messages}
        
        mock_users = MagicMock()
        mock_messages_obj = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_list_response
        
        mock_messages_obj.list.return_value = mock_list
        mock_users.messages.return_value = mock_messages_obj
        self.mock_service.users.return_value = mock_users
        
        # _get_email_details 메서드 패치
        with patch.object(self.gmail_service, "_get_email_details") as mock_get_details:
            mock_get_details.side_effect = [
                {"id": "msg1", "subject": "Test 1"},
                {"id": "msg2", "subject": "Test 2"}
            ]
            
            # 보관 처리된 이메일 확인
            emails = self.gmail_service.check_archived_emails()
            
            # 검증
            self.assertEqual(len(emails), 2)
            self.assertEqual(emails[0]["subject"], "Test 1")
            self.assertEqual(emails[1]["subject"], "Test 2")
            
            # 메서드 호출 검증
            mock_messages_obj.list.assert_called_once()
            mock_get_details.assert_any_call("msg1")
            mock_get_details.assert_any_call("msg2")
    
    def test_check_unread_emails(self):
        """읽지 않은 이메일 확인 테스트"""
        # 모의 응답 설정
        mock_messages = [{"id": "msg1"}, {"id": "msg2"}]
        mock_list_response = {"messages": mock_messages}
        
        mock_users = MagicMock()
        mock_messages_obj = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_list_response
        
        mock_messages_obj.list.return_value = mock_list
        mock_users.messages.return_value = mock_messages_obj
        self.mock_service.users.return_value = mock_users
        
        # _get_email_details 메서드 패치
        with patch.object(self.gmail_service, "_get_email_details") as mock_get_details:
            mock_get_details.side_effect = [
                {"id": "msg1", "subject": "Test 1"},
                {"id": "msg2", "subject": "Test 2"}
            ]
            
            # 읽지 않은 이메일 확인
            emails = self.gmail_service.check_unread_emails()
            
            # 검증
            self.assertEqual(len(emails), 2)
            self.assertEqual(emails[0]["subject"], "Test 1")
            self.assertEqual(emails[1]["subject"], "Test 2")
            
            # 메서드 호출 검증
            mock_messages_obj.list.assert_called_once()
            mock_get_details.assert_any_call("msg1")
            mock_get_details.assert_any_call("msg2")
    
    def test_search_emails(self):
        """이메일 검색 테스트"""
        # 모의 응답 설정
        mock_messages = [{"id": "msg1"}, {"id": "msg2"}]
        mock_list_response = {"messages": mock_messages}
        
        mock_users = MagicMock()
        mock_messages_obj = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_list_response
        
        mock_messages_obj.list.return_value = mock_list
        mock_users.messages.return_value = mock_messages_obj
        self.mock_service.users.return_value = mock_users
        
        # _get_email_details 메서드 패치
        with patch.object(self.gmail_service, "_get_email_details") as mock_get_details:
            mock_get_details.side_effect = [
                {"id": "msg1", "subject": "Test 1"},
                {"id": "msg2", "subject": "Test 2"}
            ]
            
            # 이메일 검색
            emails = self.gmail_service.search_emails("test query")
            
            # 검증
            self.assertEqual(len(emails), 2)
            self.assertEqual(emails[0]["subject"], "Test 1")
            self.assertEqual(emails[1]["subject"], "Test 2")
            
            # 메서드 호출 검증
            mock_messages_obj.list.assert_called_once_with(
                userId="me", q="test query", maxResults=10)
            mock_get_details.assert_any_call("msg1")
            mock_get_details.assert_any_call("msg2")
    
    def test_apply_label(self):
        """라벨 적용 테스트"""
        # _get_or_create_label 메서드 패치
        with patch.object(self.gmail_service, "_get_or_create_label") as mock_get_label:
            mock_get_label.return_value = "label1"
            
            # 모의 응답 설정
            mock_users = MagicMock()
            mock_messages_obj = MagicMock()
            mock_modify = MagicMock()
            
            mock_messages_obj.modify.return_value = mock_modify
            mock_users.messages.return_value = mock_messages_obj
            self.mock_service.users.return_value = mock_users
            
            # 라벨 적용
            result = self.gmail_service.apply_label(["msg1", "msg2"], "Test Label")
            
            # 검증
            self.assertTrue(result)
            
            # 메서드 호출 검증
            mock_get_label.assert_called_once_with("Test Label")
            self.assertEqual(mock_messages_obj.modify.call_count, 2)
    
    def test_archive_emails(self):
        """이메일 보관 처리 테스트"""
        # 모의 응답 설정
        mock_users = MagicMock()
        mock_messages_obj = MagicMock()
        mock_modify = MagicMock()
        
        mock_messages_obj.modify.return_value = mock_modify
        mock_users.messages.return_value = mock_messages_obj
        self.mock_service.users.return_value = mock_users
        
        # 이메일 보관 처리
        result = self.gmail_service.archive_emails(["msg1", "msg2"])
        
        # 검증
        self.assertTrue(result)
        
        # 메서드 호출 검증
        self.assertEqual(mock_messages_obj.modify.call_count, 2)
        mock_messages_obj.modify.assert_any_call(
            userId="me", id="msg1", body={"removeLabelIds": ["INBOX"]})
        mock_messages_obj.modify.assert_any_call(
            userId="me", id="msg2", body={"removeLabelIds": ["INBOX"]})
    
    def test_delete_emails(self):
        """이메일 삭제 테스트"""
        # 모의 응답 설정
        mock_users = MagicMock()
        mock_messages_obj = MagicMock()
        mock_trash = MagicMock()
        
        mock_messages_obj.trash.return_value = mock_trash
        mock_users.messages.return_value = mock_messages_obj
        self.mock_service.users.return_value = mock_users
        
        # 이메일 삭제
        result = self.gmail_service.delete_emails(["msg1", "msg2"])
        
        # 검증
        self.assertTrue(result)
        
        # 메서드 호출 검증
        self.assertEqual(mock_messages_obj.trash.call_count, 2)
        mock_messages_obj.trash.assert_any_call(userId="me", id="msg1")
        mock_messages_obj.trash.assert_any_call(userId="me", id="msg2")
    
    def test_create_filter(self):
        """필터 생성 테스트"""
        # 모의 응답 설정
        mock_users = MagicMock()
        mock_settings = MagicMock()
        mock_filters = MagicMock()
        mock_create = MagicMock()
        mock_create.execute.return_value = {"id": "filter1"}
        
        mock_filters.create.return_value = mock_create
        mock_settings.filters.return_value = mock_filters
        mock_users.settings.return_value = mock_settings
        self.mock_service.users.return_value = mock_users
        
        # 필터 생성
        filter_criteria = {"from": "test@example.com"}
        filter_id = self.gmail_service.create_filter(filter_criteria)
        
        # 검증
        self.assertEqual(filter_id, "filter1")
        
        # 메서드 호출 검증
        mock_filters.create.assert_called_once_with(
            userId="me", body={"criteria": filter_criteria})
    
    def test_get_email_details(self):
        """이메일 상세 정보 가져오기 테스트"""
        # 모의 응답 설정
        mock_users = MagicMock()
        mock_messages_obj = MagicMock()
        mock_get = MagicMock()
        
        mock_message = {
            "id": "msg1",
            "threadId": "thread1",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "This is a test email",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2023 12:00:00 +0000"}
                ]
            }
        }
        
        mock_get.execute.return_value = mock_message
        mock_messages_obj.get.return_value = mock_get
        mock_users.messages.return_value = mock_messages_obj
        self.mock_service.users.return_value = mock_users
        
        # 이메일 상세 정보 가져오기
        email_info = self.gmail_service._get_email_details("msg1")
        
        # 검증
        self.assertEqual(email_info["id"], "msg1")
        self.assertEqual(email_info["threadId"], "thread1")
        self.assertEqual(email_info["subject"], "Test Subject")
        self.assertEqual(email_info["from"], "sender@example.com")
        self.assertEqual(email_info["to"], "recipient@example.com")
        self.assertEqual(email_info["date"], "Mon, 1 Jan 2023 12:00:00 +0000")
        self.assertEqual(email_info["snippet"], "This is a test email")
        
        # 메서드 호출 검증
        mock_messages_obj.get.assert_called_once_with(userId="me", id="msg1")
    
    def test_get_or_create_label(self):
        """라벨 가져오기 또는 생성하기 테스트"""
        # 모의 응답 설정 - 기존 라벨 찾기
        mock_users = MagicMock()
        mock_labels_obj = MagicMock()
        mock_list = MagicMock()
        
        mock_list.execute.return_value = {
            "labels": [
                {"id": "label1", "name": "Test Label"},
                {"id": "label2", "name": "Another Label"}
            ]
        }
        
        mock_labels_obj.list.return_value = mock_list
        mock_users.labels.return_value = mock_labels_obj
        self.mock_service.users.return_value = mock_users
        
        # 라벨 가져오기
        label_id = self.gmail_service._get_or_create_label("Test Label")
        
        # 검증
        self.assertEqual(label_id, "label1")
        
        # 메서드 호출 검증
        mock_labels_obj.list.assert_called_once_with(userId="me")
        
        # 모의 응답 설정 - 새 라벨 생성
        mock_list.execute.return_value = {
            "labels": [
                {"id": "label2", "name": "Another Label"}
            ]
        }
        
        mock_create = MagicMock()
        mock_create.execute.return_value = {"id": "new_label", "name": "New Label"}
        mock_labels_obj.create.return_value = mock_create
        
        # 라벨 생성
        label_id = self.gmail_service._get_or_create_label("New Label")
        
        # 검증
        self.assertEqual(label_id, "new_label")
        
        # 메서드 호출 검증
        mock_labels_obj.create.assert_called_once_with(
            userId="me", body={"name": "New Label"})

if __name__ == "__main__":
    unittest.main()