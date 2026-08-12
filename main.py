#!/usr/bin/env python3
import json
import time
import statistics
import sys

EPSILON = 1e-9


def normalize_label(label):
    if not isinstance(label, str):
        return label
    text = label.strip()
    if text == '+':
        return 'Cross'
    if text.lower() == 'x':
        return 'X'
    if text.lower() == 'cross':
        return 'Cross'
    return text


def format_score(score):
    if abs(score - round(score)) < EPSILON:
        return f"{round(score):.1f}"
    return f"{score:.16f}"


def mac_score(matrix_a, matrix_b):
    total = 0.0
    for i in range(len(matrix_a)):
        row_a = matrix_a[i]
        row_b = matrix_b[i]
        for j in range(len(row_a)):
            total += row_a[j] * row_b[j]
    return total


def timed_mac(matrix_a, matrix_b, repeats=1):
    times = []
    score = None
    for _ in range(repeats):
        start = time.perf_counter()
        score = mac_score(matrix_a, matrix_b)
        end = time.perf_counter()
        times.append((end - start) * 1000.0)
    average_ms = statistics.mean(times) if times else 0.0
    return average_ms, score


def read_matrix_interactive(name, n=3):
    print(f"\n[{name}] {n}x{n} 행렬을 입력하세요. 각 행은 공백으로 구분된 {n}개의 숫자입니다.")
    matrix = []
    for row_index in range(n):
        while True:
            raw = input(f"{row_index+1}행: ").strip()
            parts = raw.split()
            if len(parts) != n:
                print("입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요.")
                continue
            try:
                row = []
                for token in parts:
                    row.append(float(token))
                matrix.append(row)
                break
            except ValueError:
                print("입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요.")
    return matrix


def print_title():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]\n")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")


def read_menu_selection():
    while True:
        selection = input("선택: ").strip()
        if selection in ('1', '2'):
            return selection
        print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


def interactive_mode():
    print("#----------------------------------------")
    print("# [1] 사용자 입력 (3x3)")
    print("#----------------------------------------")
    filter_a = read_matrix_interactive('필터 A', 3)
    filter_b = read_matrix_interactive('필터 B', 3)
    pattern = read_matrix_interactive('패턴', 3)

    t_a, score_a = timed_mac(filter_a, pattern, repeats=10)
    t_b, score_b = timed_mac(filter_b, pattern, repeats=10)
    avg_time = (t_a + t_b) / 2.0

    print("\n#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")
    print(f"A 점수: {format_score(score_a)}")
    print(f"B 점수: {format_score(score_b)}")
    print(f"연산 시간(평균/10회): {avg_time:.3f} ms")

    if score_a > score_b + EPSILON:
        result = 'A'
    elif score_b > score_a + EPSILON:
        result = 'B'
    else:
        result = '판정 불가 (|A-B| < 1e-9)'

    print(f"판정: {result}")


def validate_matrix_shape(matrix, n):
    if not isinstance(matrix, list) or len(matrix) != n:
        return False
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return False
        for value in row:
            if not isinstance(value, (int, float)):
                return False
    return True


def extract_size_key(pattern_key):
    parts = pattern_key.split('_')
    if len(parts) < 2:
        return None
    if parts[0] != 'size':
        return None
    return f"size_{parts[1]}"


