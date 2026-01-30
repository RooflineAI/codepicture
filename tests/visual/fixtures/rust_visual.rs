/// Calculate factorial recursively
fn factorial(n: u64) -> u64 {
    match n {
        0 | 1 => 1,
        _ => n * factorial(n - 1),
    }
}

fn main() {
    let result = factorial(10);
    println!("10! = {result}");
}
