<<<<<<< HEAD
# predict.py
import pandas as pd
import numpy as np
import joblib # joblib으로 저장했으므로 joblib으로 로드
import json
import preprocessing # 전처리 모듈 임포트

# --- 1. 모델 및 아티팩트 전역 변수로 로드 ---
# (API 서버가 시작될 때 1회만 실행됩니다.)
try:
    print("API: 모델 및 아티팩트 로드 시작...")
    XGB_MODEL = joblib.load('final_xgboost_model.pkl')
    RF_MODEL = joblib.load('final_randomforest_model.pkl')
    
    with open('optimal_thresholds_final.json', 'r') as f:
        THRESHOLDS = json.load(f)
        
    with open('model_columns.json', 'r') as f:
        MODEL_COLUMNS = json.load(f)
        
    with open('industry_config.json', 'r', encoding="cp949") as f:
        INDUSTRY_CONFIG = json.load(f)
        
    print("API: 로드 완료.")
    
except FileNotFoundError:
    print("🚨 치명적 오류: 예측에 필요한 모델 또는 아티팩트 파일이 없습니다.")
    # 실제 서버에서는 여기서 오류를 발생시키거나 로깅해야 함
    XGB_MODEL, RF_MODEL, THRESHOLDS, MODEL_COLUMNS, INDUSTRY_CONFIG = None, None, None, None, None

def get_prediction(raw_data_dict):
    """
    백엔드로부터 받은 Raw 데이터(dict)를 기반으로 3단계 예측을 수행합니다.
    
    Args:
        raw_data_dict (dict): 단일 가맹점의 *Raw* 피처 딕셔너리.
                             (주의: 피처 엔지니어링에 필요한 모든 원본 컬럼이 포함되어야 함)
                             예: {'TA_YM': 202310, 'MCT_BRD_NUM': 'SOME_BRAND', ...}
                             
    Returns:
        dict: 예측 결과 (단계, 확률 등)
    """
    if XGB_MODEL is None:
        return {"error": "모델이 로드되지 않았습니다."}
        
    try:
        # 1. Raw Dict -> DataFrame 변환
        # (주의: 백엔드와 이 딕셔너리의 Key(컬럼명)를 정확히 일치시켜야 함)
        raw_df = pd.DataFrame([raw_data_dict])

        # 2. 피처 엔지니어링 (예측 모드)
        # (주의: TA_YM 같은 시간 컬럼, M12_MAL_XX_RAT 같은 고객 컬럼이 모두 dict에 있어야 함)
        df_engineered = preprocessing.feature_engineer(raw_df, industry_config=INDUSTRY_CONFIG)
        
        # 3. 결측치 처리
        df_filled = preprocessing.apply_imputation(df_engineered)
        
        # 4. OHE 및 컬럼 정렬 (예측 모드)
        X_processed = preprocessing.encode_and_align(df_filled, train_columns=MODEL_COLUMNS)
        
        # 5. 모델 예측
        xgb_proba = XGB_MODEL.predict_proba(X_processed)[0, 1]
        rf_proba = RF_MODEL.predict_proba(X_processed)[0, 1]
        
        # 6. 3단계 로직 적용
        tier = '안전'
        if rf_proba >= THRESHOLDS['threshold_danger_rf']:
            tier = '위험'
        elif xgb_proba >= THRESHOLDS['threshold_caution_xgb']:
            tier = '주의'
            
        return {
            "prediction_tier": tier,
            "xgb_probability": float(xgb_proba),
            "rf_probability": float(rf_proba),
            "threshold_caution": THRESHOLDS['threshold_caution_xgb'],
            "threshold_danger": THRESHOLDS['threshold_danger_rf']
        }

    except Exception as e:
=======
# predict.py
import pandas as pd
import numpy as np
import joblib # joblib으로 저장했으므로 joblib으로 로드
import json
import preprocessing # 전처리 모듈 임포트

# --- 1. 모델 및 아티팩트 전역 변수로 로드 ---
# (API 서버가 시작될 때 1회만 실행됩니다.)
try:
    print("API: 모델 및 아티팩트 로드 시작...")
    XGB_MODEL = joblib.load('final_xgboost_model.pkl')
    RF_MODEL = joblib.load('final_randomforest_model.pkl')
    
    with open('optimal_thresholds_final.json', 'r') as f:
        THRESHOLDS = json.load(f)
        
    with open('model_columns.json', 'r') as f:
        MODEL_COLUMNS = json.load(f)
        
    with open('industry_config.json', 'r', encoding="cp949") as f:
        INDUSTRY_CONFIG = json.load(f)
        
    print("API: 로드 완료.")
    
except FileNotFoundError:
    print("🚨 치명적 오류: 예측에 필요한 모델 또는 아티팩트 파일이 없습니다.")
    # 실제 서버에서는 여기서 오류를 발생시키거나 로깅해야 함
    XGB_MODEL, RF_MODEL, THRESHOLDS, MODEL_COLUMNS, INDUSTRY_CONFIG = None, None, None, None, None

def get_prediction(raw_data_dict):
    """
    백엔드로부터 받은 Raw 데이터(dict)를 기반으로 3단계 예측을 수행합니다.
    
    Args:
        raw_data_dict (dict): 단일 가맹점의 *Raw* 피처 딕셔너리.
                             (주의: 피처 엔지니어링에 필요한 모든 원본 컬럼이 포함되어야 함)
                             예: {'TA_YM': 202310, 'MCT_BRD_NUM': 'SOME_BRAND', ...}
                             
    Returns:
        dict: 예측 결과 (단계, 확률 등)
    """
    if XGB_MODEL is None:
        return {"error": "모델이 로드되지 않았습니다."}
        
    try:
        # 1. Raw Dict -> DataFrame 변환
        # (주의: 백엔드와 이 딕셔너리의 Key(컬럼명)를 정확히 일치시켜야 함)
        raw_df = pd.DataFrame([raw_data_dict])

        # 2. 피처 엔지니어링 (예측 모드)
        # (주의: TA_YM 같은 시간 컬럼, M12_MAL_XX_RAT 같은 고객 컬럼이 모두 dict에 있어야 함)
        df_engineered = preprocessing.feature_engineer(raw_df, industry_config=INDUSTRY_CONFIG)
        
        # 3. 결측치 처리
        df_filled = preprocessing.apply_imputation(df_engineered)
        
        # 4. OHE 및 컬럼 정렬 (예측 모드)
        X_processed = preprocessing.encode_and_align(df_filled, train_columns=MODEL_COLUMNS)
        
        # 5. 모델 예측
        xgb_proba = XGB_MODEL.predict_proba(X_processed)[0, 1]
        rf_proba = RF_MODEL.predict_proba(X_processed)[0, 1]
        
        # 6. 3단계 로직 적용
        tier = '안전'
        if rf_proba >= THRESHOLDS['threshold_danger_rf']:
            tier = '위험'
        elif xgb_proba >= THRESHOLDS['threshold_caution_xgb']:
            tier = '주의'
            
        return {
            "prediction_tier": tier,
            "xgb_probability": float(xgb_proba),
            "rf_probability": float(rf_proba),
            "threshold_caution": THRESHOLDS['threshold_caution_xgb'],
            "threshold_danger": THRESHOLDS['threshold_danger_rf']
        }

    except Exception as e:
>>>>>>> fa3378e86e5a1605c3bc82c00b0970beb4a69ad1
        return {"error": f"예측 중 오류 발생: {str(e)}"}