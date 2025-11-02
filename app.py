<<<<<<< HEAD
# app.py
from flask import Flask, request, jsonify
import predict # predict.py를 임포트합니다.

app = Flask(__name__)

# predict.py가 시작될 때 모델을 미리 로드하므로 app.py는 간단합니다.
# (predict.py의 "API: 로드 완료." 메시지가 서버 시작 시 한 번 뜹니다.)

@app.route('/predict', methods=['POST'])
def handle_prediction():
    """
    백엔드로부터 POST 요청을 받아 예측을 수행하는 엔드포인트입니다.
    """
    # 1. 백엔드가 보낸 JSON 데이터를 받습니다.
    raw_data_dict = request.get_json()

    if raw_data_dict is None:
        return jsonify({"error": "잘못된 요청입니다. JSON 데이터가 없습니다."}), 400

    # 2. predict.py의 예측 함수를 호출합니다.
    # 이 함수는 전처리, 예측, 3단계 분류를 모두 수행합니다.
    result = predict.get_prediction(raw_data_dict)

    # 3. 결과를 백엔드에 JSON 형태로 응답(Response)합니다.
    if "error" in result:
        return jsonify(result), 500 # 예측 중 오류 발생
    
    return jsonify(result)

if __name__ == '__main__':
    # 서버를 0.0.0.0 (모든 IP)의 8080 포트로 실행합니다.
    # Docker 환경에서는 이 부분이 아닌 Gunicorn을 사용합니다.
=======
# app.py
from flask import Flask, request, jsonify
import predict # predict.py를 임포트합니다.

app = Flask(__name__)

# predict.py가 시작될 때 모델을 미리 로드하므로 app.py는 간단합니다.
# (predict.py의 "API: 로드 완료." 메시지가 서버 시작 시 한 번 뜹니다.)

@app.route('/predict', methods=['POST'])
def handle_prediction():
    """
    백엔드로부터 POST 요청을 받아 예측을 수행하는 엔드포인트입니다.
    """
    # 1. 백엔드가 보낸 JSON 데이터를 받습니다.
    raw_data_dict = request.get_json()

    if raw_data_dict is None:
        return jsonify({"error": "잘못된 요청입니다. JSON 데이터가 없습니다."}), 400

    # 2. predict.py의 예측 함수를 호출합니다.
    # 이 함수는 전처리, 예측, 3단계 분류를 모두 수행합니다.
    result = predict.get_prediction(raw_data_dict)

    # 3. 결과를 백엔드에 JSON 형태로 응답(Response)합니다.
    if "error" in result:
        return jsonify(result), 500 # 예측 중 오류 발생
    
    return jsonify(result)

if __name__ == '__main__':
    # 서버를 0.0.0.0 (모든 IP)의 8080 포트로 실행합니다.
    # Docker 환경에서는 이 부분이 아닌 Gunicorn을 사용합니다.
>>>>>>> fa3378e86e5a1605c3bc82c00b0970beb4a69ad1
    app.run(host='0.0.0.0', port=8080, debug=True)