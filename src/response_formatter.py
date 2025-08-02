# -*- coding: utf-8 -*-
"""
응답 포맷팅 모듈

도구 실행 결과를 사용자 친화적인 응답으로 변환하는 기능을 제공합니다.
"""

import json
import re
from typing import Dict, List, Any, Union, Optional
from datetime import datetime

class ResponseFormatter:
    """
    도구 실행 결과를 사용자 친화적인 응답으로 변환하는 클래스
    """
    
    def __init__(self):
        """
        ResponseFormatter 초기화
        """
        # 통화 포맷 설정
        self.currency_symbol = "원"
        self.decimal_separator = "."
        self.thousands_separator = ","
    
    def format_response(self, result: Any) -> str:
        """
        도구 실행 결과를 사용자 친화적인 응답으로 포맷팅합니다.
        
        Args:
            result: 도구 실행 결과
            
        Returns:
            str: 포맷팅된 응답
        """
        # 결과가 딕셔너리가 아닌 경우 그대로 반환
        if not isinstance(result, dict):
            return str(result)
        
        # 오류 결과 처리
        if result.get('success') is False and 'error' in result:
            return self._format_error_response(result)
        
        # 결과 유형에 따른 포맷팅
        if 'transactions' in result:
            return self._format_transactions(result)
        elif 'analysis' in result:
            return self._format_analysis(result)
        elif 'comparison' in result:
            return self._format_comparison(result)
        elif 'rule' in result:
            return self._format_rule(result)
        elif 'rules' in result:
            return self._format_rules(result)
        elif 'backups' in result:
            return self._format_backups(result)
        elif 'system' in result:
            return self._format_system_status(result)
        elif 'settings' in result:
            return self._format_settings(result)
        elif 'summary' in result:
            return self._format_summary(result)
        elif 'transaction' in result:
            return self._format_single_transaction(result)
        elif 'templates' in result:
            return self._format_templates(result)
        elif 'suggestions' in result:
            return self._format_suggestions(result)
        
        # 기본 포맷팅 (JSON 문자열로 변환)
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    def _format_error_response(self, result: Dict) -> str:
        """
        오류 응답을 포맷팅합니다.
        
        Args:
            result: 오류 정보가 포함된 결과
            
        Returns:
            str: 포맷팅된 오류 메시지
        """
        error_msg = result.get('error', '알 수 없는 오류')
        error_code = result.get('error_code', '')
        error_details = result.get('error_details', '')
        
        formatted = "⚠️ 오류가 발생했습니다\n\n"
        formatted += f"{error_msg}\n"
        
        if error_code:
            formatted += f"\n오류 코드: {error_code}"
        
        if error_details:
            formatted += f"\n\n상세 정보: {error_details}"
            
        # 사용자 안내 메시지 추가
        if '데이터베이스' in error_msg:
            formatted += "\n\n💡 데이터베이스 연결을 확인해보세요. 데이터베이스 파일이 손상되었거나 접근 권한이 없을 수 있습니다."
        elif '인증' in error_msg or '권한' in error_msg:
            formatted += "\n\n💡 인증 정보를 확인해보세요. 토큰이 만료되었거나 필요한 권한이 없을 수 있습니다."
        elif '네트워크' in error_msg:
            formatted += "\n\n💡 인터넷 연결을 확인해보세요. 서버에 연결할 수 없거나 응답이 지연되고 있을 수 있습니다."
        elif '입력' in error_msg or '파라미터' in error_msg:
            formatted += "\n\n💡 입력 정보를 확인해보세요. 필수 정보가 누락되었거나 형식이 올바르지 않을 수 있습니다."
        
        return formatted
    
    def _format_transactions(self, result: Dict) -> str:
        """
        거래 목록을 포맷팅합니다.
        
        Args:
            result: 거래 목록이 포함된 결과
            
        Returns:
            str: 포맷팅된 거래 목록
        """
        transactions = result.get('transactions', [])
        if not transactions:
            return "📋 조회된 거래가 없습니다."
        
        # 거래 유형 확인 (수입/지출)
        transaction_type = self._determine_transaction_type(transactions)
        
        # 제목 설정
        if transaction_type == "income":
            formatted = "💰 수입 내역\n\n"
        elif transaction_type == "expense":
            formatted = "💸 지출 내역\n\n"
        else:
            formatted = "📊 거래 내역\n\n"
        
        # 날짜별 그룹화 여부 확인
        group_by_date = result.get('group_by_date', False)
        
        if group_by_date:
            # 날짜별로 그룹화
            date_groups = {}
            for tx in transactions:
                date = tx.get('date', '날짜 없음')
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(tx)
            
            # 날짜별로 정렬하여 출력
            for date in sorted(date_groups.keys()):
                formatted += f"📅 {date}\n"
                daily_total = 0
                
                for tx in date_groups[date]:
                    amount = tx.get('amount', 0)
                    description = tx.get('description', '설명 없음')
                    category = tx.get('category', '미분류')
                    payment_method = tx.get('payment_method', '')
                    
                    formatted += f"- {description}: {self._format_currency(amount)}"
                    if category:
                        formatted += f" ({category})"
                    if payment_method:
                        formatted += f" | {payment_method}"
                    formatted += "\n"
                    
                    daily_total += amount
                
                formatted += f"   일일 합계: {self._format_currency(daily_total)}\n\n"
        else:
            # 일반 목록 형식
            for i, tx in enumerate(transactions[:15], 1):
                date = tx.get('date', '날짜 없음')
                amount = tx.get('amount', 0)
                description = tx.get('description', '설명 없음')
                category = tx.get('category', '미분류')
                payment_method = tx.get('payment_method', '')
                
                formatted += f"{i}. [{date}] {description} - {self._format_currency(amount)}"
                if category:
                    formatted += f" ({category})"
                if payment_method:
                    formatted += f" | {payment_method}"
                formatted += "\n"
            
            if len(transactions) > 15:
                formatted += f"\n... 외 {len(transactions) - 15}건의 거래가 더 있습니다."
        
        # 요약 정보 추가
        if 'total' in result or 'summary' in result:
            formatted += "\n📊 요약 정보\n"
            
            if 'total' in result:
                formatted += f"총액: {self._format_currency(result['total'])}\n"
            
            if 'average' in result:
                formatted += f"평균: {self._format_currency(result['average'])}\n"
                
            if 'min' in result:
                formatted += f"최소: {self._format_currency(result['min'])}\n"
                
            if 'max' in result:
                formatted += f"최대: {self._format_currency(result['max'])}\n"
                
            if 'count' in result:
                formatted += f"거래 수: {result['count']}건\n"
        
        # 인사이트 추가
        if 'insights' in result:
            formatted += "\n💡 인사이트\n"
            for insight in result['insights']:
                formatted += f"- {insight}\n"
        
        return formatted
        
    def _format_analysis(self, result: Dict) -> str:
        """
        분석 결과를 포맷팅합니다.
        
        Args:
            result: 분석 결과가 포함된 결과
            
        Returns:
            str: 포맷팅된 분석 결과
        """
        analysis = result.get('analysis', {})
        if not analysis:
            return "📊 분석 결과가 없습니다."
        
        # 분석 유형 확인
        analysis_type = result.get('type', '일반')
        
        # 제목 설정
        if analysis_type == 'expense':
            formatted = "💸 지출 분석 결과\n\n"
        elif analysis_type == 'income':
            formatted = "💰 수입 분석 결과\n\n"
        elif analysis_type == 'trend':
            formatted = "📈 추세 분석 결과\n\n"
        else:
            formatted = "📊 분석 결과\n\n"
        
        # 요약 정보 추가
        if 'summary' in analysis:
            formatted += f"📝 요약: {analysis['summary']}\n\n"
        
        # 기간 정보 추가
        if 'period' in result:
            formatted += f"📅 분석 기간: {result['period']}\n\n"
        
        # 상세 내역 추가
        if 'details' in analysis and isinstance(analysis['details'], list):
            formatted += "📋 상세 내역:\n"
            
            # 차트 데이터 형식인지 확인
            is_chart_data = all('name' in item and 'value' in item for item in analysis['details'] if isinstance(item, dict))
            
            if is_chart_data:
                # 차트 데이터 포맷팅
                total_value = sum(item.get('value', 0) for item in analysis['details'] if isinstance(item, dict))
                
                for item in analysis['details'][:10]:
                    if isinstance(item, dict):
                        name = item.get('name', '항목')
                        value = item.get('value', 0)
                        percentage = item.get('percentage', (value / total_value * 100) if total_value > 0 else 0)
                        
                        # 막대 그래프 생성
                        bar_length = int(percentage / 2)  # 최대 50자
                        bar = '█' * bar_length
                        
                        formatted += f"- {name}: {self._format_currency(value)} ({percentage:.1f}%)\n"
                        formatted += f"  {bar}\n"
                
                if len(analysis['details']) > 10:
                    formatted += f"\n... 외 {len(analysis['details']) - 10}개 항목이 더 있습니다.\n"
            else:
                # 일반 목록 포맷팅
                for item in analysis['details'][:15]:
                    if isinstance(item, dict):
                        formatted += f"- {json.dumps(item, ensure_ascii=False)}\n"
                    else:
                        formatted += f"- {item}\n"
                
                if len(analysis['details']) > 15:
                    formatted += f"\n... 외 {len(analysis['details']) - 15}개 항목이 더 있습니다.\n"
        
        # 인사이트 추가
        if 'insights' in analysis:
            formatted += "\n💡 주요 인사이트:\n"
            for insight in analysis['insights']:
                formatted += f"- {insight}\n"
        
        # 추천 사항 추가
        if 'recommendations' in analysis:
            formatted += "\n✨ 추천 사항:\n"
            for recommendation in analysis['recommendations']:
                formatted += f"- {recommendation}\n"
        
        return formatted
    
    def _format_comparison(self, result: Dict) -> str:
        """
        비교 분석 결과를 포맷팅합니다.
        
        Args:
            result: 비교 분석 결과가 포함된 결과
            
        Returns:
            str: 포맷팅된 비교 분석 결과
        """
        comparison = result.get('comparison', {})
        if not comparison:
            return "📊 비교 분석 결과가 없습니다."
        
        # 비교 유형 확인
        comparison_type = result.get('type', '일반')
        
        # 제목 설정
        if comparison_type == 'expense':
            formatted = "💸 지출 비교 분석\n\n"
        elif comparison_type == 'income':
            formatted = "💰 수입 비교 분석\n\n"
        else:
            formatted = "📊 비교 분석\n\n"
        
        # 기간 정보 추가
        if 'period1' in result and 'period2' in result:
            formatted += f"📅 비교 기간:\n"
            formatted += f"- 기간 1: {result['period1']}\n"
            formatted += f"- 기간 2: {result['period2']}\n\n"
        
        # 요약 정보 추가
        if 'summary' in comparison:
            formatted += f"📝 요약: {comparison['summary']}\n\n"
        
        # 전체 변화 추가
        if 'total_change' in comparison:
            change = comparison['total_change']
            change_percentage = comparison.get('total_change_percentage', 0)
            
            if change > 0:
                formatted += f"📈 전체 변화: {self._format_currency(change)} 증가 (+{change_percentage:.1f}%)\n\n"
            elif change < 0:
                formatted += f"📉 전체 변화: {self._format_currency(abs(change))} 감소 ({change_percentage:.1f}%)\n\n"
            else:
                formatted += f"📊 전체 변화: 변동 없음 (0%)\n\n"
        
        # 주요 변화 항목 추가
        if 'changes' in comparison and isinstance(comparison['changes'], list):
            formatted += "📋 주요 변화 항목:\n"
            
            for item in comparison['changes'][:10]:
                if isinstance(item, dict):
                    name = item.get('name', '항목')
                    value1 = item.get('value1', 0)
                    value2 = item.get('value2', 0)
                    change = item.get('change', value2 - value1)
                    change_percentage = item.get('change_percentage', 0)
                    
                    formatted += f"- {name}:\n"
                    formatted += f"  - 기간 1: {self._format_currency(value1)}\n"
                    formatted += f"  - 기간 2: {self._format_currency(value2)}\n"
                    
                    if change > 0:
                        formatted += f"  - 변화: {self._format_currency(change)} 증가 (+{change_percentage:.1f}%)\n"
                    elif change < 0:
                        formatted += f"  - 변화: {self._format_currency(abs(change))} 감소 ({change_percentage:.1f}%)\n"
                    else:
                        formatted += f"  - 변화: 변동 없음 (0%)\n"
            
            if len(comparison['changes']) > 10:
                formatted += f"\n... 외 {len(comparison['changes']) - 10}개 항목이 더 있습니다.\n"
        
        # 인사이트 추가
        if 'insights' in comparison:
            formatted += "\n💡 주요 인사이트:\n"
            for insight in comparison['insights']:
                formatted += f"- {insight}\n"
        
        return formatted
        
    def _format_rule(self, result: Dict) -> str:
        """
        규칙 정보를 포맷팅합니다.
        
        Args:
            result: 규칙 정보가 포함된 결과
            
        Returns:
            str: 포맷팅된 규칙 정보
        """
        rule = result.get('rule', {})
        if not rule:
            return "📋 규칙 정보가 없습니다."
        
        formatted = "📜 규칙 정보\n\n"
        formatted += f"이름: {rule.get('rule_name', '이름 없음')}\n"
        formatted += f"유형: {rule.get('rule_type', '유형 없음')}\n"
        formatted += f"조건: {rule.get('condition_type', '조건 없음')} - {rule.get('condition_value', '값 없음')}\n"
        formatted += f"결과값: {rule.get('target_value', '값 없음')}\n"
        formatted += f"우선순위: {rule.get('priority', 0)}\n"
        formatted += f"활성화: {'✅ 예' if rule.get('is_active', False) else '❌ 아니오'}\n"
        
        # 규칙 통계 추가
        if 'stats' in result:
            stats = result['stats']
            formatted += "\n📊 규칙 통계\n"
            formatted += f"적용된 거래 수: {stats.get('applied_count', 0)}건\n"
            formatted += f"마지막 적용: {stats.get('last_applied', '없음')}\n"
        
        return formatted
    
    def _format_rules(self, result: Dict) -> str:
        """
        규칙 목록을 포맷팅합니다.
        
        Args:
            result: 규칙 목록이 포함된 결과
            
        Returns:
            str: 포맷팅된 규칙 목록
        """
        rules = result.get('rules', [])
        if not rules:
            return "📋 규칙이 없습니다."
        
        formatted = "📜 규칙 목록\n\n"
        
        # 규칙 유형별로 그룹화
        rule_types = {}
        for rule in rules:
            rule_type = rule.get('rule_type', '기타')
            if rule_type not in rule_types:
                rule_types[rule_type] = []
            rule_types[rule_type].append(rule)
        
        # 유형별로 출력
        for rule_type, type_rules in rule_types.items():
            formatted += f"📌 {rule_type} 규칙\n"
            
            for i, rule in enumerate(type_rules, 1):
                name = rule.get('rule_name', '이름 없음')
                condition = f"{rule.get('condition_type', '조건 없음')} - {rule.get('condition_value', '값 없음')}"
                target = rule.get('target_value', '값 없음')
                is_active = rule.get('is_active', False)
                
                status_icon = "✅" if is_active else "❌"
                formatted += f"{i}. {status_icon} {name}: {condition} → {target}\n"
            
            formatted += "\n"
        
        # 규칙 통계 추가
        if 'stats' in result:
            stats = result['stats']
            formatted += "📊 규칙 통계\n"
            formatted += f"총 규칙 수: {stats.get('total_count', len(rules))}개\n"
            formatted += f"활성 규칙 수: {stats.get('active_count', 0)}개\n"
            formatted += f"적용된 거래 수: {stats.get('applied_count', 0)}건\n"
        
        return formatted
    
    def _format_backups(self, result: Dict) -> str:
        """
        백업 목록을 포맷팅합니다.
        
        Args:
            result: 백업 목록이 포함된 결과
            
        Returns:
            str: 포맷팅된 백업 목록
        """
        backups = result.get('backups', [])
        if not backups:
            return "📋 백업이 없습니다."
        
        formatted = "💾 백업 목록\n\n"
        
        for i, backup in enumerate(backups[:15], 1):
            filename = backup.get('filename', '파일명 없음')
            timestamp = backup.get('timestamp', '시간 없음')
            size = backup.get('size', 0)
            size_str = f"{size / 1024 / 1024:.2f} MB" if size > 0 else "크기 정보 없음"
            backup_type = backup.get('type', '일반')
            
            formatted += f"{i}. [{backup_type}] {filename}\n"
            formatted += f"   📅 {timestamp} | 📦 {size_str}\n"
        
        if len(backups) > 15:
            formatted += f"\n... 외 {len(backups) - 15}개 백업이 더 있습니다.\n"
        
        return formatted
    
    def _format_system_status(self, result: Dict) -> str:
        """
        시스템 상태를 포맷팅합니다.
        
        Args:
            result: 시스템 상태가 포함된 결과
            
        Returns:
            str: 포맷팅된 시스템 상태
        """
        system = result.get('system', {})
        if not system:
            return "📋 시스템 정보가 없습니다."
        
        formatted = "🖥️ 시스템 상태\n\n"
        
        if 'database' in system:
            db = system['database']
            formatted += "📁 데이터베이스\n"
            formatted += f"- 경로: {db.get('path', '정보 없음')}\n"
            formatted += f"- 크기: {db.get('size', 0) / 1024 / 1024:.2f} MB\n"
            formatted += f"- 마지막 백업: {db.get('last_backup', '백업 없음')}\n"
            formatted += f"- 거래 수: {db.get('transaction_count', 0)}건\n\n"
        
        if 'backups' in system:
            backups = system['backups']
            formatted += "💾 백업 정보\n"
            formatted += f"- 데이터베이스 백업 수: {backups.get('database_count', 0)}개\n"
            formatted += f"- 설정 백업 수: {backups.get('config_count', 0)}개\n"
            formatted += f"- 마지막 백업 시간: {backups.get('last_backup_time', '없음')}\n\n"
        
        if 'performance' in system:
            perf = system['performance']
            formatted += "⚡ 성능 정보\n"
            formatted += f"- 평균 쿼리 시간: {perf.get('avg_query_time', 0):.2f}ms\n"
            formatted += f"- 캐시 히트율: {perf.get('cache_hit_rate', 0):.1f}%\n"
            formatted += f"- 메모리 사용량: {perf.get('memory_usage', 0) / 1024 / 1024:.2f} MB\n\n"
        
        if 'version' in system:
            version = system['version']
            formatted += "📌 버전 정보\n"
            formatted += f"- 시스템 버전: {version.get('system', '정보 없음')}\n"
            formatted += f"- 데이터베이스 버전: {version.get('database', '정보 없음')}\n"
        
        return formatted
        
    def _format_settings(self, result: Dict) -> str:
        """
        설정 정보를 포맷팅합니다.
        
        Args:
            result: 설정 정보가 포함된 결과
            
        Returns:
            str: 포맷팅된 설정 정보
        """
        settings = result.get('settings', {})
        if not settings:
            return "📋 설정 정보가 없습니다."
        
        formatted = "⚙️ 설정 정보\n\n"
        
        # 설정 정보를 재귀적으로 포맷팅하는 함수
        def format_settings(settings_dict, prefix=""):
            result_str = ""
            for key, value in settings_dict.items():
                if isinstance(value, dict):
                    result_str += f"{prefix}📁 {key}\n"
                    result_str += format_settings(value, prefix + "  ")
                else:
                    # 불리언 값 처리
                    if isinstance(value, bool):
                        value_str = "✅ 활성화" if value else "❌ 비활성화"
                    else:
                        value_str = str(value)
                    
                    result_str += f"{prefix}🔹 {key}: {value_str}\n"
            return result_str
        
        formatted += format_settings(settings)
        
        # 설정 변경 안내 추가
        if result.get('updated', False):
            formatted += "\n✅ 설정이 성공적으로 업데이트되었습니다."
        
        return formatted
    
    def _format_summary(self, result: Dict) -> str:
        """
        요약 정보를 포맷팅합니다.
        
        Args:
            result: 요약 정보가 포함된 결과
            
        Returns:
            str: 포맷팅된 요약 정보
        """
        summary = result.get('summary', {})
        if not summary:
            return "📋 요약 정보가 없습니다."
        
        formatted = "📊 재정 요약\n\n"
        
        # 기간 정보 추가
        if 'period' in result:
            formatted += f"📅 기간: {result['period']}\n\n"
        
        # 수입 정보 추가
        if 'income' in summary:
            income = summary['income']
            formatted += "💰 수입\n"
            formatted += f"- 총액: {self._format_currency(income.get('total', 0))}\n"
            formatted += f"- 평균: {self._format_currency(income.get('average', 0))}\n"
            
            # 수입원별 정보 추가
            if 'by_source' in income and income['by_source']:
                formatted += "- 수입원별:\n"
                for source, amount in income['by_source'].items():
                    formatted += f"  - {source}: {self._format_currency(amount)}\n"
            
            formatted += "\n"
        
        # 지출 정보 추가
        if 'expense' in summary:
            expense = summary['expense']
            formatted += "💸 지출\n"
            formatted += f"- 총액: {self._format_currency(expense.get('total', 0))}\n"
            formatted += f"- 평균: {self._format_currency(expense.get('average', 0))}\n"
            
            # 카테고리별 정보 추가
            if 'by_category' in expense and expense['by_category']:
                formatted += "- 카테고리별 상위 항목:\n"
                sorted_categories = sorted(expense['by_category'].items(), key=lambda x: x[1], reverse=True)
                for category, amount in sorted_categories[:5]:
                    formatted += f"  - {category}: {self._format_currency(amount)}\n"
                
                if len(sorted_categories) > 5:
                    formatted += f"  - ... 외 {len(sorted_categories) - 5}개 카테고리\n"
            
            formatted += "\n"
        
        # 순 현금 흐름 추가
        if 'net_flow' in summary:
            net_flow = summary['net_flow']
            formatted += "💹 순 현금 흐름\n"
            
            if net_flow > 0:
                formatted += f"- 순이익: {self._format_currency(net_flow)} 흑자\n"
            elif net_flow < 0:
                formatted += f"- 순손실: {self._format_currency(abs(net_flow))} 적자\n"
            else:
                formatted += "- 수지 균형: 0원\n"
            
            # 수입 대비 지출 비율 추가
            if 'income' in summary and 'expense' in summary:
                income_total = summary['income'].get('total', 0)
                expense_total = summary['expense'].get('total', 0)
                
                if income_total > 0:
                    expense_ratio = (expense_total / income_total) * 100
                    formatted += f"- 수입 대비 지출 비율: {expense_ratio:.1f}%\n"
            
            formatted += "\n"
        
        # 인사이트 추가
        if 'insights' in summary:
            formatted += "💡 인사이트\n"
            for insight in summary['insights']:
                formatted += f"- {insight}\n"
        
        return formatted
    
    def _format_single_transaction(self, result: Dict) -> str:
        """
        단일 거래 정보를 포맷팅합니다.
        
        Args:
            result: 거래 정보가 포함된 결과
            
        Returns:
            str: 포맷팅된 거래 정보
        """
        transaction = result.get('transaction', {})
        if not transaction:
            return "📋 거래 정보가 없습니다."
        
        # 거래 유형 확인
        transaction_type = transaction.get('type', '')
        if transaction_type == 'income':
            formatted = "💰 수입 거래 정보\n\n"
        elif transaction_type == 'expense':
            formatted = "💸 지출 거래 정보\n\n"
        else:
            formatted = "📝 거래 정보\n\n"
        
        # 기본 정보 추가
        formatted += f"📅 날짜: {transaction.get('date', '날짜 없음')}\n"
        formatted += f"💲 금액: {self._format_currency(transaction.get('amount', 0))}\n"
        formatted += f"📝 설명: {transaction.get('description', '설명 없음')}\n"
        
        # 추가 정보 추가
        if 'category' in transaction and transaction['category']:
            formatted += f"🏷️ 카테고리: {transaction['category']}\n"
        
        if 'payment_method' in transaction and transaction['payment_method']:
            formatted += f"💳 결제 방식: {transaction['payment_method']}\n"
        
        if 'income_type' in transaction and transaction['income_type']:
            formatted += f"💼 수입 유형: {transaction['income_type']}\n"
        
        if 'memo' in transaction and transaction['memo']:
            formatted += f"📌 메모: {transaction['memo']}\n"
        
        # 상태 정보 추가
        if 'is_excluded' in transaction:
            formatted += f"🚫 분석 제외: {'예' if transaction['is_excluded'] else '아니오'}\n"
        
        # 작업 결과 메시지 추가
        if result.get('created', False):
            formatted += "\n✅ 거래가 성공적으로 추가되었습니다."
        elif result.get('updated', False):
            formatted += "\n✅ 거래가 성공적으로 업데이트되었습니다."
        
        return formatted
        
    def _format_templates(self, result: Dict) -> str:
        """
        거래 템플릿 목록을 포맷팅합니다.
        
        Args:
            result: 템플릿 목록이 포함된 결과
            
        Returns:
            str: 포맷팅된 템플릿 목록
        """
        templates = result.get('templates', [])
        if not templates:
            return "📋 저장된 템플릿이 없습니다."
        
        formatted = "📑 거래 템플릿 목록\n\n"
        
        # 템플릿 유형별로 그룹화
        template_types = {}
        for template in templates:
            template_type = template.get('type', '기타')
            if template_type not in template_types:
                template_types[template_type] = []
            template_types[template_type].append(template)
        
        # 유형별로 출력
        for template_type, type_templates in template_types.items():
            if template_type == 'expense':
                formatted += "💸 지출 템플릿\n"
            elif template_type == 'income':
                formatted += "💰 수입 템플릿\n"
            else:
                formatted += f"📝 {template_type} 템플릿\n"
            
            for i, template in enumerate(type_templates, 1):
                name = template.get('name', '이름 없음')
                description = template.get('description', '설명 없음')
                amount = template.get('amount', 0)
                category = template.get('category', '')
                
                formatted += f"{i}. {name}: {self._format_currency(amount)}"
                if category:
                    formatted += f" ({category})"
                formatted += f" - {description}\n"
            
            formatted += "\n"
        
        # 작업 결과 메시지 추가
        if result.get('created', False):
            formatted += "✅ 템플릿이 성공적으로 저장되었습니다."
        elif result.get('deleted', False):
            formatted += "✅ 템플릿이 성공적으로 삭제되었습니다."
        elif result.get('applied', False):
            formatted += "✅ 템플릿이 성공적으로 적용되었습니다."
        
        return formatted
    
    def _format_suggestions(self, result: Dict) -> str:
        """
        자동완성 제안을 포맷팅합니다.
        
        Args:
            result: 자동완성 제안이 포함된 결과
            
        Returns:
            str: 포맷팅된 자동완성 제안
        """
        suggestions = result.get('suggestions', [])
        if not suggestions:
            return "📋 자동완성 제안이 없습니다."
        
        formatted = "💡 자동완성 제안\n\n"
        
        for i, suggestion in enumerate(suggestions[:15], 1):
            if isinstance(suggestion, dict):
                text = suggestion.get('text', '')
                category = suggestion.get('category', '')
                count = suggestion.get('count', 0)
                
                formatted += f"{i}. {text}"
                if category:
                    formatted += f" ({category})"
                if count > 0:
                    formatted += f" - {count}회 사용됨"
                formatted += "\n"
            else:
                formatted += f"{i}. {suggestion}\n"
        
        if len(suggestions) > 15:
            formatted += f"\n... 외 {len(suggestions) - 15}개 제안이 더 있습니다."
        
        return formatted
    
    def _determine_transaction_type(self, transactions: List[Dict]) -> str:
        """
        거래 목록의 유형을 판단합니다.
        
        Args:
            transactions: 거래 목록
            
        Returns:
            str: 거래 유형 ('income', 'expense', 'mixed')
        """
        if not transactions:
            return "unknown"
        
        income_count = 0
        expense_count = 0
        
        for tx in transactions:
            tx_type = tx.get('type', '')
            if tx_type == 'income':
                income_count += 1
            elif tx_type == 'expense':
                expense_count += 1
        
        if income_count > 0 and expense_count == 0:
            return "income"
        elif expense_count > 0 and income_count == 0:
            return "expense"
        else:
            return "mixed"
    
    def _format_currency(self, amount: Union[int, float]) -> str:
        """
        금액을 통화 형식으로 포맷팅합니다.
        
        Args:
            amount: 금액
            
        Returns:
            str: 포맷팅된 금액
        """
        # 천 단위 구분자 추가
        formatted = f"{int(amount):,}{self.decimal_separator}{int(amount * 100) % 100:02d}"
        
        # 통화 기호 추가
        if self.currency_symbol:
            formatted += f" {self.currency_symbol}"
        
        return formatted
    
    def extract_insights(self, data: Dict) -> List[str]:
        """
        데이터에서 핵심 인사이트를 추출합니다.
        
        Args:
            data: 분석 데이터
            
        Returns:
            List[str]: 추출된 인사이트 목록
        """
        insights = []
        
        # 분석 유형에 따라 인사이트 추출
        if 'analysis' in data:
            analysis = data['analysis']
            analysis_type = data.get('type', '')
            
            if analysis_type == 'expense':
                # 지출 분석 인사이트
                insights = self._extract_expense_insights(analysis, data)
            elif analysis_type == 'income':
                # 수입 분석 인사이트
                insights = self._extract_income_insights(analysis, data)
            elif analysis_type == 'trend':
                # 추세 분석 인사이트
                insights = self._extract_trend_insights(analysis, data)
        
        # 비교 분석 인사이트
        elif 'comparison' in data:
            insights = self._extract_comparison_insights(data['comparison'], data)
        
        # 요약 정보 인사이트
        elif 'summary' in data:
            insights = self._extract_summary_insights(data['summary'], data)
        
        return insights
    
    def _extract_expense_insights(self, analysis: Dict, data: Dict) -> List[str]:
        """
        지출 분석 데이터에서 인사이트를 추출합니다.
        
        Args:
            analysis: 분석 데이터
            data: 전체 데이터
            
        Returns:
            List[str]: 추출된 인사이트 목록
        """
        insights = []
        
        # 상위 지출 카테고리 확인
        if 'details' in analysis and isinstance(analysis['details'], list) and len(analysis['details']) > 0:
            # 카테고리별 지출 정보 추출
            categories = []
            for item in analysis['details']:
                if isinstance(item, dict) and 'name' in item and 'value' in item:
                    categories.append((item['name'], item['value'], item.get('percentage', 0)))
            
            # 상위 카테고리 인사이트
            if categories:
                categories.sort(key=lambda x: x[1], reverse=True)
                top_category = categories[0]
                insights.append(f"가장 많은 지출은 '{top_category[0]}' 카테고리로, 전체의 {top_category[2]:.1f}%를 차지합니다.")
                
                # 상위 3개 카테고리가 차지하는 비율
                if len(categories) >= 3:
                    top3_total = sum(cat[1] for cat in categories[:3])
                    top3_percentage = sum(cat[2] for cat in categories[:3])
                    insights.append(f"상위 3개 카테고리('{categories[0][0]}', '{categories[1][0]}', '{categories[2][0]}')가 전체 지출의 {top3_percentage:.1f}%를 차지합니다.")
        
        # 평균 및 총액 정보
        if 'total' in data and 'average' in data:
            total = data['total']
            average = data['average']
            period = data.get('period', '')
            
            if period:
                insights.append(f"{period} 동안 총 {self._format_currency(total)}를 지출했으며, 평균 지출액은 {self._format_currency(average)}입니다.")
        
        # 최대/최소 지출 정보
        if 'max' in data and 'min' in data:
            max_amount = data['max']
            min_amount = data['min']
            
            insights.append(f"가장 큰 지출은 {self._format_currency(max_amount)}, 가장 작은 지출은 {self._format_currency(min_amount)}입니다.")
        
        return insights
        
    def _extract_income_insights(self, analysis: Dict, data: Dict) -> List[str]:
        """
        수입 분석 데이터에서 인사이트를 추출합니다.
        
        Args:
            analysis: 분석 데이터
            data: 전체 데이터
            
        Returns:
            List[str]: 추출된 인사이트 목록
        """
        insights = []
        
        # 수입원별 정보 확인
        if 'details' in analysis and isinstance(analysis['details'], list) and len(analysis['details']) > 0:
            # 수입원별 정보 추출
            sources = []
            for item in analysis['details']:
                if isinstance(item, dict) and 'name' in item and 'value' in item:
                    sources.append((item['name'], item['value'], item.get('percentage', 0)))
            
            # 주요 수입원 인사이트
            if sources:
                sources.sort(key=lambda x: x[1], reverse=True)
                top_source = sources[0]
                insights.append(f"주요 수입원은 '{top_source[0]}'로, 전체 수입의 {top_source[2]:.1f}%를 차지합니다.")
                
                # 수입원 다양성 인사이트
                if len(sources) > 1:
                    insights.append(f"총 {len(sources)}개의 서로 다른 수입원이 있습니다.")
        
        # 평균 및 총액 정보
        if 'total' in data and 'average' in data:
            total = data['total']
            average = data['average']
            period = data.get('period', '')
            
            if period:
                insights.append(f"{period} 동안 총 {self._format_currency(total)}의 수입이 있었으며, 평균 수입액은 {self._format_currency(average)}입니다.")
        
        # 정기 수입 패턴 정보
        if 'patterns' in analysis:
            patterns = analysis['patterns']
            if isinstance(patterns, list) and patterns:
                insights.append(f"{len(patterns)}개의 정기적인 수입 패턴이 발견되었습니다.")
                
                # 가장 큰 정기 수입 패턴
                if len(patterns) > 0 and isinstance(patterns[0], dict):
                    top_pattern = max(patterns, key=lambda x: x.get('amount', 0))
                    pattern_desc = top_pattern.get('description', '정기 수입')
                    pattern_amount = top_pattern.get('amount', 0)
                    pattern_frequency = top_pattern.get('frequency', '매월')
                    
                    insights.append(f"가장 큰 정기 수입은 '{pattern_desc}'로, {pattern_frequency} {self._format_currency(pattern_amount)}입니다.")
        
        return insights
    
    def _extract_trend_insights(self, analysis: Dict, data: Dict) -> List[str]:
        """
        추세 분석 데이터에서 인사이트를 추출합니다.
        
        Args:
            analysis: 분석 데이터
            data: 전체 데이터
            
        Returns:
            List[str]: 추출된 인사이트 목록
        """
        insights = []
        
        # 추세 데이터 확인
        if 'trend_data' in analysis and isinstance(analysis['trend_data'], list) and len(analysis['trend_data']) > 1:
            trend_data = analysis['trend_data']
            
            # 증가/감소 추세 확인
            first_value = trend_data[0].get('value', 0) if isinstance(trend_data[0], dict) else 0
            last_value = trend_data[-1].get('value', 0) if isinstance(trend_data[-1], dict) else 0
            
            if last_value > first_value:
                change_pct = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
                insights.append(f"전체 기간 동안 {change_pct:.1f}% 증가하는 추세를 보입니다.")
            elif last_value < first_value:
                change_pct = ((first_value - last_value) / first_value * 100) if first_value > 0 else 0
                insights.append(f"전체 기간 동안 {change_pct:.1f}% 감소하는 추세를 보입니다.")
            else:
                insights.append("전체 기간 동안 큰 변화 없이 일정한 추세를 보입니다.")
            
            # 최대/최소 시점 확인
            max_point = max(trend_data, key=lambda x: x.get('value', 0) if isinstance(x, dict) else 0)
            min_point = min(trend_data, key=lambda x: x.get('value', 0) if isinstance(x, dict) else 0)
            
            if isinstance(max_point, dict) and isinstance(min_point, dict):
                max_period = max_point.get('period', '')
                min_period = min_point.get('period', '')
                
                if max_period and min_period:
                    insights.append(f"가장 높은 값은 {max_period}에 {self._format_currency(max_point.get('value', 0))}, 가장 낮은 값은 {min_period}에 {self._format_currency(min_point.get('value', 0))}입니다.")
        
        # 계절성 패턴 확인
        if 'seasonality' in analysis:
            seasonality = analysis['seasonality']
            if seasonality:
                insights.append(f"데이터에서 {seasonality}의 계절성 패턴이 발견되었습니다.")
        
        # 이상치 확인
        if 'anomalies' in analysis and isinstance(analysis['anomalies'], list):
            anomalies = analysis['anomalies']
            if anomalies:
                insights.append(f"{len(anomalies)}개의 이상치가 발견되었습니다.")
        
        return insights
    
    def _extract_comparison_insights(self, comparison: Dict, data: Dict) -> List[str]:
        """
        비교 분석 데이터에서 인사이트를 추출합니다.
        
        Args:
            comparison: 비교 분석 데이터
            data: 전체 데이터
            
        Returns:
            List[str]: 추출된 인사이트 목록
        """
        insights = []
        
        # 전체 변화 확인
        if 'total_change' in comparison and 'total_change_percentage' in comparison:
            change = comparison['total_change']
            change_percentage = comparison['total_change_percentage']
            
            period1 = data.get('period1', '이전 기간')
            period2 = data.get('period2', '현재 기간')
            
            if change > 0:
                insights.append(f"{period1}에 비해 {period2}에 {change_percentage:.1f}% 증가했습니다.")
            elif change < 0:
                insights.append(f"{period1}에 비해 {period2}에 {abs(change_percentage):.1f}% 감소했습니다.")
            else:
                insights.append(f"{period1}과 {period2} 사이에 변화가 없습니다.")
        
        # 주요 변화 항목 확인
        if 'changes' in comparison and isinstance(comparison['changes'], list) and len(comparison['changes']) > 0:
            changes = comparison['changes']
            
            # 가장 큰 증가/감소 항목 찾기
            increases = [item for item in changes if isinstance(item, dict) and item.get('change', 0) > 0]
            decreases = [item for item in changes if isinstance(item, dict) and item.get('change', 0) < 0]
            
            if increases:
                increases.sort(key=lambda x: x.get('change', 0), reverse=True)
                top_increase = increases[0]
                insights.append(f"가장 큰 증가는 '{top_increase.get('name', '항목')}'로, {top_increase.get('change_percentage', 0):.1f}% 증가했습니다.")
            
            if decreases:
                decreases.sort(key=lambda x: x.get('change', 0))
                top_decrease = decreases[0]
                insights.append(f"가장 큰 감소는 '{top_decrease.get('name', '항목')}'로, {abs(top_decrease.get('change_percentage', 0)):.1f}% 감소했습니다.")
            
            # 새로 추가된/사라진 항목 확인
            new_items = [item for item in changes if isinstance(item, dict) and item.get('value1', 0) == 0 and item.get('value2', 0) > 0]
            removed_items = [item for item in changes if isinstance(item, dict) and item.get('value1', 0) > 0 and item.get('value2', 0) == 0]
            
            if new_items:
                insights.append(f"{len(new_items)}개의 새로운 항목이 추가되었습니다.")
            
            if removed_items:
                insights.append(f"{len(removed_items)}개의 항목이 사라졌습니다.")
        
        return insights
    
    def _extract_summary_insights(self, summary: Dict, data: Dict) -> List[str]:
        """
        요약 데이터에서 인사이트를 추출합니다.
        
        Args:
            summary: 요약 데이터
            data: 전체 데이터
            
        Returns:
            List[str]: 추출된 인사이트 목록
        """
        insights = []
        
        # 수입-지출 비교
        if 'income' in summary and 'expense' in summary:
            income = summary['income'].get('total', 0) if isinstance(summary['income'], dict) else 0
            expense = summary['expense'].get('total', 0) if isinstance(summary['expense'], dict) else 0
            
            if income > 0 and expense > 0:
                expense_ratio = (expense / income) * 100
                
                if expense_ratio < 80:
                    insights.append(f"수입의 {expense_ratio:.1f}%만 지출하여 재정 상태가 양호합니다.")
                elif expense_ratio < 100:
                    insights.append(f"수입의 {expense_ratio:.1f}%를 지출하고 있습니다.")
                else:
                    insights.append(f"수입보다 지출이 많아 재정 관리에 주의가 필요합니다. (수입 대비 지출 비율: {expense_ratio:.1f}%)")
        
        # 순 현금 흐름 확인
        if 'net_flow' in summary:
            net_flow = summary['net_flow']
            period = data.get('period', '')
            
            if net_flow > 0:
                insights.append(f"{period}동안 {self._format_currency(net_flow)}의 순이익이 발생했습니다.")
            elif net_flow < 0:
                insights.append(f"{period}동안 {self._format_currency(abs(net_flow))}의 순손실이 발생했습니다.")
            else:
                insights.append(f"{period}동안 수입과 지출이 정확히 균형을 이루었습니다.")
        
        # 주요 지출 카테고리 확인
        if 'expense' in summary and isinstance(summary['expense'], dict) and 'by_category' in summary['expense']:
            categories = summary['expense']['by_category']
            if categories:
                sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                top_category = sorted_categories[0]
                
                total_expense = summary['expense'].get('total', 0)
                if total_expense > 0:
                    top_percentage = (top_category[1] / total_expense) * 100
                    insights.append(f"가장 많은 지출은 '{top_category[0]}' 카테고리로, 전체 지출의 {top_percentage:.1f}%를 차지합니다.")
        
        # 주요 수입원 확인
        if 'income' in summary and isinstance(summary['income'], dict) and 'by_source' in summary['income']:
            sources = summary['income']['by_source']
            if sources:
                sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
                top_source = sorted_sources[0]
                
                total_income = summary['income'].get('total', 0)
                if total_income > 0:
                    top_percentage = (top_source[1] / total_income) * 100
                    insights.append(f"주요 수입원은 '{top_source[0]}'로, 전체 수입의 {top_percentage:.1f}%를 차지합니다.")
        
        return insights


