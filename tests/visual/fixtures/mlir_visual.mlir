// Matrix multiply operation
func.func @matmul(%A: memref<64x64xf32>,
                   %B: memref<64x64xf32>,
                   %C: memref<64x64xf32>) {
  affine.for %i = 0 to 64 {
    affine.for %j = 0 to 64 {
      %sum = arith.constant 0.0 : f32
      affine.store %sum, %C[%i, %j] : memref<64x64xf32>
    }
  }
  return
}
