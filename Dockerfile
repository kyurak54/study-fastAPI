# 사용할 Python 기본 이미지
FROM python:3.13.3-slim-bookworm

# 작업 디렉토리 설정 (컨테이너 내부)
WORKDIR /app

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사 # main.py 파일 복사
COPY main.py .

# 컨테이너가 리스닝할 포트 (Uvicorn이 사용할 포트) # Uvicorn의 기본 포트
EXPOSE 8000

# 컨테이너 실행 시 Uvicorn을 사용하여 FastAPI 애플리케이션 실행
# --host 0.0.0.0: 모든 IP에서 리스닝
# --port 8000: 8000 포트 사용
# main:app: 'main.py' 파일 내의 FastAPI 애플리케이션 객체 이름이 'app'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]