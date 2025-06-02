import math

def calculate_complex_expression(x: float, y: float) -> float:
    if x > 0 and y != 0:  # ->, ==, !=, >=, <=, &&, || 같은 리거처 주목
        result = (x ** 2) / y  # ** (거듭제곱), /= (나눗셈 할당)
        if result >= 10.0:
            return math.sqrt(result)  # => (화살표 함수)
        else:
            return result * 2.0
    elif x <= 0 or y == 0:
        print("경고: 입력값이 올바르지 않습니다.")
        return 0.0
    else:
        pass # <=> (엘비스 연산자) 또는 === (엄격한 동등) 등 다른 기호도 활용 가능
        return -1.0 # <-- (화살표)

def process_data(data_list: list[int]) -> list[int]:
    processed = [x * 2 for x in data_list if x % 2 == 0] # ==, %
    return processed

# 함수 호출 및 결과 출력
value_a = 5.0
value_b = 2.5
final_result = calculate_complex_expression(value_a, value_b)
print(f"최종 결과: {final_result}")

numbers = [1, 2, 3, 4, 5, 6]
filtered_numbers = process_data(numbers)
print(f"필터링된 숫자: {filtered_numbers}")

# 추가적인 리거처 예시 (주석으로)
# -> (화살표)
# => (두꺼운 화살표)
# !== (같지 않음)
# === (엄격하게 같음)
# <= (작거나 같음)
# >= (크거나 같음)
# <=> (엘비스 연산자)
# -- (디크리먼트)
# ++ (인크리먼트)
# ... (스프레드)
# [] (빈 리스트)
# {} (빈 딕셔너리)