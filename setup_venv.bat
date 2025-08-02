@echo off
echo Python venv 가상환경을 설정합니다...

REM venv 가상환경 생성
python -m venv venv

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo 가상환경이 활성화되었습니다.
echo Python 버전:
python --version

REM 필요한 패키지 설치
if exist requirements.txt (
    echo requirements.txt에서 패키지를 설치합니다...
    pip install -r requirements.txt
)

echo 설정이 완료되었습니다.