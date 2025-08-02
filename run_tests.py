#!/usr/bin/env python3
"""
캘린더 서비스 테스트 실행 스크립트

이 스크립트는 다양한 테스트 시나리오를 실행할 수 있는 편의 기능을 제공합니다.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """명령어 실행"""
    if description:
        print(f"\n{'='*60}")
        print(f"실행 중: {description}")
        print(f"명령어: {' '.join(cmd)}")
        print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"오류 발생: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="캘린더 서비스 테스트 실행")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="unit",
        help="실행할 테스트 유형 (기본값: unit)"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="코드 커버리지 측정"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세 출력"
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="병렬 실행 프로세스 수"
    )
    parser.add_argument(
        "--module",
        help="특정 모듈만 테스트 (예: test_models, test_auth)"
    )
    parser.add_argument(
        "--function",
        help="특정 함수만 테스트 (예: test_calendar_event_creation)"
    )
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="이전에 실패한 테스트만 다시 실행"
    )
    parser.add_argument(
        "--ignore-failures",
        action="store_true",
        help="실패한 테스트가 있어도 계속 진행"
    )
    
    args = parser.parse_args()
    
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 기본 pytest 명령어
    cmd = ["python", "-m", "pytest"]
    
    # 테스트 유형에 따른 옵션 추가
    if args.type == "unit":
        cmd.extend(["-m", "not integration"])
        description = "단위 테스트 실행"
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
        description = "통합 테스트 실행 (실제 API 필요)"
    else:  # all
        description = "모든 테스트 실행"
    
    # 특정 모듈 테스트
    if args.module:
        cmd.append(f"tests/calendar/test_{args.module}.py")
        description += f" (모듈: {args.module})"
    
    # 특정 함수 테스트
    if args.function:
        if args.module:
            cmd[-1] += f"::{args.function}"
        else:
            cmd.extend(["-k", args.function])
        description += f" (함수: {args.function})"
    
    # 커버리지 옵션
    if args.coverage:
        cmd.extend([
            "--cov=src/calendar",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])
        description += " (커버리지 포함)"
    
    # 상세 출력
    if args.verbose:
        cmd.append("-vv")
    
    # 병렬 실행
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
        description += f" (병렬: {args.parallel})"
    
    # 실패한 테스트만 실행
    if args.failed_only:
        cmd.append("--lf")
        description += " (실패한 테스트만)"
    
    # 실패 무시
    if args.ignore_failures:
        cmd.append("--tb=no")
        description += " (실패 무시)"
    
    # 테스트 실행
    success = run_command(cmd, description)
    
    if success:
        print(f"\n✅ 테스트 완료!")
        
        if args.coverage:
            print("\n📊 커버리지 리포트가 htmlcov/ 디렉토리에 생성되었습니다.")
            print("브라우저에서 htmlcov/index.html을 열어 확인하세요.")
    else:
        print(f"\n❌ 테스트 실패!")
        sys.exit(1)


def run_specific_tests():
    """특정 테스트 시나리오들"""
    scenarios = {
        "models": {
            "cmd": ["python", "-m", "pytest", "tests/calendar/test_models.py", "-v"],
            "desc": "모델 테스트"
        },
        "auth": {
            "cmd": ["python", "-m", "pytest", "tests/calendar/test_auth.py", "-v"],
            "desc": "인증 테스트"
        },
        "provider": {
            "cmd": ["python", "-m", "pytest", "tests/calendar/test_google_provider.py", "-v"],
            "desc": "Google Provider 테스트"
        },
        "service": {
            "cmd": ["python", "-m", "pytest", "tests/calendar/test_service.py", "-v"],
            "desc": "서비스 테스트"
        },
        "exceptions": {
            "cmd": ["python", "-m", "pytest", "tests/calendar/test_exceptions.py", "-v"],
            "desc": "예외 테스트"
        },
        "factory": {
            "cmd": ["python", "-m", "pytest", "tests/calendar/test_factory.py", "-v"],
            "desc": "팩토리 테스트"
        }
    }
    
    print("사용 가능한 테스트 시나리오:")
    for key, scenario in scenarios.items():
        print(f"  {key}: {scenario['desc']}")
    
    choice = input("\n실행할 시나리오를 선택하세요 (또는 'all'): ").strip().lower()
    
    if choice == "all":
        for key, scenario in scenarios.items():
            success = run_command(scenario["cmd"], scenario["desc"])
            if not success:
                print(f"❌ {scenario['desc']} 실패!")
                return False
        print("✅ 모든 테스트 완료!")
        return True
    elif choice in scenarios:
        scenario = scenarios[choice]
        return run_command(scenario["cmd"], scenario["desc"])
    else:
        print("잘못된 선택입니다.")
        return False


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 인자가 없으면 대화형 모드
        print("캘린더 서비스 테스트 실행기")
        print("=" * 40)
        
        choice = input("1. 명령행 모드\n2. 시나리오 선택 모드\n선택 (1-2): ").strip()
        
        if choice == "2":
            run_specific_tests()
        else:
            print("\n명령행 옵션:")
            print("python run_tests.py --help")
    else:
        main()