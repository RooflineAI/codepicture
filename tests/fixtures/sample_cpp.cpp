// Sample C++ code with templates, lambdas, and modern features
#include <iostream>
#include <vector>
#include <algorithm>
#include <memory>

template <typename T>
class Stack {
public:
    void push(T value) { data_.push_back(std::move(value)); }

    T pop() {
        T top = std::move(data_.back());
        data_.pop_back();
        return top;
    }

    [[nodiscard]] bool empty() const noexcept { return data_.empty(); }
    [[nodiscard]] size_t size() const noexcept { return data_.size(); }

private:
    std::vector<T> data_;
};

int main() {
    auto stack = std::make_unique<Stack<int>>();
    std::vector<int> values = {5, 3, 8, 1, 9};

    std::for_each(values.begin(), values.end(),
        [&stack](int v) { stack->push(v); });

    while (!stack->empty()) {
        std::cout << stack->pop() << "\n";
    }

    return 0;
}
