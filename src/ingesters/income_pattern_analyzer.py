# -*- coding: utf-8 -*-
"""
IncomePatternAnalyzer 클래스 정의

수입 거래의 패턴을 분석하고 정기성을 식별하는 기능을 제공합니다.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import statistics
import calendar
import math
import json
from pathlib import Path

# 로깅 설정
logger = logging.getLogger(__name__)

class IncomePatternAnalyzer:
    """
    수입 패턴 분석기
    
    수입 거래의 패턴을 분석하고 정기성을 식별하는 기능을 제공합니다.
    정기 수입 예측, 수입 트렌드 분석 등을 수행합니다.
    """
    
    def __init__(self, history_file: Optional[str] = None):
        """
        수입 패턴 분석기 초기화
        
        Args:
            history_file: 수입 내역 기록 파일 경로 (선택)
        """
        # 수입 내역 기록
        self._income_history = {}
        
        # 정기 수입 패턴
        self.regular_patterns = {}
        
        # 수입 트렌드
        self.income_trends = {}
        
        # 내역 파일 경로
        self.history_file = history_file
        
        # 내역 파일이 있으면 로드
        if history_file:
            self.load_history(history_file)
    
    def load_history(self, history_file: str) -> None:
        """
        수입 내역 기록을 파일에서 로드합니다.
        
        Args:
            history_file: 수입 내역 기록 파일 경로
        """
        try:
            path = Path(history_file)
            if not path.exists():
                logger.warning(f"수입 내역 기록 파일이 존재하지 않습니다: {history_file}")
                return
            
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 날짜 문자열을 date 객체로 변환
            if 'income_history' in data:
                history = data['income_history']
                for category, transactions in history.items():
                    if category not in self._income_history:
                        self._income_history[category] = []
                    
                    for transaction in transactions:
                        if 'date' in transaction and isinstance(transaction['date'], str):
                            transaction['date'] = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
                        
                        self._income_history[category].append(transaction)
            
            # 정기 수입 패턴 로드
            if 'regular_patterns' in data:
                self.regular_patterns = data['regular_patterns']
            
            # 수입 트렌드 로드
            if 'income_trends' in data:
                self.income_trends = data['income_trends']
            
            logger.info(f"수입 내역 기록을 로드했습니다: {len(self._income_history)} 카테고리")
            
        except Exception as e:
            logger.error(f"수입 내역 기록 로드 중 오류 발생: {e}")
    
    def save_history(self, history_file: Optional[str] = None) -> None:
        """
        수입 내역 기록을 파일에 저장합니다.
        
        Args:
            history_file: 수입 내역 기록 파일 경로 (선택)
        """
        try:
            file_path = history_file or self.history_file
            if not file_path:
                logger.warning("저장할 파일 경로가 지정되지 않았습니다.")
                return
            
            # 날짜 객체를 문자열로 변환
            serializable_history = {}
            for category, transactions in self._income_history.items():
                serializable_history[category] = []
                
                for transaction in transactions:
                    serializable_transaction = transaction.copy()
                    if 'date' in serializable_transaction and isinstance(serializable_transaction['date'], date):
                        serializable_transaction['date'] = serializable_transaction['date'].strftime('%Y-%m-%d')
                    
                    serializable_history[category].append(serializable_transaction)
            
            data = {
                'income_history': serializable_history,
                'regular_patterns': self.regular_patterns,
                'income_trends': self.income_trends
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"수입 내역 기록을 저장했습니다: {file_path}")
            
        except Exception as e:
            logger.error(f"수입 내역 기록 저장 중 오류 발생: {e}")
    
    def add_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        거래를 수입 내역에 추가합니다.
        
        Args:
            transaction: 거래 데이터
        """
        category = transaction.get('category', '기타수입')
        
        if category not in self._income_history:
            self._income_history[category] = []
        
        # 날짜 처리
        if 'transaction_date' in transaction:
            if isinstance(transaction['transaction_date'], str):
                transaction_date = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d').date()
            else:
                transaction_date = transaction['transaction_date']
        else:
            transaction_date = date.today()
        
        # 금액 처리
        if 'amount' in transaction:
            if isinstance(transaction['amount'], Decimal):
                amount = float(transaction['amount'])
            else:
                amount = float(transaction['amount'])
        else:
            amount = 0.0
        
        # 내역에 추가
        self._income_history[category].append({
            'date': transaction_date,
            'amount': amount,
            'description': transaction.get('description', ''),
            'transaction_id': transaction.get('transaction_id', '')
        })
        
        logger.debug(f"거래를 수입 내역에 추가했습니다: {category}, {transaction_date}, {amount}")
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """
        수입 패턴을 분석합니다.
        
        Returns:
            Dict[str, Any]: 분석 결과
        """
        logger.info("수입 패턴 분석 시작")
        
        # 카테고리별 정기 패턴 분석
        regular_patterns = {}
        
        for category, transactions in self._income_history.items():
            if len(transactions) < 2:
                continue
            
            # 날짜순 정렬
            sorted_transactions = sorted(transactions, key=lambda x: x['date'])
            
            # 날짜 간격 계산
            intervals = []
            for i in range(1, len(sorted_transactions)):
                interval = (sorted_transactions[i]['date'] - sorted_transactions[i-1]['date']).days
                intervals.append(interval)
            
            # 간격이 일정한지 확인
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                
                # 표준편차 계산
                if len(intervals) > 1:
                    std_dev = statistics.stdev(intervals)
                else:
                    std_dev = 0
                
                # 변동 계수 (표준편차/평균) - 값이 작을수록 규칙적
                cv = std_dev / avg_interval if avg_interval > 0 else float('inf')
                
                # 정기성 판단 (변동 계수가 0.2 이하면 정기적)
                is_regular = cv <= 0.2 and avg_interval > 0
                
                if is_regular:
                    # 주기 유형 결정
                    period_type = self._determine_period_type(avg_interval)
                    
                    # 금액 일관성 확인
                    amounts = [t['amount'] for t in sorted_transactions]
                    avg_amount = sum(amounts) / len(amounts)
                    
                    if len(amounts) > 1:
                        amount_std_dev = statistics.stdev(amounts)
                        amount_cv = amount_std_dev / avg_amount if avg_amount > 0 else float('inf')
                    else:
                        amount_std_dev = 0
                        amount_cv = 0
                    
                    # 금액 일관성 (변동 계수가 0.1 이하면 일관적)
                    amount_consistent = amount_cv <= 0.1
                    
                    # 다음 예상 날짜 계산
                    last_date = sorted_transactions[-1]['date']
                    next_date = last_date + timedelta(days=int(round(avg_interval)))
                    
                    # 정기 패턴 저장
                    regular_patterns[category] = {
                        'avg_interval': avg_interval,
                        'std_dev': std_dev,
                        'cv': cv,
                        'period_type': period_type,
                        'avg_amount': avg_amount,
                        'amount_std_dev': amount_std_dev,
                        'amount_consistent': amount_consistent,
                        'last_date': last_date.strftime('%Y-%m-%d'),
                        'next_expected_date': next_date.strftime('%Y-%m-%d'),
                        'confidence': self._calculate_confidence(len(intervals), cv, amount_cv)
                    }
                    
                    logger.info(f"정기 수입 패턴 발견: {category}, 주기: {period_type}, 평균 간격: {avg_interval:.1f}일, 다음 예상: {next_date}")
        
        # 정기 패턴 업데이트
        self.regular_patterns = regular_patterns
        
        # 월별 수입 트렌드 분석
        self.income_trends = self._analyze_monthly_trends()
        
        # 결과 생성
        result = {
            'regular_patterns': regular_patterns,
            'income_trends': self.income_trends,
            'analysis_date': date.today().strftime('%Y-%m-%d')
        }
        
        return result
    
    def _determine_period_type(self, avg_interval: float) -> str:
        """
        평균 간격을 기반으로 주기 유형을 결정합니다.
        
        Args:
            avg_interval: 평균 간격 (일)
            
        Returns:
            str: 주기 유형 (daily, weekly, biweekly, monthly, quarterly, yearly)
        """
        if avg_interval < 2:
            return 'daily'
        elif 6 <= avg_interval <= 8:
            return 'weekly'
        elif 13 <= avg_interval <= 15:
            return 'biweekly'
        elif 28 <= avg_interval <= 31:
            return 'monthly'
        elif 89 <= avg_interval <= 92:
            return 'quarterly'
        elif 364 <= avg_interval <= 366:
            return 'yearly'
        else:
            return f'custom_{int(round(avg_interval))}_days'
    
    def _calculate_confidence(self, sample_size: int, interval_cv: float, amount_cv: float) -> float:
        """
        패턴 신뢰도를 계산합니다.
        
        Args:
            sample_size: 샘플 크기 (거래 수 - 1)
            interval_cv: 간격의 변동 계수
            amount_cv: 금액의 변동 계수
            
        Returns:
            float: 신뢰도 (0.0 ~ 1.0)
        """
        # 샘플 크기 가중치 (최대 0.4)
        sample_weight = min(0.4, (sample_size - 1) * 0.1)
        
        # 간격 일관성 가중치 (최대 0.4)
        interval_weight = 0.4 * max(0, 1 - 5 * interval_cv)
        
        # 금액 일관성 가중치 (최대 0.2)
        amount_weight = 0.2 * max(0, 1 - 10 * amount_cv)
        
        # 총 신뢰도
        confidence = sample_weight + interval_weight + amount_weight
        
        return round(min(1.0, max(0.0, confidence)), 2)
    
    def _analyze_monthly_trends(self) -> Dict[str, Any]:
        """
        월별 수입 트렌드를 분석합니다.
        
        Returns:
            Dict[str, Any]: 월별 트렌드 데이터
        """
        # 월별 수입 집계
        monthly_totals = {}
        monthly_by_category = {}
        
        for category, transactions in self._income_history.items():
            for transaction in transactions:
                transaction_date = transaction['date']
                amount = transaction['amount']
                
                # 월 키 생성 (YYYY-MM)
                month_key = transaction_date.strftime('%Y-%m')
                
                # 월별 총액 업데이트
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = 0
                monthly_totals[month_key] += amount
                
                # 카테고리별 월별 금액 업데이트
                if month_key not in monthly_by_category:
                    monthly_by_category[month_key] = {}
                
                if category not in monthly_by_category[month_key]:
                    monthly_by_category[month_key][category] = 0
                monthly_by_category[month_key][category] += amount
        
        # 월별 데이터 정렬
        sorted_months = sorted(monthly_totals.keys())
        
        # 월별 총액 시계열
        monthly_series = [
            {'month': month, 'total': monthly_totals[month]}
            for month in sorted_months
        ]
        
        # 카테고리별 월별 시계열
        category_series = {}
        all_categories = set()
        
        for month_data in monthly_by_category.values():
            all_categories.update(month_data.keys())
        
        for category in all_categories:
            category_series[category] = [
                {
                    'month': month,
                    'amount': monthly_by_category[month].get(category, 0)
                }
                for month in sorted_months
            ]
        
        # 성장률 계산
        growth_rates = []
        
        for i in range(1, len(sorted_months)):
            prev_month = sorted_months[i-1]
            curr_month = sorted_months[i]
            
            prev_total = monthly_totals[prev_month]
            curr_total = monthly_totals[curr_month]
            
            if prev_total > 0:
                growth_rate = (curr_total - prev_total) / prev_total
            else:
                growth_rate = float('inf') if curr_total > 0 else 0
            
            growth_rates.append({
                'month': curr_month,
                'rate': growth_rate
            })
        
        # 결과 생성
        return {
            'monthly_totals': monthly_series,
            'category_series': category_series,
            'growth_rates': growth_rates
        }
    
    def predict_future_income(self, months_ahead: int = 3) -> Dict[str, Any]:
        """
        미래 수입을 예측합니다.
        
        Args:
            months_ahead: 예측할 개월 수
            
        Returns:
            Dict[str, Any]: 예측 결과
        """
        if not self.regular_patterns:
            self.analyze_patterns()
        
        today = date.today()
        predictions = []
        
        # 정기 수입 예측
        for category, pattern in self.regular_patterns.items():
            # 신뢰도가 낮으면 건너뜀
            if pattern.get('confidence', 0) < 0.5:
                continue
            
            last_date = datetime.strptime(pattern['last_date'], '%Y-%m-%d').date()
            avg_interval = pattern['avg_interval']
            avg_amount = pattern['avg_amount']
            period_type = pattern['period_type']
            
            # 예측 기간 동안의 수입 계산
            current_date = last_date
            
            for _ in range(months_ahead * 2):  # 충분한 여유를 두고 계산
                # 다음 예상 날짜 계산
                if period_type == 'monthly':
                    # 월별 수입은 날짜를 유지하면서 월만 증가
                    next_month = current_date.month + 1
                    next_year = current_date.year
                    
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    
                    # 해당 월의 마지막 날짜 확인
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    next_day = min(current_date.day, last_day)
                    
                    next_date = date(next_year, next_month, next_day)
                else:
                    # 기타 주기는 일수 기반으로 계산
                    next_date = current_date + timedelta(days=int(round(avg_interval)))
                
                # 예측 기간 내에 있는 경우만 추가
                if next_date <= today + timedelta(days=months_ahead * 30):
                    predictions.append({
                        'category': category,
                        'date': next_date.strftime('%Y-%m-%d'),
                        'amount': avg_amount,
                        'confidence': pattern.get('confidence', 0.5),
                        'period_type': period_type
                    })
                
                current_date = next_date
        
        # 날짜순 정렬
        predictions.sort(key=lambda x: x['date'])
        
        # 월별 예상 총액 계산
        monthly_totals = {}
        
        for prediction in predictions:
            date_obj = datetime.strptime(prediction['date'], '%Y-%m-%d').date()
            month_key = date_obj.strftime('%Y-%m')
            
            if month_key not in monthly_totals:
                monthly_totals[month_key] = 0
            
            monthly_totals[month_key] += prediction['amount']
        
        # 결과 생성
        result = {
            'predictions': predictions,
            'monthly_totals': [
                {'month': month, 'total': total}
                for month, total in sorted(monthly_totals.items())
            ]
        }
        
        return result
    
    def get_regular_income_summary(self) -> Dict[str, Any]:
        """
        정기 수입 요약 정보를 반환합니다.
        
        Returns:
            Dict[str, Any]: 정기 수입 요약
        """
        if not self.regular_patterns:
            self.analyze_patterns()
        
        # 정기 수입 총액
        total_regular_income = sum(
            pattern['avg_amount']
            for pattern in self.regular_patterns.values()
            if pattern.get('confidence', 0) >= 0.5
        )
        
        # 월 환산 정기 수입
        monthly_equivalent = 0
        
        for category, pattern in self.regular_patterns.items():
            if pattern.get('confidence', 0) < 0.5:
                continue
            
            avg_amount = pattern['avg_amount']
            period_type = pattern['period_type']
            
            # 주기별 월 환산 계수
            if period_type == 'daily':
                factor = 30
            elif period_type == 'weekly':
                factor = 4.33
            elif period_type == 'biweekly':
                factor = 2.17
            elif period_type == 'monthly':
                factor = 1
            elif period_type == 'quarterly':
                factor = 1/3
            elif period_type == 'yearly':
                factor = 1/12
            elif period_type.startswith('custom_'):
                days = int(period_type.split('_')[1])
                factor = 30 / days
            else:
                factor = 1
            
            monthly_equivalent += avg_amount * factor
        
        # 결과 생성
        result = {
            'total_regular_income': total_regular_income,
            'monthly_equivalent': monthly_equivalent,
            'regular_income_count': len(self.regular_patterns),
            'high_confidence_count': sum(
                1 for pattern in self.regular_patterns.values()
                if pattern.get('confidence', 0) >= 0.7
            ),
            'by_period_type': {}
        }
        
        # 주기별 통계
        period_stats = {}
        
        for category, pattern in self.regular_patterns.items():
            period_type = pattern['period_type']
            
            if period_type not in period_stats:
                period_stats[period_type] = {
                    'count': 0,
                    'total': 0
                }
            
            period_stats[period_type]['count'] += 1
            period_stats[period_type]['total'] += pattern['avg_amount']
        
        result['by_period_type'] = period_stats
        
        return result