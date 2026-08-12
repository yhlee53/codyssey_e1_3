import json
import time

# [설정] 부동소수점 비교를 위한 허용 오차
EPSILON = 1e-9

def calculate_mac(filter_matrix, pattern_matrix):
    """
    MAC(Multiply-Accumulate) 연산을 반복문으로 직접 구현 (외부 라이브러리 금지)
    """
    rows = len(filter_matrix)
    cols = len(filter_matrix[0])
    total_sum = 0.0
    for r in range(rows):
        for c in range(cols):
            total_sum += filter_matrix[r][c] * pattern_matrix[r][c]
    return total_sum

def normalize_label(label):
    """
    라벨 정규화: '+', 'cross' -> 'Cross' / 'x' -> 'X'
    """
    label = str(label).lower().strip()
    if label in ['+', 'cross']:
        return "Cross"
    if label == 'x':
        return "X"
    return label

def compare_scores(score_a, score_b):
    """
    에플리론(epsilon) 기반 점수 비교 정책
    """
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return "A" if score_a > score_b else "B"

def get_3x3_input(name):
    """
    모드 1: 3x3 행렬 입력 및 검증
    """
    print(f"\n{name} 입력 (3줄, 각 줄에 숫자 3개를 공백으로 구분)")
    matrix = []
    while len(matrix) < 3:
        try:
            line = input(f"{len(matrix)+1}행: ").split()
            if len(line) != 3:
                print("입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요.")
                continue
            row = [float(x) for x in line]
            matrix.append(row)
        except ValueError:
            print("입력 형식 오류: 숫자만 입력 가능합니다.")
    return matrix

def measure_performance(f, p, size_n, iterations=10):
    """
    성능 측정: I/O를 제외한 순수 연산 구간 10회 반복 평균
    """
    start_time = time.perf_counter()
    for _ in range(iterations):
        calculate_mac(f, p)
    end_time = time.perf_counter()
    avg_time_ms = ((end_time - start_time) / iterations) * 1000
    return avg_time_ms

def run_mode_1():
    print("\n#----------------------------------------")
    print("# [1] 필터 및 패턴 입력 (모드 1)")
    print("#----------------------------------------")
    filter_a = get_3x3_input("필터 A")
    filter_b = get_3x3_input("필터 B")
    pattern = get_3x3_input("패턴")

    # 연산 및 판정
    score_a = calculate_mac(filter_a, pattern)
    score_b = calculate_mac(filter_b, pattern)
    
    # 성능 측정 (3x3)
    avg_t = measure_performance(filter_a, pattern, 3)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    print(f"A 점수: {score_a:.16f}")
    print(f"B 점수: {score_b:.16f}")
    
    diff = abs(score_a - score_b)
    if diff < EPSILON:
        print(f"판정: 판정 불가 (|A-B| < 1e-9)")
    else:
        result = "A" if score_a > score_b else "B"
        print(f"판정: {result}")
    
    print(f"연산 시간(평균/10회): {avg_t:.6f} ms")
    return {"size": "3x3", "time": avg_t, "ops": 9}

def run_mode_2(data):
    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    filters = data.get("filters", {})
    for key in filters:
        print(f"✓ {key} 필터 로드 완료 (Cross, X)")

    print("\n\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    
    patterns = data.get("patterns", {})
    results_summary = []
    perf_data = []
    
    # 3x3 성능 데이터 (위 모드1에서 측정된 것이 있다면 추가하기 위해 리스트로 관리)
    
    pass_count = 0
    fail_count = 0
    fail_cases = []

    for p_id, p_info in patterns.items():
        print(f"\n- -- {p_id} ---")
        
        # 1. 크기 추출 및 필터 매칭
        try:
            size_n = int(p_id.split('_')[1])
            filter_key = f"size_{size_n}"
            if filter_key not in filters:
                raise KeyError(f"필터 {filter_key}가 존재하지 않음")
            
            f_cross = filters[filter_key]['cross']
            f_x = filters[filter_key]['x']
            p_input = p_info['input']
            expected_raw = p_info['expected']
            
            # 2. 스키마 검증
            if len(f_cross) != size_n or len(p_input) != size_n:
                raise ValueError(f"크기 불일치: 필터({len(f_cross)}) vs 패턴({len(p_input)})")

            # 3. MAC 연산
            score_cross = calculate_mac(f_cross, p_input)
            score_x = calculate_mac(f_x, p_input)
            
            # 4. 판정 및 정규화
            expected_norm = normalize_label(expected_raw)
            
            if abs(score_cross - score_x) < EPSILON:
                detected = "UNDECIDED"
            else:
                detected = "Cross" if score_cross > score_x else "X"
            
            status = "PASS" if detected == expected_norm else "FAIL"
            
            print(f"Cross 점수: {score_cross:.16f}")
            print(f"X 점수: {score_x:.16f}")
            
            fail_reason = ""
            if detected == "UNDECIDED":
                fail_reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
            
            print(f"판정: {detected} | expected: {expected_norm} | {status} {fail_reason}")
            
            if status == "PASS":
                pass_count += 1
            else:
                fail_count += 1
                fail_cases.append(f"{p_id}: {fail_reason if fail_reason else '판정 불일치'}")

            # 5. 성능 측정 데이터 수집 (중복 크기는 한 번만 기록)
            if not any(d['size'] == f"{size_n}x{size_n}" for d in perf_data):
                avg_t = measure_performance(f_cross, p_input, size_n)
                perf_data.append({"size": f"{size_n}x{size_n}", "time": avg_t, "ops": size_n**2})

        except Exception as e:
            print(f"[ERROR] {p_id} 처리 실패: {e}")
            fail_count += 1
            fail_cases.append(f"{p_id}: {e}")

    return pass_count, fail_count, fail_cases, perf_data

def main():
    print("\n\n\n=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    
    choice = input("선택: ")
    
    perf_3x3 = None
    if choice == '1':
        perf_3x3 = run_mode_1()
    
    # 모드 2는 항상 실행하거나 선택적으로 실행 가능 (요구사항에 따라 흐름 구성)
    # 여기서는 요구사항의 '실행 흐름'에 따라 순차적으로 진행할 수 있도록 구성합니다.
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("data.json 파일을 찾을 수 없습니다.")
        return

    if choice == '2':
        pass_c, fail_c, fail_list, perf_list = run_mode_2(data)
        
        # 성능 분석 표 출력
        print("\n\n#---------------------------------------")
        print("# [3] 성능 분석 (평균/10회)")
        print("#---------------------------------------")
        print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수':<10}")
        print("-" * 40)
        
        # 3x3 데이터가 있다면 추가
        if perf_3x3:
            print(f"{perf_3x3['size']:<10} {perf_3x3['time']:<15.6f} {perf_3x3['ops']:<10}")
        
        for p in perf_list:
            print(f"{p['size']:<10} {p['time']:<15.6f} {p['ops']:<10}")

        print("\n\n#---------------------------------------")
        print("# [4] 결과 요약")
        print("#---------------------------------------")
        print(f"총 테스트: {pass_c + fail_c}개")
        print(f"통과: {pass_c}개")
        print(f"실패: {fail_c}개")
        if fail_list:
            print("\n\n실패 케이스:")
            for case in fail_list:
                print(f"- {case}")
        print("\n\n")

if __name__ == "__main__":
    main()