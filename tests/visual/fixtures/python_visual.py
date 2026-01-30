# Fibonacci sequence generator
def fibonacci(n: int) -> list[int]:
    """Return first n Fibonacci numbers."""
    result = [0, 1]
    for i in range(2, n):
        result.append(result[-1] + result[-2])
    return result

print(fibonacci(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
