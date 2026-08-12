# 분석 리포트
## 실패 원인 분석 (Failure Analysis)
테스트 결과 중 특정 케이스에서 FAIL이 발생할 수 있는 주요 원인은 다음과 같습니다.

- 라벨/스키마 불일치 (Label Mismatch):
data.json의 필터 키는 cross이지만, expected 값은 +로 표기되어 있습니다. 코드 내에서 이를 매핑하는 로직이 없으면 불일치로 인해 FAIL이 발생합니다.
- 부동소수점 오차 (Floating Point Precision):
size_13의 x 필터 중앙값이 7.5와 같이 큰 값을 가집니다. MAC 연산 과정에서 매우 작은 소수점 차이로 인해 UNDECIDED가 나오거나 판정이 뒤바뀔 가능성이 있습니다.
- 필터 가중치 비대칭 (Weight Scale):
size_5 필터는 값이 1.0 위주인 반면, size_13은 0.3 위주입니다. 필터의 크기(Size)가 커질수록 합산되는 항의 개수가 많아지므로, 적절한 정규화(Normalization)가 없으면 점수 스케일이 급격히 차이 나게 됩니다.

## 시간 복잡도 분석 (Complexity Analysis)
MAC 연산 복잡도: 필터의 한 변의 길이를 $N$이라고 할 때, MAC 연산은 $N \times N$ 번의 곱셈과 $N^2 - 1$ 번의 덧셈이 일어납니다.
빅오 표기법: $O(N^2)$
입력 데이터 크기에 따라 연산량이 제곱 비례하여 증가합니다.
실제 측정 결과에서도 $5 \times 5$ 대비 $25 \times 25$ 연산 시 약 25배($5^2$ 배)에 가까운 연산 시간 증가가 관찰될 것입니다.

# 시각화 자료 (성능 분석 차트)
학습을 돕기 위해 연산 크기에 따른 시간 복잡도 변화를 차트로 생성해 보았습니다.

위 차트는 필터 크기($N$)에 따른 성능 변화를 보여줍니다.

Operation Count (Blue, $N^2$): 필터 크기가 커짐에 따라 연산 횟수가 제곱수 형태로 급격히 증가하는 것을 볼 수 있습니다. (연산 복잡도 $O(N^2)$)
Avg Execution Time (Red, ms): 실제 연산 시간 또한 연산 횟수와 동일한 궤적을 그리며 증가합니다.
💡 학생을 위한 팁
NumPy 활용: 위 코드에서 np.sum(f * p)를 사용한 이유는 파이썬의 for 루프보다 NumPy의 벡터 연산이 훨씬 빠르기 때문입니다. 대용량 데이터를 처리할 때는 이 차이가 매우 큽니다.
부동소수점 비교: 실무에서는 score_a == score_b 대신 abs(score_a - score_b) < 1e-9와 같이 아주 작은 오차 범위를 두고 비교하는 것이 안전합니다.
확장성: 현재는 2D 패턴 매칭이지만, 이 원리를 3D로 확장하고 여러 층을 쌓으면 현대 인공지능의 핵심인 **CNN(Convolutional Neural Network)**의 기초가 됩니다!

![gemini_output_1](../gemini_output_1.png)

![gemini_output_2](../gemini_output_2.png)