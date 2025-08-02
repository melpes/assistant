# -*- coding: utf-8 -*-
"""
데이터 관리 도구 모듈

RuleEngine, BackupManager, ConfigManager를 활용한 데이터 관리 도구 함수들을 제공합니다.
LLM 에이전트가 호출할 수 있는 도구 함수 인터페이스를 구현합니다.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from src.rule_engine import RuleEngine
from src.backup_manager import BackupManager
from src.config_manager import ConfigManager
from src.repositories.rule_repository import RuleRepository
from src.models import ClassificationRule

# 로거 설정
logger = logging.getLogger(__name__)

# 전역 인스턴스
_rule_repository = None
_rule_engine = None
_backup_manager = None
_config_manager = None

def _get_rule_repository() -> RuleRepository:
    """규칙 저장소 인스턴스를 반환합니다."""
    global _rule_repository
    if _rule_repository is None:
        _rule_repository = RuleRepository()
    return _rule_repository

def _get_rule_engine() -> RuleEngine:
    """규칙 엔진 인스턴스를 반환합니다."""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine(_get_rule_repository())
    return _rule_engine

def _get_backup_manager() -> BackupManager:
    """백업 관리자 인스턴스를 반환합니다."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(_get_config_manager())
    return _backup_manager

def _get_config_manager() -> ConfigManager:
    """설정 관리자 인스턴스를 반환합니다."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def add_classification_rule(
    rule_name: str,
    rule_type: str,
    condition_type: str,
    condition_value: str,
    target_value: str,
    priority: int = 0
) -> Dict[str, Any]:
    """
    새로운 분류 규칙을 추가합니다.
    
    Args:
        rule_name: 규칙 이름
        rule_type: 규칙 유형 (category/payment_method/filter)
        condition_type: 조건 유형 (contains/equals/regex/amount_range)
        condition_value: 조건 값
        target_value: 분류 결과 값
        priority: 우선순위
        
    Returns:
        Dict[str, Any]: 추가된 규칙 정보
    """
    try:
        # 유효성 검사
        if rule_type not in ['category', 'payment_method', 'filter']:
            return {
                'success': False,
                'error': f"유효하지 않은 규칙 유형: {rule_type}. 'category', 'payment_method', 'filter' 중 하나여야 합니다."
            }
        
        if condition_type not in [
            ClassificationRule.CONDITION_CONTAINS,
            ClassificationRule.CONDITION_EQUALS,
            ClassificationRule.CONDITION_REGEX,
            ClassificationRule.CONDITION_AMOUNT_RANGE
        ]:
            return {
                'success': False,
                'error': f"유효하지 않은 조건 유형: {condition_type}. 'contains', 'equals', 'regex', 'amount_range' 중 하나여야 합니다."
            }
        
        # 규칙 객체 생성
        rule = ClassificationRule(
            rule_name=rule_name,
            rule_type=rule_type,
            condition_type=condition_type,
            condition_value=condition_value,
            target_value=target_value,
            priority=priority,
            is_active=True,
            created_by='financial_agent'
        )
        
        # 규칙 추가
        rule_engine = _get_rule_engine()
        created_rule = rule_engine.add_rule(rule)
        
        return {
            'success': True,
            'rule': {
                'id': created_rule.id,
                'rule_name': created_rule.rule_name,
                'rule_type': created_rule.rule_type,
                'condition_type': created_rule.condition_type,
                'condition_value': created_rule.condition_value,
                'target_value': created_rule.target_value,
                'priority': created_rule.priority,
                'is_active': created_rule.is_active,
                'created_at': created_rule.created_at.isoformat() if created_rule.created_at else None,
                'created_by': created_rule.created_by
            }
        }
        
    except Exception as e:
        logger.error(f"규칙 추가 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"규칙 추가 중 오류 발생: {str(e)}"
        }

def update_classification_rule(
    rule_id: int,
    rule_name: str = None,
    condition_type: str = None,
    condition_value: str = None,
    target_value: str = None,
    priority: int = None,
    is_active: bool = None
) -> Dict[str, Any]:
    """
    기존 분류 규칙을 업데이트합니다.
    
    Args:
        rule_id: 규칙 ID
        rule_name: 새 규칙 이름
        condition_type: 새 조건 유형
        condition_value: 새 조건 값
        target_value: 새 분류 결과 값
        priority: 새 우선순위
        is_active: 활성화 여부
        
    Returns:
        Dict[str, Any]: 업데이트된 규칙 정보
    """
    try:
        # 규칙 조회
        rule_repository = _get_rule_repository()
        rule = rule_repository.read(rule_id)
        
        if not rule:
            return {
                'success': False,
                'error': f"규칙을 찾을 수 없습니다: ID={rule_id}"
            }
        
        # 필드 업데이트
        if rule_name is not None:
            rule.rule_name = rule_name
        
        if condition_type is not None:
            if condition_type not in [
                ClassificationRule.CONDITION_CONTAINS,
                ClassificationRule.CONDITION_EQUALS,
                ClassificationRule.CONDITION_REGEX,
                ClassificationRule.CONDITION_AMOUNT_RANGE
            ]:
                return {
                    'success': False,
                    'error': f"유효하지 않은 조건 유형: {condition_type}"
                }
            rule.condition_type = condition_type
        
        if condition_value is not None:
            rule.condition_value = condition_value
        
        if target_value is not None:
            rule.target_value = target_value
        
        if priority is not None:
            rule.priority = priority
        
        if is_active is not None:
            rule.is_active = is_active
        
        # 규칙 업데이트
        rule_engine = _get_rule_engine()
        updated_rule = rule_engine.update_rule(rule)
        
        return {
            'success': True,
            'rule': {
                'id': updated_rule.id,
                'rule_name': updated_rule.rule_name,
                'rule_type': updated_rule.rule_type,
                'condition_type': updated_rule.condition_type,
                'condition_value': updated_rule.condition_value,
                'target_value': updated_rule.target_value,
                'priority': updated_rule.priority,
                'is_active': updated_rule.is_active,
                'created_at': updated_rule.created_at.isoformat() if updated_rule.created_at else None,
                'created_by': updated_rule.created_by
            }
        }
        
    except Exception as e:
        logger.error(f"규칙 업데이트 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"규칙 업데이트 중 오류 발생: {str(e)}"
        }

def delete_classification_rule(rule_id: int) -> Dict[str, Any]:
    """
    분류 규칙을 삭제합니다.
    
    Args:
        rule_id: 규칙 ID
        
    Returns:
        Dict[str, Any]: 삭제 결과
    """
    try:
        # 규칙 삭제
        rule_engine = _get_rule_engine()
        success = rule_engine.delete_rule(rule_id)
        
        if success:
            return {
                'success': True,
                'message': f"규칙이 삭제되었습니다: ID={rule_id}"
            }
        else:
            return {
                'success': False,
                'error': f"규칙 삭제 실패: ID={rule_id}"
            }
        
    except Exception as e:
        logger.error(f"규칙 삭제 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"규칙 삭제 중 오류 발생: {str(e)}"
        }

def get_classification_rules(rule_type: str = None) -> Dict[str, Any]:
    """
    분류 규칙 목록을 조회합니다.
    
    Args:
        rule_type: 규칙 유형 (category/payment_method/filter)
        
    Returns:
        Dict[str, Any]: 규칙 목록
    """
    try:
        # 규칙 저장소
        rule_repository = _get_rule_repository()
        
        # 규칙 조회
        if rule_type:
            rules = rule_repository.get_active_rules_by_type(rule_type)
        else:
            rules = rule_repository.get_all_rules()
        
        # 결과 변환
        rule_list = []
        for rule in rules:
            rule_list.append({
                'id': rule.id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'condition_type': rule.condition_type,
                'condition_value': rule.condition_value,
                'target_value': rule.target_value,
                'priority': rule.priority,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat() if rule.created_at else None,
                'created_by': rule.created_by
            })
        
        return {
            'success': True,
            'rules': rule_list,
            'count': len(rule_list)
        }
        
    except Exception as e:
        logger.error(f"규칙 조회 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"규칙 조회 중 오류 발생: {str(e)}"
        }

def get_rule_stats(rule_type: str = None) -> Dict[str, Any]:
    """
    분류 규칙 통계를 조회합니다.
    
    Args:
        rule_type: 규칙 유형 (category/payment_method/filter)
        
    Returns:
        Dict[str, Any]: 규칙 통계
    """
    try:
        # 규칙 엔진
        rule_engine = _get_rule_engine()
        
        # 통계 조회
        if rule_type:
            stats = rule_engine.get_rule_stats(rule_type)
            return {
                'success': True,
                'stats': stats,
                'rule_type': rule_type
            }
        else:
            # 모든 유형의 통계 조회
            all_stats = {}
            for rt in ['category', 'payment_method', 'filter']:
                all_stats[rt] = rule_engine.get_rule_stats(rt)
            
            return {
                'success': True,
                'stats': all_stats
            }
        
    except Exception as e:
        logger.error(f"규칙 통계 조회 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"규칙 통계 조회 중 오류 발생: {str(e)}"
        }

def backup_data(
    backup_name: str = None,
    include_settings: bool = True
) -> Dict[str, Any]:
    """
    데이터를 백업합니다.
    
    Args:
        backup_name: 백업 이름
        include_settings: 설정 포함 여부
        
    Returns:
        Dict[str, Any]: 백업 결과 정보
    """
    try:
        # 백업 관리자
        backup_manager = _get_backup_manager()
        
        # 데이터베이스 백업
        db_backup_file = backup_manager.backup_database()
        
        result = {
            'success': bool(db_backup_file),
            'database_backup': db_backup_file,
            'timestamp': datetime.now().isoformat(),
            'settings_backup': None
        }
        
        # 설정 백업
        if include_settings:
            config_backup_file = backup_manager.backup_config()
            result['settings_backup'] = config_backup_file
        
        if not result['success']:
            result['error'] = "데이터베이스 백업 실패"
        
        return result
        
    except Exception as e:
        logger.error(f"데이터 백업 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"데이터 백업 중 오류 발생: {str(e)}"
        }

def restore_data(
    backup_path: str,
    include_settings: bool = True
) -> Dict[str, Any]:
    """
    백업에서 데이터를 복원합니다.
    
    Args:
        backup_path: 백업 파일 경로
        include_settings: 설정 복원 여부
        
    Returns:
        Dict[str, Any]: 복원 결과 정보
    """
    try:
        # 백업 파일 확인
        if not os.path.exists(backup_path):
            return {
                'success': False,
                'error': f"백업 파일을 찾을 수 없습니다: {backup_path}"
            }
        
        # 백업 관리자
        backup_manager = _get_backup_manager()
        
        # 데이터베이스 복원
        if backup_path.endswith('.db') or backup_path.endswith('.zip'):
            db_restore_success = backup_manager.restore_database(backup_path)
            
            return {
                'success': db_restore_success,
                'message': "데이터베이스 복원 완료" if db_restore_success else "데이터베이스 복원 실패",
                'timestamp': datetime.now().isoformat()
            }
        
        # 설정 복원
        elif backup_path.endswith('.yaml') and include_settings:
            config_restore_success = backup_manager.restore_config(backup_path)
            
            return {
                'success': config_restore_success,
                'message': "설정 복원 완료" if config_restore_success else "설정 복원 실패",
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            return {
                'success': False,
                'error': f"지원하지 않는 백업 파일 형식: {backup_path}"
            }
        
    except Exception as e:
        logger.error(f"데이터 복원 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"데이터 복원 중 오류 발생: {str(e)}"
        }

def list_backups(backup_type: str = 'database') -> Dict[str, Any]:
    """
    백업 목록을 조회합니다.
    
    Args:
        backup_type: 백업 유형 (database/config)
        
    Returns:
        Dict[str, Any]: 백업 목록
    """
    try:
        # 백업 관리자
        backup_manager = _get_backup_manager()
        
        # 백업 목록 조회
        backups = backup_manager.list_backups(backup_type)
        
        # 결과 변환
        backup_list = []
        for backup in backups:
            backup_info = {
                'file': backup['file'],
                'filename': backup.get('filename', os.path.basename(backup['file'])),
                'timestamp': backup['timestamp'].isoformat() if isinstance(backup['timestamp'], datetime) else backup['timestamp'],
                'size': backup.get('size', 0),
                'type': backup.get('type', backup_type)
            }
            backup_list.append(backup_info)
        
        return {
            'success': True,
            'backups': backup_list,
            'count': len(backup_list),
            'backup_type': backup_type
        }
        
    except Exception as e:
        logger.error(f"백업 목록 조회 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"백업 목록 조회 중 오류 발생: {str(e)}"
        }

def export_data(format: str = 'csv', tables: List[str] = None) -> Dict[str, Any]:
    """
    데이터를 내보냅니다.
    
    Args:
        format: 내보내기 형식 (csv/json)
        tables: 내보낼 테이블 목록 (None: 모든 테이블)
        
    Returns:
        Dict[str, Any]: 내보내기 결과
    """
    try:
        # 백업 관리자
        backup_manager = _get_backup_manager()
        
        # 데이터 내보내기
        export_files = backup_manager.export_data(format, tables)
        
        if export_files:
            return {
                'success': True,
                'files': export_files,
                'format': format,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': "데이터 내보내기 실패"
            }
        
    except Exception as e:
        logger.error(f"데이터 내보내기 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"데이터 내보내기 중 오류 발생: {str(e)}"
        }

def get_system_status() -> Dict[str, Any]:
    """
    시스템 상태 정보를 반환합니다.
    
    Returns:
        Dict[str, Any]: 시스템 상태 정보
    """
    try:
        # 설정 관리자
        config_manager = _get_config_manager()
        
        # 시스템 설정 조회
        system_config = config_manager.get_config('system')
        
        # 백업 관리자
        backup_manager = _get_backup_manager()
        
        # 백업 상태 조회
        db_backups = backup_manager.list_backups('database')
        config_backups = backup_manager.list_backups('config')
        
        # 데이터베이스 경로
        db_path = config_manager.get_config_value('system.database.path')
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        # 마지막 백업 정보
        last_db_backup = db_backups[0] if db_backups else None
        last_config_backup = config_backups[0] if config_backups else None
        
        return {
            'success': True,
            'system': {
                'database': {
                    'path': db_path,
                    'size': db_size,
                    'exists': os.path.exists(db_path),
                    'backup_enabled': config_manager.get_config_value('system.database.backup_enabled', True),
                    'backup_interval_days': config_manager.get_config_value('system.database.backup_interval_days', 7),
                    'last_backup': last_db_backup['timestamp'].isoformat() if last_db_backup and isinstance(last_db_backup['timestamp'], datetime) else None
                },
                'config': {
                    'path': config_manager.config_file,
                    'last_backup': last_config_backup['timestamp'].isoformat() if last_config_backup and isinstance(last_config_backup['timestamp'], datetime) else None
                },
                'backups': {
                    'database_count': len(db_backups),
                    'config_count': len(config_backups)
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"시스템 상태 조회 중 오류 발생: {str(e)}"
        }

def update_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    시스템 설정을 업데이트합니다.
    
    Args:
        settings: 업데이트할 설정 정보
        
    Returns:
        Dict[str, Any]: 업데이트된 설정 정보
    """
    try:
        # 설정 관리자
        config_manager = _get_config_manager()
        
        # 설정 업데이트
        updated_settings = {}
        failed_settings = {}
        
        for key, value in settings.items():
            success = config_manager.set_config_value(key, value)
            if success:
                updated_settings[key] = value
            else:
                failed_settings[key] = value
        
        # 설정 저장
        config_manager.save_config()
        
        result = {
            'success': len(updated_settings) > 0,
            'updated_settings': updated_settings,
            'timestamp': datetime.now().isoformat()
        }
        
        if failed_settings:
            result['failed_settings'] = failed_settings
        
        return result
        
    except Exception as e:
        logger.error(f"설정 업데이트 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"설정 업데이트 중 오류 발생: {str(e)}"
        }

def get_settings(section: str = None) -> Dict[str, Any]:
    """
    시스템 설정을 조회합니다.
    
    Args:
        section: 설정 섹션 (system, user, rules)
        
    Returns:
        Dict[str, Any]: 설정 정보
    """
    try:
        # 설정 관리자
        config_manager = _get_config_manager()
        
        # 설정 조회
        if section:
            settings = config_manager.get_config(section)
            return {
                'success': True,
                'settings': settings,
                'section': section
            }
        else:
            settings = config_manager.get_config()
            return {
                'success': True,
                'settings': settings
            }
        
    except Exception as e:
        logger.error(f"설정 조회 중 오류 발생: {e}")
        return {
            'success': False,
            'error': f"설정 조회 중 오류 발생: {str(e)}"
        }