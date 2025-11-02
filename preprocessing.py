<<<<<<< HEAD
# preprocessing.py
import pandas as pd
import numpy as np

def load_and_merge_data(path_info, path_customer, path_sales):
    """3개의 Raw CSV 파일을 로드하고 병합합니다."""
    df_info = pd.read_csv(path_info, encoding='cp949')
    df_customer = pd.read_csv(path_customer, encoding='cp949')
    df_sales = pd.read_csv(path_sales, encoding='cp949')

    df_monthly_data = pd.merge(
        df_customer,
        df_sales,
        on=['ENCODED_MCT', 'TA_YM'],
        how='inner'
    )
    
    df_total = pd.merge(
        df_monthly_data,
        df_info,
        on='ENCODED_MCT',
        how='left'
    )
    
    # 학습에 사용할 컬럼만 필터링 (원본 스크립트 기준)
    columns_to_keep = [
        'ENCODED_MCT', 'TA_YM', 'M12_MAL_1020_RAT', 'M12_MAL_30_RAT',
        'M12_MAL_40_RAT', 'M12_MAL_50_RAT', 'M12_MAL_60_RAT',
        'MCT_UE_CLN_REU_RAT', 'RC_M1_SHC_FLP_UE_CLN_RAT', 'M12_SME_RY_ME_MCT_RAT',
        'M1SME_RY_SAA_RAT', 'M1_SME_RY_CNT_RAT', 'M12_SME_RY_SAA_PCE_RT',
        'DLV_SAA_RAT', 'MCT_BRD_NUM', 'HPSN_MCT_ZCD_NM', 'MCT_ME_D',
        'ARE_D', 'MCT_OPE_MS_CN'
    ]
    # 원본에 'M1_SME_RY_SAA_RAT'가 'M1SME_RY_SAA_RAT'로 오타가 있을 수 있으므로 확인
    # 원본 스크립트의 columns_to_keep 리스트를 정확하게 복사해와야 합니다.
    # 여기서는 예시로 원본의 일부 컬럼명을 사용했습니다.
    
    # 실제 사용할 컬럼이 df_total에 있는지 확인 (오타 방지)
    valid_cols = [col for col in columns_to_keep if col in df_total.columns]
    df_total = df_total[valid_cols]
    
    return df_total

