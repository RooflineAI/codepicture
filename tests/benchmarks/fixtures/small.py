def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.

    Args:
        n: The position in the sequence (0-indexed).

    Returns:
        The Fibonacci number at position n.
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