def batch_mode(data):
    print("#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")

    filters = data.get('filters', {})
    patterns = data.get('patterns', {})
    for size_key in sorted(filters.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0):
        size_info = filters[size_key]
        if isinstance(size_info, dict) and 'cross' in size_info and 'x' in size_info:
            print(f"✓ {size_key}  필터 로드 완료 (Cross, X)")
        else:
            print(f"✗ {size_key}  필터 정보 누락")

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")

    total = 0
    passed = 0
    failed = 0
    fail_cases = []
    perf_summary = {}

    for pattern_key in sorted(patterns.keys()):
        total += 1
        pattern_info = patterns[pattern_key]
        input_matrix = pattern_info.get('input')
        expected_raw = pattern_info.get('expected', '')
        expected_label = normalize_label(expected_raw)
        size_key = extract_size_key(pattern_key)
        size_n = None
        if size_key is not None and size_key in filters:
            try:
                size_n = int(size_key.split('_')[1])
            except ValueError:
                size_n = None

        status = 'PASS'
        reason = ''
        detected = 'UNDECIDED'
        score_cross = 0.0
        score_x = 0.0
        time_cross = 0.0
        time_x = 0.0

        if size_key is None or size_key not in filters:
            status = 'FAIL'
            reason = '필터 크기 불일치 또는 키 형식 오류'
        elif size_n is None:
            status = 'FAIL'
            reason = '패턴 키에서 크기를 파싱할 수 없음'
        elif not validate_matrix_shape(input_matrix, size_n):
            status = 'FAIL'
            reason = f'{size_n}x{size_n} 패턴 데이터 형식 오류'
        else:
            filter_set = filters[size_key]
            if not validate_matrix_shape(filter_set.get('cross', []), size_n) or not validate_matrix_shape(filter_set.get('x', []), size_n):
                status = 'FAIL'
                reason = f'{size_n}x{size_n} 필터 데이터 형식 오류'
            else:
                time_cross, score_cross = timed_mac(filter_set['cross'], input_matrix, repeats=10)
                time_x, score_x = timed_mac(filter_set['x'], input_matrix, repeats=10)
                if score_cross > score_x + EPSILON:
                    detected = 'Cross'
                elif score_x > score_cross + EPSILON:
                    detected = 'X'
                else:
                    detected = 'UNDECIDED'

                if expected_label not in ('Cross', 'X'):
                    status = 'FAIL'
                    reason = 'expected 값이 Cross/X 또는 +/x 형태가 아닙니다'
                elif detected != expected_label:
                    status = 'FAIL'
                    if detected == 'UNDECIDED':
                        reason = '동점 규칙에 따른 UNDECIDED'
                    else:
                        reason = '판정 결과가 예상과 다릅니다'

        print(f"- -- {pattern_key} ---")
        print(f"Cross 점수: {format_score(score_cross)}")
        print(f"X 점수: {format_score(score_x)}")
        if status == 'FAIL' and detected == 'UNDECIDED' and reason == '동점 규칙에 따른 UNDECIDED':
            print(f"판정: {detected} | expected: {expected_label} | FAIL (동점 규칙)")
        elif status == 'FAIL' and reason:
            print(f"판정: {detected} | expected: {expected_label} | FAIL ({reason})")
        else:
            print(f"판정: {detected} | expected: {expected_label} | {status}")

        if status == 'PASS':
            passed += 1
        else:
            failed += 1
            fail_cases.append({'case': pattern_key, 'reason': reason})

        if size_n is not None and size_n > 0:
            perf_summary.setdefault(size_n, []).append(time_cross)
            perf_summary.setdefault(size_n, []).append(time_x)

    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print('-' * 45)
    for size in sorted(perf_summary.keys()):
        avg_time = statistics.mean(perf_summary[size]) if perf_summary[size] else 0.0
        print(f"{size}x{size:<8} {avg_time:<15.3f} {size * size}")

    print("\n#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")
    if failed > 0:
        print("\n실패 케이스:")
        for fail_case in fail_cases:
            print(f"- {fail_case['case']}: {fail_case['reason']}")


def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print_title()
    selection = read_menu_selection()
    if selection == '1':
        interactive_mode()
    else:
        try:
            data = load_data('data.json')
        except FileNotFoundError:
            print('오류: data.json 파일을 찾을 수 없습니다.')
            return
        except json.JSONDecodeError:
            print('오류: data.json 파일을 읽는 중 JSON 형식 오류가 발생했습니다.')
            return
        batch_mode(data)


if __name__ == '__main__':
    main()
