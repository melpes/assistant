# 개인 금융 거래 관리 시스템 설치 가이드

## 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [설치 방법](#2-설치-방법)
   - [Python 설치](#21-python-설치)
   - [가상 환경 설정](#22-가상-환경-설정)
   - [소스 코드 다운로드](#23-소스-코드-다운로드)
   - [의존성 설치](#24-의존성-설치)
3. [초기 설정](#3-초기-설정)
   - [데이터베이스 초기화](#31-데이터베이스-초기화)
   - [설정 파일 구성](#32-설정-파일-구성)
4. [실행 방법](#4-실행-방법)
5. [업데이트 방법](#5-업데이트-방법)
6. [문제 해결](#6-문제-해결)

## 1. 시스템 요구사항

개인 금융 거래 관리 시스템을 설치하기 위한 최소 요구사항은 다음과 같습니다:

- **운영체제**: Windows, macOS, Linux
- **Python**: 3.10 이상
- **저장 공간**: 최소 100MB (데이터 크기에 따라 증가)
- **메모리**: 최소 4GB RAM

## 2. 설치 방법

### 2.1 Python 설치

1. [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 3.10 이상 버전을 다운로드합니다.
2. 설치 과정에서 "Add Python to PATH" 옵션을 선택합니다.
3. 설치가 완료되면 명령 프롬프트(Windows) 또는 터미널(macOS/Linux)에서 다음 명령어를 실행하여 설치를 확인합니다:

```bash
python --version
```

### 2.2 가상 환경 설정

가상 환경을 사용하면 프로젝트별로 독립적인 Python 환경을 유지할 수 있습니다.

#### Conda 사용 (권장)

1. [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 또는 [Anaconda](https://www.anaconda.com/products/individual)를 설치합니다.
2. 명령 프롬프트 또는 터미널에서 다음 명령어를 실행합니다:

```bash
# 가상환경 생성
conda create -n my-agent python=3.10

# 가상환경 활성화
conda activate my-agent
```

#### venv 사용

1. 명령 프롬프트 또는 터미널에서 다음 명령어를 실행합니다:

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2.3 소스 코드 다운로드

Git을 사용하여 소스 코드를 다운로드합니다:

```bash
git clone https://github.com/username/financial-transaction-management.git
cd financial-transaction-management
```

또는 ZIP 파일로 다운로드하여 압축을 풀고 해당 디렉토리로 이동합니다.

### 2.4 의존성 설치

프로젝트 디렉토리에서 다음 명령어를 실행하여 필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

## 3. 초기 설정

### 3.1 데이터베이스 초기화

다음 명령어를 실행하여 데이터베이스를 초기화합니다:

```bash
python src/database_setup.py
```

### 3.2 설정 파일 구성

1. `config` 디렉토리가 없는 경우 생성합니다:

```bash
mkdir -p config
```

2. 기본 설정 파일을 생성합니다:

```bash
python src/cli.py config reset
```

3. 필요에 따라 설정을 수정합니다:

```bash
python src/cli.py config set --key user.display.language --value ko
```

## 4. 실행 방법

### 메인 애플리케이션 실행

```bash
python main.py
```

### CLI 인터페이스 사용

```bash
python src/cli.py
```

### 데이터 수집

```bash
# 토스뱅크 카드 명세서 가져오기
python src/cli.py ingest toss_card --file <파일경로>

# 토스뱅크 계좌 내역 가져오기
python src/cli.py ingest toss_account --file <파일경로>

# 수동 지출 입력
python src/cli.py ingest manual --type expense

# 수동 수입 입력
python src/cli.py ingest manual --type income
```

### 분석 및 리포트

```bash
# 지출 분석
python src/cli.py analyze expense --period month

# 수입 분석
python src/cli.py analyze income --period month

# 리포트 생성
python src/cli.py report summary --period month --format csv --output report.csv
```

## 5. 업데이트 방법

Git을 사용하여 소스 코드를 다운로드한 경우:

```bash
# 최신 코드 가져오기
git pull

# 의존성 업데이트
pip install -r requirements.txt

# 데이터베이스 마이그레이션 실행 (필요한 경우)
python src/database_migration.py
```

ZIP 파일로 다운로드한 경우:

1. 최신 버전을 다운로드합니다.
2. 기존 설치의 `config`, `data`, `backups` 디렉토리를 백업합니다.
3. 새 버전을 설치합니다.
4. 백업한 디렉토리를 새 설치에 복원합니다.
5. 의존성을 업데이트합니다:

```bash
pip install -r requirements.txt
```

6. 데이터베이스 마이그레이션을 실행합니다 (필요한 경우):

```bash
python src/database_migration.py
```

## 6. 문제 해결

### 의존성 오류

의존성 설치 중 오류가 발생하는 경우:

```bash
# 가상환경이 활성화되어 있는지 확인
conda info --envs  # Conda 사용 시
python -m venv     # venv 사용 시

# pip 업그레이드
pip install --upgrade pip

# 의존성 개별 설치
pip install pandas
pip install google-generativeai
pip install tavily-python
pip install google-api-python-client
```

### 데이터베이스 오류

데이터베이스 관련 오류가 발생하는 경우:

```bash
# 데이터베이스 최적화
python src/cli.py backup optimize

# 데이터베이스 백업
python src/cli.py backup backup-db

# 데이터베이스 재생성
python src/database_setup.py --force
```

### 로그 확인

오류 발생 시 로그 파일을 확인합니다:

```bash
# 로그 디렉토리 확인
ls -la logs/

# 최신 로그 확인
tail -n 100 logs/financial_system.log
```

### 추가 도움말

더 자세한 도움말은 다음 명령어로 확인할 수 있습니다:

```bash
python src/cli.py --help
python src/cli.py <명령어> --help
```