class Greeter:
    """A friendly greeter."""

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

    def farewell(self) -> str:
        return f"Goodbye, {self.name}!"

greeter = Greeter("World")
print(greeter.greet())