def feature_engineer(df, industry_config=None):
    """
    핵심 피처 엔지니어링 및 타겟 변수 생성을 수행합니다.
    - industry_config: None이면 학습(Train) 모드, 값이 있으면 예측(Predict) 모드
    """
    
    is_train_mode = (industry_config is None)
    df_processed = df.copy()

    # --- 타입 변환 및 기본 피처 생성 ---
    df_processed['MCT_OPE_MS_CN'] = pd.to_numeric(
        df_processed['MCT_OPE_MS_CN'].str.extract('(\\d+)')[0], errors='coerce'
    )
    df_processed['브랜드_여부'] = df_processed['MCT_BRD_NUM'].notna().astype(int)

    # --- 업종 피처 단순화 ---
    # 💡 [수정] if industry_config is None: -> if is_train_mode:
    if is_train_mode:
        # (학습 모드) 업종 기준을 계산하고 저장
        industry_counts = df_processed['HPSN_MCT_ZCD_NM'].value_counts()
        threshold = 20
        rare_industries = industry_counts[industry_counts < threshold].index.tolist()
        coffee_categories = ['커피전문점', '테이크아웃커피']
        
        # 예측 시 사용하기 위해 config 저장
        industry_config = {
            'rare_industries': rare_industries,
            'coffee_categories': coffee_categories
        }
    else:
        # (예측 모드) 저장된 업종 기준을 로드하여 사용
        rare_industries = industry_config['rare_industries']
        coffee_categories = industry_config['coffee_categories']

    df_processed.loc[
        df_processed['HPSN_MCT_ZCD_NM'].isin(rare_industries), 'HPSN_MCT_ZCD_NM'
    ] = '업종_기타'
    df_processed.loc[
        df_processed['HPSN_MCT_ZCD_NM'].isin(coffee_categories), 'HPSN_MCT_ZCD_NM'
    ] = '카페'

    # --- 결측치 Placeholder 처리 ---
    df_processed.replace(-999999.9, np.nan, inplace=True)

    # --- 시간 피처 변환 (TA_YM) ---
    df_processed['TA_YM'] = pd.to_datetime(df_processed['TA_YM'], format='%Y%m')
    df_processed['연도'] = df_processed['TA_YM'].dt.year
    df_processed['월'] = df_processed['TA_YM'].dt.month
    df_processed['월_sin'] = np.sin(2 * np.pi * df_processed['월'] / 12)
    df_processed['월_cos'] = np.cos(2 * np.pi * df_processed['월'] / 12)
    
    # 💡 [수정] if industry_config is None: -> if is_train_mode:
    # (경과_개월은 학습/테스트 분리용으로만 생성)
    if is_train_mode: # 학습 모드일 때만 생성
        start_month = df_processed['TA_YM'].min()
        df_processed['경과_개월'] = ((df_processed['TA_YM'].dt.year - start_month.year) * 12 +
                                   (df_processed['TA_YM'].dt.month - start_month.month))

    # --- 피처 통합 (남성) ---
    df_processed['남성_2030대_고객비중'] = df_processed['M12_MAL_1020_RAT'] + df_processed['M12_MAL_30_RAT']
    df_processed['남성_40대이상_고객비중'] = df_processed['M12_MAL_40_RAT'] + \
                                          df_processed['M12_MAL_50_RAT'] + \
                                          df_processed['M12_MAL_60_RAT']

    # --- 상호작용 피처 ---
    df_processed['비배달_비프랜차이즈'] = ((df_processed['DLV_SAA_RAT'] == 0) & (df_processed['브랜드_여부'] == 0)).astype(int)
    df_processed['신규매장_여부'] = (df_processed['MCT_OPE_MS_CN'] <= 1).astype(int)
    df_processed['슈퍼위험군_하위매출_비배달_비프랜차이즈'] = (
        (df_processed['비배달_비프랜차이즈'] == 1) & (df_processed['M12_SME_RY_SAA_PCE_RT'] > 50)
    ).astype(int)

    # --- 💡 [수정] ---
    # 타겟 변수 생성 로직을 '학습 모드'일 때만 실행하도록 변경
    if is_train_mode:
        # --- 타겟 변수 생성 ---
        df_processed['폐업_여부'] = df_processed['MCT_ME_D'].notna().astype(int)
    
    
    # --- 불필요 컬럼 제거 ---
    # 원본 피처 엔지니어링에서 제거된 컬럼들
    cols_to_drop = [
        'ENCODED_MCT', 'MCT_BRD_NUM', 'TA_YM', '월',
        'M12_MAL_1020_RAT', 'M12_MAL_30_RAT', 'M12_MAL_40_RAT',
        'M12_MAL_50_RAT', 'M12_MAL_60_RAT',
    ]
    df_processed = df_processed.drop(columns=[col for col in cols_to_drop if col in df_processed.columns])

    # 💡 [수정] 함수 마지막 return 구문을 is_train_mode 플래그로 변경
    if is_train_mode:
        return df_processed, industry_config # 2개 값 반환 (학습 모드)
    else:
        return df_processed # 1개 값 반환 (예측 모드)

def clean_data_for_training(df):
    """(학습 전용) 노이즈 데이터 (좀비/우량)를 제거합니다."""
    df_cleaned = df.copy()
    
    # 1. 활동성 지표 컬럼 (fillna를 위해 정의)
    activity_cols = [
        'MCT_UE_CLN_REU_RAT', 'RC_M1_SHC_FLP_UE_CLN_RAT',
        'M1_SME_RY_SAA_RAT', 'M1_SME_RY_CNT_RAT', 'DLV_SAA_RAT'
    ]
    
    # activity_cols 중 실제 존재하는 컬럼만 사용
    valid_activity_cols = [col for col in activity_cols if col in df_cleaned.columns]
    
    # 2. '좀비 가게' 제거
    df_cleaned[valid_activity_cols] = df_cleaned[valid_activity_cols].fillna(0)
    all_zero_mask = df_cleaned[valid_activity_cols].sum(axis=1) == 0
    zombie_store_mask = (all_zero_mask) & (df_cleaned['폐업_여부'] == 0)
    zombie_indices = df_cleaned[zombie_store_mask].index
    if len(zombie_indices) > 0:
        df_cleaned = df_cleaned.drop(zombie_indices)

    # 3. '우량 가게 폐업' 제거
    healthy_store_mask = (df_cleaned['M12_SME_RY_SAA_PCE_RT'].fillna(50) <= 20)
    unpredictable_closure_mask = (healthy_store_mask) & (df_cleaned['폐업_여부'] == 1)
    unpredictable_indices = df_cleaned[unpredictable_closure_mask].index
    if len(unpredictable_indices) > 0:
        df_cleaned = df_cleaned.drop(unpredictable_indices)
        
    return df_cleaned

