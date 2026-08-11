#!/usr/bin/env python3
import json
import time
import datetime
import statistics
import sys


def mac_score(filt, pattern):
    # element-wise multiply-accumulate for same-shaped matrices
    s = 0.0
    for i in range(len(filt)):
        row_f = filt[i]
        row_p = pattern[i]
        for j in range(len(row_f)):
            s += row_f[j] * row_p[j]
    return s


def timed_mac(filt, pattern, repeats=1):
    # run MAC repeats times, return average elapsed_ms and last score
    times = []
    score = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        score = mac_score(filt, pattern)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    return statistics.mean(times), score


def read_matrix_interactive(name, n=3):
    print(f"{n}x{n} 행렬 '{name}'을(를) 입력하세요. 각 행은 공백으로 구분된 {n}개의 숫자입니다.")
    mat = []
    for i in range(n):
        while True:
            raw = input(f"{name} row {i+1}: ").strip()
            parts = raw.split()
            if len(parts) != n:
                print(f"{n}개의 값이 필요합니다. 다시 입력하세요.")
                continue
            try:
                row = [float(x) for x in parts]
                mat.append(row)
                break
            except ValueError:
                print("숫자 형식 오류. 다시 입력하세요.")
    return mat


def interactive_mode():
    print("콘솔 입력 모드: 두 개의 3x3 필터(A,B)와 3x3 패턴을 입력합니다.")
    A = read_matrix_interactive('A', 3)
    B = read_matrix_interactive('B', 3)
    P = read_matrix_interactive('pattern', 3)

    # measure each once (timing includes only one MAC)
    tA, sA = timed_mac(A, P, repeats=1)
    tB, sB = timed_mac(B, P, repeats=1)

    eps = 1e-9
    if sA > sB + eps:
        decision = 'A'
    elif sB > sA + eps:
        decision = 'B'
    else:
        decision = '판정 불가'

    print('\n결과:')
    print(f"A score: {sA:.6f}, time: {tA:.3f} ms")
    print(f"B score: {sB:.6f}, time: {tB:.3f} ms")
    print(f"판정: {decision}")


def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def batch_mode(data, min_repeats=10):
    filters = data['filters']
    patterns = data['patterns']

    results = []
    total = 0
    passed = 0
    failed = 0
    fails = []

    out_lines = []
    out_lines.append(f"Batch run: {datetime.datetime.now().isoformat()}")

    # performance summary per size
    perf_summary = {}

    # for each pattern, determine matching filter size
    for pname, pinfo in patterns.items():
        total += 1
        inp = pinfo['input']
        expected = pinfo.get('expected')

        # determine size prefix: size_5_x -> size_5
        size_key = pname.split('_')[0] + '_' + pname.split('_')[1] if '_' in pname else None
        # alternative: look for first part until second underscore
        # simpler: find keys in filters that match length
        n = len(inp)
        used_filter_key = None
        for fk in filters.keys():
            if int(fk.split('_')[1]) == n:
                used_filter_key = fk
                break

        if used_filter_key is None:
            print(f"패턴 {pname}에 맞는 필터 크기 없음, 건너뜀")
            continue

        fset = filters[used_filter_key]
        # determine repeats based on size
        repeats = max(min_repeats, 10000 // (n * n))

        # compute both scores with timing (average)
        t_cross, s_cross = timed_mac(fset['cross'], inp, repeats=repeats)
        t_x, s_x = timed_mac(fset['x'], inp, repeats=repeats)

        # decision
        eps = 1e-6
        if s_cross > s_x + eps:
            decision = 'cross'
        elif s_x > s_cross + eps:
            decision = 'x'
        else:
            decision = 'UNDECIDED'

        # map expected '+' -> 'cross'
        exp_map = {'+': 'cross', 'x': 'x'}
        exp_label = exp_map.get(expected, expected)
        passfail = 'PASS' if exp_label == decision else 'FAIL'
        if passfail == 'PASS':
            passed += 1
        else:
            failed += 1
            fails.append({'case': pname, 'expected': expected, 'decision': decision, 's_cross': s_cross, 's_x': s_x})

        results.append({
            'case': pname,
            'decision': decision,
            'expected': expected,
            's_cross': s_cross,
            's_x': s_x,
            't_cross_ms': t_cross,
            't_x_ms': t_x,
            'repeats': repeats,
            'ops': n * n
        })

        # accumulate perf summary
        if n not in perf_summary:
            perf_summary[n] = {'times': [], 'ops': n * n, 'count': 0}
        perf_summary[n]['times'].append(t_cross)
        perf_summary[n]['times'].append(t_x)
        perf_summary[n]['count'] += 2

    # print results per case
    out_lines.append('\n=== Batch 판정 결과 ===')
    print('\n=== Batch 판정 결과 ===')
    for r in results:
        status = 'PASS' if (r['expected'] == 'x' and r['decision'] == 'x') or (r['expected'] == '+' and r['decision'] == 'cross') else ('PASS' if r['expected'] == r['decision'] else 'FAIL' if r['decision'] != 'UNDECIDED' else 'FAIL')
        line = f"{r['case']}: decision={r['decision']}, expected={r['expected']}, {status}"
        out_lines.append(line)
        print(line)

    # performance table
    out_lines.append('\n=== 성능 분석 (평균) ===')
    out_lines.append('Size\tOps(N^2)\tAvg time (ms)\tSamples')
    print('\n=== 성능 분석 (평균) ===')
    print('Size\tOps(N^2)\tAvg time (ms)\tSamples')
    for n, info in sorted(perf_summary.items()):
        avg = statistics.mean(info['times']) if info['times'] else 0.0
        line = f"{n}\t{info['ops']}\t{avg:.6f}\t{info['count']}"
        out_lines.append(line)
        print(line)

    # final report summary
    out_lines.append('\n=== 리포트 요약 ===')
    summary = f"전체 케이스: {total}, PASS: {passed}, FAIL: {failed}"
    out_lines.append(summary)
    print('\n=== 리포트 요약 ===')
    print(summary)
    if fails:
        out_lines.append('실패 케이스 목록:')
        print('실패 케이스 목록:')
        for f in fails:
            line = f" - {f['case']}: expected={f['expected']}, decision={f['decision']}, s_cross={f['s_cross']:.6f}, s_x={f['s_x']:.6f}"
            out_lines.append(line)
            print(line)

    # write log file
    log_path = 'batch_report.log'
    try:
        with open(log_path, 'w', encoding='utf-8') as lf:
            lf.write('\n'.join(out_lines))
        print(f"\n로그 파일로 저장되었습니다: {log_path}")
    except Exception as e:
        print(f"로그 파일 저장 중 오류 발생: {e}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        path = sys.argv[2] if len(sys.argv) > 2 else 'data.json'
        data = load_data(path)
        batch_mode(data)
    else:
        interactive_mode()


if __name__ == '__main__':
    main()
