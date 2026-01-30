#include <iostream>
#include <vector>

// Sum elements using range-based for
template<typename T>
T sum(const std::vector<T>& values) {
    T total = 0;
    for (const auto& v : values) {
        total += v;
    }
    return total;
}
