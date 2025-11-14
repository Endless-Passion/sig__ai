# 가맹점 폐업 위험 예측 AI 모델  
## 1. 프로젝트 개요

본 프로젝트는 가맹점의 다양한 데이터를(기본 정보, 고객, 매출) 기반으로 향후 폐업 위험을 예측하는 머신러닝 모델이다.  

이 프로젝트는 2가지 모델(XGBoost, Random Forest)의 예측 확률을 조합하여 가맹점의 위험 상태를 [안전, 주의, 위험] 3단계로 분류한다.  

최종 완성된 모델은 Flask와 Gunicorn을 통해 API 서버로 제공되며, Docker를 통해 컨테이너 환경에서 손쉽게 배포할 수 있도록 설계되었다.  

## 2. 프로젝트 아키텍처 및 파일 구조  
이 프로젝트는 **학습(train.py)**과 **예측(predict.py)**의 파이프라인이 분리되어 있으며, preprocessing.py 모듈을 공유하여 데이터 일관성을 유지한다.  

```bash
.
├── 📜 app.py               # API 서버 실행 (Flask)
├── 📜 predict.py           # API 요청 시 실제 예측 수행 로직
├── 📜 preprocessing.py     # 데이터 전처리 및 피처 엔지니어링 모듈
|
├── 📜 train.py             # 모델 학습 및 아티팩트(산출물) 생성 스크립트
├── 📜 check_importance.py  # (유틸리티) 학습된 모델의 피처 중요도 시각화
|
├── 📦 dockerfile           # API 서버 배포용 Docker 이미지 빌드 파일
├── 📦 requirements.txt     # Python 의존성 패키지 목록
|
├── 💾 final_xgboost_model.pkl      # (train.py 실행 후 생성됨)
├── 💾 final_randomforest_model.pkl # (train.py 실행 후 생성됨)
├── 💾 model_columns.json           # (train.py 실행 후 생성됨)
├── 💾 industry_config.json         # (train.py 실행 후 생성됨)
└── 💾 optimal_thresholds_final.json  # (train.py 실행 후 생성됨)
```
---  

## 파일 상세 설명
### train.py

- Raw 데이터(CSV)를 로드하여 `preprocessing.py`를 통해 피처 엔지니어링을 수행

- XGBoost, Random Forest 두 모델을 학습

- 비즈니스 요구사항(특정 Recall/Precision)에 맞는 최적의 임계값(Threshold)을 계산

- 예측에 필요한 5가지 핵심 산출물(pkl 2개 + JSON 3개)을 저장

---

### preprocessing.py

- 공통 전처리 로직을 담당

- 학습 모드 / 예측 모드 지원

- 수행 기능:
  - 결측치 예측
  - 원-핫 인코딩
  - 스키마 정렬
  - 업종/지역 등 카테고리 전처리
  - 시간 기반 파생 변수 생성   

---

### predict.py

- API 서버가 시작 시 학습된 모델과 JSON config 5종 로드

- `get_prediction(raw_data_dict)` 실행 시
  1. 입력 JSON 전처리
  2. 두 모델 확률 계산
  3. 임계값 기준으로 **안전/주의/위험** 등급 산출

---

### app.py

- Flask 기반 `/predict` 엔드포인트를 제공  
- 클라이언트의 POST JSON 입력 -> `predict.py` 호출 -> JSON 출력

---

### check_importance.py

- 학습된 모델 두 개를 불러와 **피처 중요도 시각화**
- `xgb_feature_importance.png`, `rf_feature_importance.png` 생성

---

### requirements.txt
프로젝트 실행에 필요한 주요 패키지
```nginx
pandas
scikit-learn
xgboost
Flask
gunicorn
```

--- 

### dockerfile

- `python:3.9-slim` 기반
- 의존성 설치 후 전체 프로젝트 복사
- Gunicorn으로 `app:app`실행 (port 80) 

---

## 3. 사용 방법
## 1) 의존성 설치
```bash
pip install -r requirements.txt
```
---

## 2) 모델 학습 (최초 1회)
`train.py` 내부의 `PATH_INFO`, `PATH_CUSTOMER`, `PATH_SALES` 경로를 실제 CSV 위치로 맞춘 뒤  
```bash
python train.py
```

실행 후 아래 5개 파일이 생성되어야 함  
- final_xgboost_model.pkl
- final_randomforest_model.pkl
- model_columns.json
- industry_config.json
- optimal_thresholds_final.json


**(선택) 피처 중요도 확인**
```bash
python check_importance.py
```

---

## 3) API 서버 실행
## A. 로컬 실행 (테스트용)
```bash

python app.py

```

## B. Docker 실행 (배포용)
이미지 빌드

```bash

docker build -t store-closure-api .

````

컨테이너 실행
```bash

docker run -p 8000:80 store-closure-api

```

API 주소
```bash

http://localhost:8000/predict

```

---

## 4. API 사용법
## POST /predict
**요청 형식(JSON)**
predict.py -> preprocessing.py의 입력 스키마와 동일해야 함.

```JSON
{
  "TA_YM": 202310,
  "HPSN_MCT_ZCD_NM": "커피전문점",
  "MCT_BRD_NUM": "BRAND_ID_123",
  "MCT_OPE_MS_CN": 15,
  "DLV_SAA_RAT": 0.0,
  "M12_MAL_1020_RAT": 0.15,
  "M12_MAL_30_RAT": 0.25,
  "M12_MAL_40_RAT": 0.20,
  "M12_MAL_50_RAT": 0.10,
  "M12_MAL_60_RAT": 0.05,
  "MCT_UE_CLN_REU_RAT": 0.8,
  "RC_M1_SHC_FLP_UE_CLN_RAT": 0.5,
  "M12_SME_RY_ME_MCT_RAT": 1.2,
  "M1SME_RY_SAA_RAT": 0.9,
  "M1_SME_RY_CNT_RAT": 1.1,
  "M12_SME_RY_SAA_PCE_RT": 30.0,
  "ARE_D": "서울 강남구"
}
```

---

## 성공 응답 (200 OK)

```JSON

{
  "prediction_tier": "주의",
  "xgb_probability": 0.625,
  "rf_probability": 0.310,
  "threshold_caution": 0.581,
  "threshold_danger": 0.752
}
```

---

## 오류 응답 (500 Internal Server Error)

```JSON

{
  "error": "예측 중 오류 발생: 'M12_MAL_1020_RAT' key not found"
}

```
