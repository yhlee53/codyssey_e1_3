import json
import time
import numpy as np

def calculate_mac(filter_matrix, pattern_matrix):
    """MAC(Multiply-Accumulate) 연산을 수행합니다."""
    f = np.array(filter_matrix)
    p = np.array(pattern_matrix)
    # 요소별 곱셈 후 전체 합산
    return np.sum(f * p)

def get_3x3_input(prompt):
    """사용자로부터 3x3 행렬을 입력받습니다."""
    print(f"\n[{prompt}] 3x3 행렬의 각 행을 공백으로 구분하여 입력하세요 (예: 1 0 1):")
    matrix = []
    for i in range(3):
        while True:
            try:
                row = list(map(float, input(f"{i+1}행: ").split()))
                if len(row) != 3:
                    raise ValueError
                matrix.append(row)
                break
            except ValueError:
                print("오류: 3개의 숫자를 정확히 입력해주세요.")
    return matrix

def run_user_input_mode():
    print("\n" + "="*50)
    print("모드 1: 사용자 3x3 입력 판정")
    filter_a = get_3x3_input("필터 A")
    filter_b = get_3x3_input("필터 B")
    pattern = get_3x3_input("패턴")

    start_time = time.perf_counter()
    score_a = calculate_mac(filter_a, pattern)
    score_b = calculate_mac(filter_b, pattern)
    end_time = time.perf_counter()

    duration_ms = (end_time - start_time) * 1000

    print(f"\n[결과]")
    print(f"- 필터 A 점수: {score_a:.4f}")
    print(f"- 필터 B 점수: {score_b:.4f}")
    print(f"- 연산 시간: {duration_ms:.4f} ms")
    
    if score_a > score_b:
        print("=> 최종 판정: 필터 A 승리")
    elif score_b > score_a:
        print("=> 최종 판정: 필터 B 승리")
    else:
        print("=> 최종 판정: 판정 불가 (동점)")

def run_json_analysis(data):
    print("\n" + "="*50)
    print("모드 2: JSON 데이터 일괄 분석")
    
    filters = data['filters']
    patterns = data['patterns']
    
    results = []
    performance_stats = {}

    for p_key, p_val in patterns.items():
        size_str = f"size_{len(p_val['input'])}"
        size_int = len(p_val['input'])
        
        f_cross = filters[size_str]['cross']
        f_x = filters[size_str]['x']
        pattern_in = p_val['input']
        expected = p_val['expected'] # '+' 또는 'x'

        # 성능 측정을 위한 반복 연산 (최소 100회)
        start_time = time.perf_counter()
        for _ in range(100):
            score_cross = calculate_mac(f_cross, pattern_in)
            score_x = calculate_mac(f_x, pattern_in)
        end_time = time.perf_counter()
        
        avg_time_ms = ((end_time - start_time) * 1000) / 200 # 2개 필터 x 100회
        
        # 판정 로직 (+는 cross와 매칭)
        if score_cross > score_x:
            detected = "+"
        elif score_x > score_cross:
            detected = "x"
        else:
            detected = "UNDECIDED"
        
        status = "PASS" if detected == expected else "FAIL"
        results.append({
            "id": p_key,
            "size": size_int,
            "expected": expected,
            "detected": detected,
            "status": status,
            "time": avg_time_ms
        })
        
        # 성능 통계 저장
        if size_int not in performance_stats:
            performance_stats[size_int] = []
        performance_stats[size_int].append(avg_time_ms)

    # 결과 출력
    print(f"{'ID':<12} | {'Size':<4} | {'Exp':<4} | {'Det':<4} | {'Status':<5}")
    print("-" * 45)
    pass_count = 0
    for r in results:
        print(f"{r['id']:<12} | {r['size']:<4} | {r['expected']:<4} | {r['detected']:<4} | {r['status']:<5}")
        if r['status'] == "PASS": pass_count += 1

    # 성능 리포트
    print("\n[성능 분석 리포트]")
    print(f"{'Size (NxN)':<10} | {'Avg Time (ms)':<15} | {'Ops (N^2)':<10}")
    print("-" * 40)
    for size in sorted(performance_stats.keys()):
        avg_t = sum(performance_stats[size]) / len(performance_stats[size])
        print(f"{size:<10} | {avg_t:<15.6f} | {size**2:<10}")

    # 최종 요약
    print(f"\n[최종 요약]")
    print(f"- 전체 테스트: {len(results)}")
    print(f"- 통과: {pass_count}")
    print(f"- 실패: {len(results) - pass_count}")
    if len(results) - pass_count > 0:
        print("- 실패 케이스 목록:", [r['id'] for r in results if r['status'] == "FAIL"])

if __name__ == "__main__":
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("오류: data.json 파일을 찾을 수 없습니다.")
        exit()

    # 실행 순서
    run_user_input_mode()
    run_json_analysis(data)