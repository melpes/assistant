# -*- coding: utf-8 -*-
"""
데이터 수집 모듈 패키지

다양한 소스로부터 거래 데이터를 수집하는 플러그인 기반 아키텍처를 제공합니다.
"""

from .base_ingester import BaseIngester
from .ingester_factory import IngesterFactory
from .toss_bank_card_ingester import TossBankCardIngester
from .toss_bank_account_ingester import TossBankAccountIngester
from .manual_ingester import ManualIngester

__all__ = [
    'BaseIngester',
    'IngesterFactory',
    'TossBankCardIngester',
    'TossBankAccountIngester',
    'ManualIngester'
]