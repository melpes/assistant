"""
pytest 설정 및 공통 픽스처
"""
import pytest
import os
import sys
from unittest.mock import Mock

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def pytest_configure(config):
    """pytest 설정"""
    # 커스텀 마커 등록
    config.addinivalue_line(
        "markers", "integration: 실제 API를 사용하는 통합 테스트"
    )
    config.addinivalue_line(
        "markers", "slow: 실행 시간이 오래 걸리는 테스트"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 처리"""
    # 통합 테스트에 skip 마커 추가 (기본적으로 실행하지 않음)
    skip_integration = pytest.mark.skip(reason="통합 테스트는 --integration 옵션으로 실행")
    
    for item in items:
        if "integration" in item.keywords:
            if not config.getoption("--integration"):
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """커맨드라인 옵션 추가"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="통합 테스트 실행"
    )


@pytest.fixture
def mock_config():
    """Mock 설정"""
    return {
        'provider': 'google',
        'google': {
            'calendar_id': 'primary',
            'use_service_pool': True
        }
    }


@pytest.fixture
def sample_google_api_response():
    """샘플 Google API 응답"""
    return {
        'items': [
            {
                'id': 'sample-event-1',
                'summary': '샘플 이벤트 1',
                'description': '첫 번째 샘플 이벤트',
                'location': '서울시 강남구',
                'start': {'dateTime': '2024-01-01T10:00:00+09:00'},
                'end': {'dateTime': '2024-01-01T11:00:00+09:00'}
            },
            {
                'id': 'sample-event-2',
                'summary': '샘플 이벤트 2',
                'start': {'date': '2024-01-02'},
                'end': {'date': '2024-01-03'}
            }
        ]
    }


@pytest.fixture
def mock_google_service():
    """Mock Google API 서비스"""
    service = Mock()
    events_resource = Mock()
    service.events.return_value = events_resource
    
    # 기본 응답 설정
    events_resource.list.return_value.execute.return_value = {'items': []}
    events_resource.insert.return_value.execute.return_value = {
        'id': 'new-event-123',
        'summary': '새 이벤트',
        'start': {'dateTime': '2024-01-01T10:00:00+09:00'},
        'end': {'dateTime': '2024-01-01T11:00:00+09:00'}
    }
    events_resource.update.return_value.execute.return_value = {
        'id': 'updated-event-123',
        'summary': '수정된 이벤트',
        'start': {'dateTime': '2024-01-01T10:00:00+09:00'},
        'end': {'dateTime': '2024-01-01T11:00:00+09:00'}
    }
    events_resource.delete.return_value.execute.return_value = None
    events_resource.get.return_value.execute.return_value = {
        'id': 'get-event-123',
        'summary': '조회된 이벤트',
        'start': {'dateTime': '2024-01-01T10:00:00+09:00'},
        'end': {'dateTime': '2024-01-01T11:00:00+09:00'}
    }
    
    return service


@pytest.fixture(autouse=True)
def setup_test_environment():
    """테스트 환경 설정"""
    # 테스트 중에는 실제 파일 시스템 접근을 제한
    original_exists = os.path.exists
    
    def mock_exists(path):
        # 테스트 관련 파일만 존재한다고 가정
        if 'test_' in path or 'mock_' in path:
            return True
        return original_exists(path)
    
    # 테스트 후 정리
    yield
    
    # 필요한 경우 정리 작업 수행


@pytest.fixture
def temp_credentials_file(tmp_path):
    """임시 인증 파일"""
    credentials_content = {
        "installed": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    
    credentials_file = tmp_path / "test_credentials.json"
    credentials_file.write_text(str(credentials_content).replace("'", '"'))
    
    return str(credentials_file)


@pytest.fixture
def temp_token_file(tmp_path):
    """임시 토큰 파일"""
    token_content = {
        "token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret"
    }
    
    token_file = tmp_path / "test_token.json"
    token_file.write_text(str(token_content).replace("'", '"'))
    
    return str(token_file)