#!/usr/bin/env python3
"""
스펙 상태 업데이트 및 대시보드 생성 스크립트
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path

def parse_spec_metadata(file_path):
    """스펙 파일에서 메타데이터 추출"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # YAML front matter 추출
    yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if yaml_match:
        try:
            metadata = yaml.safe_load(yaml_match.group(1))
            return metadata
        except yaml.YAMLError:
            return None
    return None

def get_status_emoji(status):
    """상태에 따른 이모지 반환"""
    emoji_map = {
        'IMPLEMENTED': '✅',
        'IN_PROGRESS': '🔄',
        'DRAFT': '📝',
        'PAUSED': '⏸️',
        'ARCHIVED': '🗄️',
        'UNKNOWN': '❓'
    }
    return emoji_map.get(status, '❓')

def update_dashboard():
    """대시보드 업데이트"""
    specs_dir = Path('.kiro/specs')
    specs = []
    
    for spec_dir in specs_dir.iterdir():
        if spec_dir.is_dir() and spec_dir.name not in ['__pycache__']:
            req_file = spec_dir / 'requirements.md'
            if req_file.exists():
                metadata = parse_spec_metadata(req_file)
                if metadata:
                    specs.append({
                        'name': spec_dir.name,
                        'path': f'./{spec_dir.name}/',
                        **metadata
                    })
    
    # 대시보드 생성
    dashboard_content = generate_dashboard_content(specs)
    
    with open(specs_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(dashboard_content)
    
    print(f"대시보드가 업데이트되었습니다. ({len(specs)}개 스펙)")

def generate_dashboard_content(specs):
    """대시보드 내용 생성"""
    # 여기에 대시보드 템플릿 로직 구현
    # 현재는 간단한 예시만 제공
    return "# 스펙 상태 대시보드\n\n업데이트됨: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    update_dashboard()