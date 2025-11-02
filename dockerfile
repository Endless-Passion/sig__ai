# Dockerfile

# 1. 기본 이미지: Python 3.9 (학습 환경과 동일하게)
FROM python:3.9-slim

# 2. 작업 디렉터리 설정
WORKDIR /app

# 3. requirements.txt 먼저 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 모든 파일 복사
# (app.py, predict.py, preprocessing.py, *.pkl, *.json 파일들)
COPY . .

# 5. API 서버 실행
# Gunicorn을 사용하여 80번 포트로 app.py를 실행
# (백엔드가 Docker 컨테이너의 80번 포트로 접속합니다)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:80"]