module {
  func.func @"quoted.symbol.name"() {
    ^entry:
      %0 = "dialect.custom_op"() {attr = 0xFF00 : i32, name = "hello\nworld"} : () -> i64
      %1 = arith.constant 3.14e-5 : f64
      %2 = arith.constant 0x7FC00000 : f32
      cf.br ^exit
    ^exit:
      return
  }
}
