module {
  func.func @wide_signature(%a0: f32, %a1: f32, %a2: f32, %a3: f32, %a4: f32, %a5: f32, %a6: f32, %a7: f32) -> (f32, f32, f32, f32) {
    %0 = arith.addf %a0, %a1 : f32
    %1 = arith.addf %a2, %a3 : f32
    %2 = arith.addf %a4, %a5 : f32
    %3 = arith.addf %a6, %a7 : f32
    return %0, %1, %2, %3 : f32, f32, f32, f32
  }
}
