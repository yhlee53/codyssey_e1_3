import json

def load_json_data(file_path):
    """
    지정된 경로의 JSON 파일을 읽어서 딕셔너리로 반환합니다.
    파일이 없거나 형식이 잘못된 경우 None을 반환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"\n[오류] '{file_path}' 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError:
        print(f"\n[오류] '{file_path}' 파일의 형식이 올바르지 않습니다.")
    except Exception as e:
        print(f"\n[오류] 알 수 없는 에러 발생: {e}")
    
    return None