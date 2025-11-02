import pandas as pd
import joblib  # 모델 로드를 위해 joblib 사용
import json
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib # 한글 폰트 자동 설정

# --- 1. 파일 로드 ---
print("모델 및 컬럼 파일 로드를 시작합니다...")

try:
    # 모델 로드
    # (train.py에서 joblib.dump로 저장했으므로 joblib.load 사용)
    xgb_model = joblib.load('final_xgboost_model.pkl')
    rf_model = joblib.load('final_randomforest_model.pkl')
    
    # 모델 학습 시 사용된 컬럼(피처) 목록 로드
    with open('model_columns.json', 'r') as f:
        model_columns = json.load(f)
        
    print("✅ 로드 완료.")

except FileNotFoundError:
    print("🚨 오류: 'final_xgboost_model.pkl', 'final_randomforest_model.pkl', 또는 'model_columns.json' 파일을 찾을 수 없습니다.")
    print("-> train.py를 먼저 실행하여 모델과 아티팩트 파일을 생성해야 합니다.")
    exit()

# --- 2. 피처 중요도 추출 (Pandas Series로 변환) ---

# 2-1. XGBoost
xgb_importance_values = xgb_model.feature_importances_
xgb_importance_series = pd.Series(xgb_importance_values, index=model_columns)
xgb_top20 = xgb_importance_series.sort_values(ascending=False).head(20)

# 2-2. Random Forest
rf_importance_values = rf_model.feature_importances_
rf_importance_series = pd.Series(rf_importance_values, index=model_columns)
rf_top20 = rf_importance_series.sort_values(ascending=False).head(20)

# --- 3. 콘솔에 상위 20개 피처 출력 ---
print("\n--- [XGBoost] 상위 20개 피처 중요도 ---")
print(xgb_top20)

print("\n--- [Random Forest] 상위 20개 피처 중요도 ---")
print(rf_top20)

# --- 4. 시각화 및 이미지 파일로 저장 ---

# 4-1. XGBoost 시각화
plt.figure(figsize=(10, 8))
sns.barplot(x=xgb_top20.values, y=xgb_top20.index)
plt.title('XGBoost 피처 중요도 (Top 20)')
plt.xlabel('Importance')
plt.ylabel('Features')
plt.tight_layout() # 레이블이 잘리지 않도록 조정
plt.savefig('xgb_feature_importance.png')
print("\n✅ 'xgb_feature_importance.png' 파일로 저장되었습니다.")

# 4-2. Random Forest 시각화
plt.figure(figsize=(10, 8))
sns.barplot(x=rf_top20.values, y=rf_top20.index)
plt.title('Random Forest 피처 중요도 (Top 20)')
plt.xlabel('Importance')
plt.ylabel('Features')
plt.tight_layout()
plt.savefig('rf_feature_importance.png')
print("✅ 'rf_feature_importance.png' 파일로 저장되었습니다.")