// MLIR sample demonstrating various syntax constructs
module {
  // Function with SSA values and types
  func.func @add_vectors(%arg0: tensor<4xf32>, %arg1: tensor<4xf32>) -> tensor<4xf32> {
    // Arithmetic operation with result binding
    %0 = arith.addf %arg0, %arg1 : tensor<4xf32>

    // Constants of different types
    %c42 = arith.constant 42 : i32
    %cst = arith.constant 3.14159 : f64
    %true = arith.constant true

    // Memory operations
    %mem = memref.alloc() : memref<16x16xf32>

    // Affine operations with map
    affine.for %i = 0 to 16 {
      affine.store %cst, %mem[%i, %i] : memref<16x16xf32>
    }

    // Block with label
    cf.br ^bb1

  ^bb1:
    // String attribute
    "test.op"() {attr = "hello\nworld"} : () -> ()

    func.return %0 : tensor<4xf32>
  }
}
