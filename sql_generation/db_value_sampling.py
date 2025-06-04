from dotenv import load_dotenv
import os

import pandas as pd
import pickle
from sqlalchemy import create_engine, text

from prompt_templates.schema_ddl import table_names

load_dotenv()  # .env 파일 불러오기

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def db_value_sampling(schema: str = 'public', tables_sample_path: str = 'all_tables_sample.pkl'):
    all_tables_data = {}
    engine = None
    is_updated = False

    if os.path.exists(tables_sample_path):
        try:
            with open(tables_sample_path, "rb") as f:
                all_tables_data = pickle.load(f)
            print(f"캐시된 테이블 데이터를 불러왔습니다. ({len(all_tables_data)}개 테이블)")
            return all_tables_data
        except Exception as e:
            print(f"캐시 파일 로드 실패: {e}")
            all_tables_data = {}

    for table_name in table_names:
        if table_name not in all_tables_data:
            if not engine:
                print("데이터베이스 엔진 생성 중...")
                engine = create_engine(connection_string)
                print("엔진 생성 성공.")
            try:
                query = text(f"SELECT * FROM {schema}.{table_name} LIMIT 30;")
                df_result = pd.read_sql(query, con=engine)
                all_tables_data[table_name] = df_result
                print(f"테이블 {table_name} 행 {len(df_result)}개 업데이트 완료.")
                is_updated = True
            except Exception as e:
                print(f"쿼리 실패 - {table_name}: {e}")

    if engine:
        engine.dispose()
        print("데이터베이스 엔진 연결이 종료되었습니다.")

    if is_updated:
        with open(tables_sample_path, "wb") as f:
            pickle.dump(all_tables_data, f)

    return all_tables_data
