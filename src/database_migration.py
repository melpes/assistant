# src/database_migration.py
"""
개인 금융 거래 관리 시스템 데이터베이스 마이그레이션 클래스
기존 expenses 테이블을 transactions 테이블로 확장하고 새로운 테이블들을 생성합니다.

이 파일은 클래스 기반 구현을 제공하며, 실제 마이그레이션은 migrate_database.py에서 수행합니다.
"""
import sqlite3
import os
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_FILE_NAME = "personal_data.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

class DatabaseMigration:
    """데이터베이스 마이그레이션 클래스"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")  # 외래키 제약조건 활성화
            logger.info(f"데이터베이스에 연결되었습니다: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise
            
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            logger.info("데이터베이스 연결이 해제되었습니다.")
            
    def backup_existing_data(self):
        """기존 데이터 백업"""
        try:
            cursor = self.connection.cursor()
            
            # 기존 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='expenses'
            """)
            
            if not cursor.fetchone():
                logger.info("기존 expenses 테이블이 없습니다. 백업을 건너뜁니다.")
                return None
                
            # 백업 테이블 생성
            backup_table_name = f"expenses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute(f"""
                CREATE TABLE {backup_table_name} AS 
                SELECT * FROM expenses
            """)
            
            # 백업된 레코드 수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
            count = cursor.fetchone()[0]
            
            logger.info(f"기존 데이터 백업 완료: {backup_table_name} ({count}개 레코드)")
            return backup_table_name
            
        except sqlite3.Error as e:
            logger.error(f"데이터 백업 실패: {e}")
            raise
            
    def run_migration(self):
        """전체 마이그레이션 실행"""
        logger.info("이 클래스는 직접 실행하지 않습니다. migrate_database.py를 사용하세요.")
        logger.info("python src/migrate_database.py 명령으로 마이그레이션을 실행하세요.")

if __name__ == '__main__':
    logger.info("이 파일은 직접 실행하지 않습니다. migrate_database.py를 사용하세요.")
    logger.info("python src/migrate_database.py 명령으로 마이그레이션을 실행하세요.")