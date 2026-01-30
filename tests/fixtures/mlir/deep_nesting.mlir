module {
  func.func @nested_loops(%arg0: memref<64x64x64xf32>) {
    affine.for %i = 0 to 64 {
      affine.for %j = 0 to 64 {
        affine.for %k = 0 to 64 {
          %0 = affine.load %arg0[%i, %j, %k] : memref<64x64x64xf32>
          %1 = arith.mulf %0, %0 : f32
          affine.store %1, %arg0[%i, %j, %k] : memref<64x64x64xf32>
        }
      }
    }
    return
  }
}
