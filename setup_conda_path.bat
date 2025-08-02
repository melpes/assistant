@echo off
echo conda 경로를 환경 변수에 추가합니다...

REM 아래 경로는 일반적인 Anaconda 설치 경로입니다. 실제 경로로 수정해주세요.
set PATH=%PATH%;C:\Users\vega4\anaconda3\condabin\conda.bat

echo 환경 변수 설정이 완료되었습니다.
echo 이제 conda 명령어를 사용할 수 있습니다.
echo 현재 PATH: %PATH%