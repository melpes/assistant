@echo off
echo 가상환경을 활성화하고 프로젝트를 시작합니다...
call conda activate my-agent
if %ERRORLEVEL% NEQ 0 (
    echo 가상환경 활성화에 실패했습니다. conda가 설치되어 있는지 확인하세요.
    exit /b %ERRORLEVEL%
)
echo 가상환경 'my-agent'가 활성화되었습니다.
echo 이제 Python 명령어를 실행할 수 있습니다.
cmd /k