# 싱글톤 인스턴스 생성
formatter = ResponseFormatter()

def format_response(result: Any) -> str:
    """
    도구 실행 결과를 사용자 친화적인 응답으로 포맷팅합니다.
    
    Args:
        result: 도구 실행 결과
        
    Returns:
        str: 포맷팅된 응답
    """
    return formatter.format_response(result)

def extract_insights(data: Dict) -> List[str]:
    """
    데이터에서 핵심 인사이트를 추출합니다.
    
    Args:
        data: 분석 데이터
        
    Returns:
        List[str]: 추출된 인사이트 목록
    """
    return formatter.extract_insights(data)

def handle_agent_error(error: Exception) -> str:
    """
    에이전트 오류를 사용자 친화적 메시지로 변환합니다.
    
    Args:
        error: 발생한 예외
        
    Returns:
        str: 사용자 친화적 오류 메시지
    """
    if isinstance(error, Exception):
        error_type = type(error).__name__
        error_message = str(error)
        
        # 오류 유형별 메시지 생성
        if "ValidationError" in error_type:
            return f"⚠️ 입력 정보가 올바르지 않습니다: {error_message}"
        
        elif "DataIngestionError" in error_type:
            return f"⚠️ 데이터 처리 중 문제가 발생했습니다: {error_message}"
        
        elif "ClassificationError" in error_type:
            return f"⚠️ 거래 분류 중 문제가 발생했습니다: {error_message}"
        
        elif "AnalysisError" in error_type:
            return f"⚠️ 데이터 분석 중 문제가 발생했습니다: {error_message}"
        
        elif "DatabaseError" in error_type:
            return f"⚠️ 데이터베이스 작업 중 문제가 발생했습니다: {error_message}\n\n💡 데이터베이스 연결을 확인해보세요."
        
        elif "ConfigError" in error_type:
            return f"⚠️ 시스템 설정 관련 문제가 발생했습니다: {error_message}"
        
        elif "BackupError" in error_type:
            return f"⚠️ 데이터 백업 또는 복원 중 문제가 발생했습니다: {error_message}"
        
        elif "BlockedPromptException" in error_type:
            return "⚠️ 죄송합니다. 요청하신 내용은 안전 정책에 따라 처리할 수 없습니다."
        
        elif "StopCandidateException" in error_type:
            return "⚠️ 죄송합니다. 응답 생성 중 문제가 발생했습니다. 다른 방식으로 질문해 주세요."
        
        elif "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            return f"⚠️ 필요한 모듈을 불러올 수 없습니다: {error_message}\n\n💡 필요한 패키지가 설치되어 있는지 확인해주세요."
        
        else:
            return f"⚠️ 처리 중 오류가 발생했습니다: {error_message}"
    
    return f"⚠️ 알 수 없는 오류가 발생했습니다: {error}"