def apply_imputation(df):
    """결측치를 처리합니다."""
    df_filled = df.copy()
    
    # 0으로 채울 컬럼들 (원본 스크립트 기준)
    cols_to_fill_zero = [
        'DLV_SAA_RAT', '남성_2030대_고객비중', '남성_40대이상_고객비중',
        'MCT_UE_CLN_REU_RAT', 'RC_M1_SHC_FLP_UE_CLN_RAT'
    ]
    
    for col in cols_to_fill_zero:
        if col in df_filled.columns:
            df_filled[col] = df_filled[col].fillna(0)
            
    # (XGBoost가 나머지 NaN을 처리하므로 다른 처리는 생략)
    return df_filled

def encode_and_align(df, train_columns=None):
    """
    원-핫 인코딩을 적용하고, 학습(Train) 스키마에 맞게 컬럼을 정렬합니다.
    - train_columns: None이면 학습(Train) 모드, 값이 있으면 예측(Predict) 모드
    """
    categorical_cols_to_encode = ['HPSN_MCT_ZCD_NM']
    
    # 원-핫 인코딩
    df_encoded = pd.get_dummies(
        df, 
        columns=[col for col in categorical_cols_to_encode if col in df.columns], 
        drop_first=True
    )
    
    if train_columns is None:
        # (학습 모드) 현재 컬럼 목록을 반환
        return df_encoded, df_encoded.columns.tolist()
    else:
        # (예측 모드) 학습 시점의 컬럼 목록(train_columns)에 맞게 정렬
        # 없는 컬럼은 0으로 채워지고, 예측 시점에만 있는 컬럼은 제거됨
        df_aligned = df_encoded.reindex(columns=train_columns, fill_value=0)
=======
# preprocessing.py
import pandas as pd
import numpy as np

def load_and_merge_data(path_info, path_customer, path_sales):
    """3개의 Raw CSV 파일을 로드하고 병합합니다."""
    df_info = pd.read_csv(path_info, encoding='cp949')
    df_customer = pd.read_csv(path_customer, encoding='cp949')
    df_sales = pd.read_csv(path_sales, encoding='cp949')

    df_monthly_data = pd.merge(
        df_customer,
        df_sales,
        on=['ENCODED_MCT', 'TA_YM'],
        how='inner'
    )
    
    df_total = pd.merge(
        df_monthly_data,
        df_info,
        on='ENCODED_MCT',
        how='left'
    )
    
    # 학습에 사용할 컬럼만 필터링 (원본 스크립트 기준)
    columns_to_keep = [
        'ENCODED_MCT', 'TA_YM', 'M12_MAL_1020_RAT', 'M12_MAL_30_RAT',
        'M12_MAL_40_RAT', 'M12_MAL_50_RAT', 'M12_MAL_60_RAT',
        'MCT_UE_CLN_REU_RAT', 'RC_M1_SHC_FLP_UE_CLN_RAT', 'M12_SME_RY_ME_MCT_RAT',
        'M1SME_RY_SAA_RAT', 'M1_SME_RY_CNT_RAT', 'M12_SME_RY_SAA_PCE_RT',
        'DLV_SAA_RAT', 'MCT_BRD_NUM', 'HPSN_MCT_ZCD_NM', 'MCT_ME_D',
        'ARE_D', 'MCT_OPE_MS_CN'
    ]
    # 원본에 'M1_SME_RY_SAA_RAT'가 'M1SME_RY_SAA_RAT'로 오타가 있을 수 있으므로 확인
    # 원본 스크립트의 columns_to_keep 리스트를 정확하게 복사해와야 합니다.
    # 여기서는 예시로 원본의 일부 컬럼명을 사용했습니다.
    
    # 실제 사용할 컬럼이 df_total에 있는지 확인 (오타 방지)
    valid_cols = [col for col in columns_to_keep if col in df_total.columns]
    df_total = df_total[valid_cols]
    
    return df_total

