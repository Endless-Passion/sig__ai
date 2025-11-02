# train.py
import pandas as pd
import numpy as np
import pickle
import joblib # Pickle보다 안정적일 수 있습니다.
import json
import optuna
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import fbeta_score, make_scorer, precision_recall_curve

# 1. 전처리 모듈 임포트
import preprocessing

# --- 0. 경로 설정 ---
PATH_INFO = r'C:\Users\aqtg6\OneDrive\바탕 화면\Hackerton\data\big_data_set1_f.csv'
PATH_CUSTOMER = r'C:\Users\aqtg6\OneDrive\바탕 화면\Hackerton\data\big_data_set2_f.csv'
PATH_SALES = r'C:\Users\aqtg6\OneDrive\바탕 화면\Hackerton\data\big_data_set3_f.csv'

# --- 1. 데이터 로드 및 피처 엔지니어링 ---
print("1. 데이터 로드 및 병합...")
df_total = preprocessing.load_and_merge_data(PATH_INFO, PATH_CUSTOMER, PATH_SALES)

print("2. 피처 엔지니어링...")
# (학습 모드) industry_config를 반환받음
df_processed, industry_config = preprocessing.feature_engineer(df_total, industry_config=None)

# --- 2. 학습용 데이터 클리닝 (좀비/우량 제거) ---
print("3. 노이즈 데이터 제거...")
df_cleaned = preprocessing.clean_data_for_training(df_processed)

# --- 3. 시간순 데이터 분할 (Train/Test Split) ---
print("4. 데이터 분할 (시간순 80:20)...")
df_sorted = df_cleaned.sort_values(by='경과_개월')

# 분리 후 불필요한 원본 컬럼 제거
y = df_sorted['폐업_여부']
X = df_sorted.drop(columns=[
    '폐업_여부', 'ARE_D', 'MCT_OPE_MS_CN', 'MCT_ME_D', '경과_개월'
])

split_point = int(len(df_sorted) * 0.8)
X_train, X_test = X[:split_point], X[split_point:]
y_train, y_test = y[:split_point], y[split_point:]

# --- 4. 전처리 파이프라인 (Imputation & OHE) ---
print("5. 전처리 파이프라인 적용 (결측치, OHE)...")
# 결측치 처리
X_train_filled = preprocessing.apply_imputation(X_train)
X_test_filled = preprocessing.apply_imputation(X_test)

# (학습 모드) OHE 적용 및 최종 컬럼 리스트(model_columns) 저장
X_train_final, model_columns = preprocessing.encode_and_align(X_train_filled, train_columns=None)

# (예측 모드) OHE 적용 및 컬럼 정렬
X_test_final = preprocessing.encode_and_align(X_test_filled, train_columns=model_columns)

# --- 5. 학습에 필요한 아티팩트(Artifacts) 저장 ---
print("6. 예측용 아티팩트 저장...")
# A. 최종 모델 컬럼 리스트 저장 (예측 시 필수)
with open('model_columns.json', 'w') as f:
    json.dump(model_columns, f, indent=4)

# B. 업종 처리 기준 저장 (예측 시 필수)
with open('industry_config.json', 'w') as f:
    json.dump(industry_config, f, indent=4, ensure_ascii=False)

# --- 6. Optuna 하이퍼파라미터 튜닝 ---
print("7. 하이퍼파라미터 튜닝 시작 (XGBoost & RF)...")
scale_pos_weight_value = y_train.value_counts()[0] / y_train.value_counts()[1]
f2_scorer = make_scorer(fbeta_score, beta=2, pos_label=1)

# (임시: 튜닝 결과를 하드코딩. 실제로는 study.best_params 사용)
best_params_xgb = {
    'n_estimators': 219, 'max_depth': 17, 'learning_rate': 0.0681, 
    'subsample': 0.738, 'colsample_bytree': 0.977, 'gamma': 4.0, 
    'reg_alpha': 1.1, 'reg_lambda': 3.2, 'base_score': 0.5 # SHAP 오류 방지용
}
best_params_rf = {
    'n_estimators': 400, 'max_depth': 46, 'min_samples_split': 11, 
    'min_samples_leaf': 9, 'max_features': 'sqrt', 'class_weight': 'balanced'}

# --- 7. 최종 모델 학습 및 저장 ---
print("8. 최종 모델 학습 및 저장...")
# XGBoost
final_xgb_model = XGBClassifier(
    **best_params_xgb,
    scale_pos_weight=scale_pos_weight_value,
    tree_method='hist', device='cpu', random_state=42
)
final_xgb_model.fit(X_train_final, y_train)
joblib.dump(final_xgb_model, 'final_xgboost_model.pkl') # joblib 사용 권장

# Random Forest
final_rf_model = RandomForestClassifier(**best_params_rf, random_state=42, n_jobs=-1)
final_rf_model.fit(X_train_final, y_train)
joblib.dump(final_rf_model, 'final_randomforest_model.pkl')

# --- 8. 최적 임계값 탐색 및 저장 ---
print("9. 최적 임계값 탐색 및 저장...")
TARGET_RECALL = 0.80
TARGET_PRECISION = 0.70

# XGB
y_proba_xgb = final_xgb_model.predict_proba(X_test_final)[:, 1]
precisions_xgb, recalls_xgb, thresholds_xgb = precision_recall_curve(y_test, y_proba_xgb, pos_label=1)
indices_xgb = np.where(recalls_xgb[:-1] >= TARGET_RECALL)[0]
threshold_caution_xgb = thresholds_xgb[indices_xgb[np.argmax(precisions_xgb[indices_xgb])]]

# RF
y_proba_rf = final_rf_model.predict_proba(X_test_final)[:, 1]
precisions_rf, recalls_rf, thresholds_rf = precision_recall_curve(y_test, y_proba_rf, pos_label=1)
indices_rf = np.where(precisions_rf[:-1] >= TARGET_PRECISION)[0]
threshold_danger_rf = thresholds_rf[indices_rf[np.argmax(recalls_rf[indices_rf])]]

# 저장
thresholds = {
    'threshold_caution_xgb': float(threshold_caution_xgb),
    'threshold_danger_rf': float(threshold_danger_rf)
}
with open('optimal_thresholds_final.json', 'w') as f:
    json.dump(thresholds, f, indent=4)

print("--- 학습 파이프라인 완료 ---")