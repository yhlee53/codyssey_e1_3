import json
import time
# 파일 상단에 import 추가
from read import load_json_data

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

def calculate_mac_optimized(filter_1d, pattern_1d):
    """
    최적화된 MAC 연산: 1차원 배열을 사용하여 단일 루프로 처리
    """
    total_sum = 0.0
    # 단일 루프로 인덱싱 오버헤드 최소화
    for i in range(len(filter_1d)):
        total_sum += filter_1d[i] * pattern_1d[i]
    return total_sum

def flatten_matrix(matrix):
    """
    2차원 리스트를 1차원 리스트로 변환
    """
    return [item for row in matrix for item in row]

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

def generate_patterns(n):
    """
    N x N 크기의 Cross와 X 패턴을 생성
    """
    # 0.0으로 초기화된 N x N 행렬 생성
    cross_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    x_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    
    mid = n // 2
    for r in range(n):
        for c in range(n):
            # 십자가 로직: 중앙 행 또는 중앙 열
            if r == mid or c == mid:
                cross_matrix[r][c] = 1.0
            
            # X 로직: 주 대각선 또는 부 대각선
            if r == c or (r + c) == (n - 1):
                x_matrix[r][c] = 1.0
                
    return cross_matrix, x_matrix

def run_mode_3():
    print("\n#---------------------------------------")
    print("# [3] 패턴 자동 생성 및 성능 분석")
    print("#---------------------------------------")
    try:
        n = int(input("생성할 패턴의 크기 N을 입력하세요 (예: 5, 13, 25, 100): "))
        if n <= 0: raise ValueError
    except ValueError:
        print("올바른 양의 정수를 입력하세요.")
        return

    cross_p, x_p = generate_patterns(n)
    
    # 생성된 패턴 확인 (작은 크기일 때만 출력)
    if n <= 10:
        print(f"\n[생성된 {n}x{n} Cross 패턴]")
        for row in cross_p: print(row)
        print(f"\n[생성된 {n}x{n} X 패턴]")
        for row in x_p: print(row)
    else:
        print(f"\n{n}x{n} 패턴 생성 완료 (크기가 커서 출력은 생략합니다.)")

    # 성능 측정 (생성된 패턴을 필터이자 패턴으로 가정하여 연산)
    avg_t = measure_performance(cross_p, x_p, n)
    
    print("\n[성능 결과]")
    print(f"크기: {n}x{n}")
    print(f"연산 횟수: {n*n}회")
    print(f"평균 실행 시간: {avg_t:.6f} ms")
    
    return {"size": f"{n}x{n}", "time": avg_t, "ops": n*n}

def run_mode_4():
    print("\n#---------------------------------------")
    print("# [4] MAC 연산 최적화 성능 비교 (2D vs 1D)")
    print("#---------------------------------------")
    try:
        n = int(input("비교할 패턴의 크기 N을 입력하세요 (예: 100, 200, 500): "))
        if n <= 0: raise ValueError
    except ValueError:
        print("올바른 양의 정수를 입력하세요.")
        return

    # 1. 데이터 준비 (2차원 및 1차원)
    cross_2d, x_2d = generate_patterns(n)
    cross_1d = flatten_matrix(cross_2d)
    x_1d = flatten_matrix(x_2d)

    print(f"\n[실험 환경] 크기: {n}x{n} | 총 원소 수: {n*n}개")
    print("측정 중... (각 방식 10회 반복 평균)")

    # 2. 기존 방식 (2D) 성능 측정
    start_2d = time.perf_counter()
    for _ in range(10):
        calculate_mac(cross_2d, x_2d)
    end_2d = time.perf_counter()
    avg_2d = ((end_2d - start_2d) / 10) * 1000

    # 3. 최적화 방식 (1D) 성능 측정
    start_1d = time.perf_counter()
    for _ in range(10):
        calculate_mac_optimized(cross_1d, x_1d)
    end_1d = time.perf_counter()
    avg_1d = ((end_1d - start_1d) / 10) * 1000

    # 4. 결과 출력
    print("\n#---------------------------------------")
    print(f"{'연산 방식':<20} | {'평균 실행 시간(ms)':<20}")
    print("-" * 45)
    print(f"{'기존 방식 (2D Loop)':<20} | {avg_2d:<20.6f} ms")
    print(f"{'최적화 방식 (1D Loop)':<20} | {avg_1d:<20.6f} ms")
    print("-" * 45)

    if avg_1d > 0:
        speedup = avg_2d / avg_1d
        print(f"성능 향상: 약 {speedup:.2f}배 빨라짐")
    
    print("\n* 1D 방식이 빠른 이유: 중첩 루프의 인덱싱 오버헤드가 줄어들고 메모리 접근이 연속적이기 때문입니다.")

def main():
    print("\n\n\n=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. 패턴 자동 생성 및 성능 테스트") # 추가    
    print("4. [최적화] 1D vs 2D 성능 비교") # 추가

    choice = input("\n선택: ")
    
    perf_3x3 = None
    if choice == '1':
        perf_3x3 = run_mode_1()
    
    # 모드 2는 항상 실행하거나 선택적으로 실행 가능 (요구사항에 따라 흐름 구성)
    # 여기서는 요구사항의 '실행 흐름'에 따라 순차적으로 진행할 수 있도록 구성합니다.
    elif choice == '2':
        # [수정된 부분] read.py의 함수를 호출합니다.
        data = load_json_data('data.json')
        
        # 데이터 로드에 실패(None)했다면 종료
        if data is None:
            return
        
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
    elif choice == '3':
        run_mode_3() # 추가
    elif choice == '4':
            run_mode_4() # 호출

if __name__ == "__main__":
    main()