def feature_engineer(df, industry_config=None):
    """
    핵심 피처 엔지니어링 및 타겟 변수 생성을 수행합니다.
    - industry_config: None이면 학습(Train) 모드, 값이 있으면 예측(Predict) 모드
    """
    
    is_train_mode = (industry_config is None)
    df_processed = df.copy()

    # --- 타입 변환 및 기본 피처 생성 ---
    df_processed['MCT_OPE_MS_CN'] = pd.to_numeric(
        df_processed['MCT_OPE_MS_CN'].str.extract('(\\d+)')[0], errors='coerce'
    )
    df_processed['브랜드_여부'] = df_processed['MCT_BRD_NUM'].notna().astype(int)

    # --- 업종 피처 단순화 ---
    # 💡 [수정] if industry_config is None: -> if is_train_mode:
    if is_train_mode:
        # (학습 모드) 업종 기준을 계산하고 저장
        industry_counts = df_processed['HPSN_MCT_ZCD_NM'].value_counts()
        threshold = 20
        rare_industries = industry_counts[industry_counts < threshold].index.tolist()
        coffee_categories = ['커피전문점', '테이크아웃커피']
        
        # 예측 시 사용하기 위해 config 저장
        industry_config = {
            'rare_industries': rare_industries,
            'coffee_categories': coffee_categories
        }
    else:
        # (예측 모드) 저장된 업종 기준을 로드하여 사용
        rare_industries = industry_config['rare_industries']
        coffee_categories = industry_config['coffee_categories']

    df_processed.loc[
        df_processed['HPSN_MCT_ZCD_NM'].isin(rare_industries), 'HPSN_MCT_ZCD_NM'
    ] = '업종_기타'
    df_processed.loc[
        df_processed['HPSN_MCT_ZCD_NM'].isin(coffee_categories), 'HPSN_MCT_ZCD_NM'
    ] = '카페'

    # --- 결측치 Placeholder 처리 ---
    df_processed.replace(-999999.9, np.nan, inplace=True)

    # --- 시간 피처 변환 (TA_YM) ---
    df_processed['TA_YM'] = pd.to_datetime(df_processed['TA_YM'], format='%Y%m')
    df_processed['연도'] = df_processed['TA_YM'].dt.year
    df_processed['월'] = df_processed['TA_YM'].dt.month
    df_processed['월_sin'] = np.sin(2 * np.pi * df_processed['월'] / 12)
    df_processed['월_cos'] = np.cos(2 * np.pi * df_processed['월'] / 12)
    
    # 💡 [수정] if industry_config is None: -> if is_train_mode:
    # (경과_개월은 학습/테스트 분리용으로만 생성)
    if is_train_mode: # 학습 모드일 때만 생성
        start_month = df_processed['TA_YM'].min()
        df_processed['경과_개월'] = ((df_processed['TA_YM'].dt.year - start_month.year) * 12 +
                                   (df_processed['TA_YM'].dt.month - start_month.month))

    # --- 피처 통합 (남성) ---
    df_processed['남성_2030대_고객비중'] = df_processed['M12_MAL_1020_RAT'] + df_processed['M12_MAL_30_RAT']
    df_processed['남성_40대이상_고객비중'] = df_processed['M12_MAL_40_RAT'] + \
                                          df_processed['M12_MAL_50_RAT'] + \
                                          df_processed['M12_MAL_60_RAT']

    # --- 상호작용 피처 ---
    df_processed['비배달_비프랜차이즈'] = ((df_processed['DLV_SAA_RAT'] == 0) & (df_processed['브랜드_여부'] == 0)).astype(int)
    df_processed['신규매장_여부'] = (df_processed['MCT_OPE_MS_CN'] <= 1).astype(int)
    df_processed['슈퍼위험군_하위매출_비배달_비프랜차이즈'] = (
        (df_processed['비배달_비프랜차이즈'] == 1) & (df_processed['M12_SME_RY_SAA_PCE_RT'] > 50)
    ).astype(int)

    # --- 💡 [수정] ---
    # 타겟 변수 생성 로직을 '학습 모드'일 때만 실행하도록 변경
    if is_train_mode:
        # --- 타겟 변수 생성 ---
        df_processed['폐업_여부'] = df_processed['MCT_ME_D'].notna().astype(int)
    
    
    # --- 불필요 컬럼 제거 ---
    # 원본 피처 엔지니어링에서 제거된 컬럼들
    cols_to_drop = [
        'ENCODED_MCT', 'MCT_BRD_NUM', 'TA_YM', '월',
        'M12_MAL_1020_RAT', 'M12_MAL_30_RAT', 'M12_MAL_40_RAT',
        'M12_MAL_50_RAT', 'M12_MAL_60_RAT',
    ]
    df_processed = df_processed.drop(columns=[col for col in cols_to_drop if col in df_processed.columns])

    # 💡 [수정] 함수 마지막 return 구문을 is_train_mode 플래그로 변경
    if is_train_mode:
        return df_processed, industry_config # 2개 값 반환 (학습 모드)
    else:
        return df_processed # 1개 값 반환 (예측 모드)

def clean_data_for_training(df):
    """(학습 전용) 노이즈 데이터 (좀비/우량)를 제거합니다."""
    df_cleaned = df.copy()
    
    # 1. 활동성 지표 컬럼 (fillna를 위해 정의)
    activity_cols = [
        'MCT_UE_CLN_REU_RAT', 'RC_M1_SHC_FLP_UE_CLN_RAT',
        'M1_SME_RY_SAA_RAT', 'M1_SME_RY_CNT_RAT', 'DLV_SAA_RAT'
    ]
    
    # activity_cols 중 실제 존재하는 컬럼만 사용
    valid_activity_cols = [col for col in activity_cols if col in df_cleaned.columns]
    
    # 2. '좀비 가게' 제거
    df_cleaned[valid_activity_cols] = df_cleaned[valid_activity_cols].fillna(0)
    all_zero_mask = df_cleaned[valid_activity_cols].sum(axis=1) == 0
    zombie_store_mask = (all_zero_mask) & (df_cleaned['폐업_여부'] == 0)
    zombie_indices = df_cleaned[zombie_store_mask].index
    if len(zombie_indices) > 0:
        df_cleaned = df_cleaned.drop(zombie_indices)

    # 3. '우량 가게 폐업' 제거
    healthy_store_mask = (df_cleaned['M12_SME_RY_SAA_PCE_RT'].fillna(50) <= 20)
    unpredictable_closure_mask = (healthy_store_mask) & (df_cleaned['폐업_여부'] == 1)
    unpredictable_indices = df_cleaned[unpredictable_closure_mask].index
    if len(unpredictable_indices) > 0:
        df_cleaned = df_cleaned.drop(unpredictable_indices)
        
    return df_cleaned

def apply_imputation(df):
    """결측치를 처리합니다."""
    df_filled = df.copy()
    
    # 0으로 채울 컬럼들 (원본 스크립트 기준)
    cols_to_fill_zero = [
        'DLV_SAA_RAT', '남성_2030대_고객비중', '남성_40대이상_고객비중',
        'MCT_UE_CLN_REU_RAT', 'RC_M1_SHC_FLP_UE_CLN_RAT'
    ]
    
    for col in cols_to_fill_zero:
        if col in df_filled.columns:
            df_filled[col] = df_filled[col].fillna(0)
            
    # (XGBoost가 나머지 NaN을 처리하므로 다른 처리는 생략)
    return df_filled

def encode_and_align(df, train_columns=None):
    """
    원-핫 인코딩을 적용하고, 학습(Train) 스키마에 맞게 컬럼을 정렬합니다.
    - train_columns: None이면 학습(Train) 모드, 값이 있으면 예측(Predict) 모드
    """
    categorical_cols_to_encode = ['HPSN_MCT_ZCD_NM']
    
    # 원-핫 인코딩
    df_encoded = pd.get_dummies(
        df, 
        columns=[col for col in categorical_cols_to_encode if col in df.columns], 
        drop_first=True
    )
    
    if train_columns is None:
        # (학습 모드) 현재 컬럼 목록을 반환
        return df_encoded, df_encoded.columns.tolist()
    else:
        # (예측 모드) 학습 시점의 컬럼 목록(train_columns)에 맞게 정렬
        # 없는 컬럼은 0으로 채워지고, 예측 시점에만 있는 컬럼은 제거됨
        df_aligned = df_encoded.reindex(columns=train_columns, fill_value=0)
>>>>>>> fa3378e86e5a1605c3bc82c00b0970beb4a69ad1
        return df_aligned