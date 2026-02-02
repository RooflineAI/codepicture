module attributes {stream.topology = #hal.device.topology<links = [
  (@device_a -> @device_b = {unified_memory = true, transparent_access = true}),
  (@device_b -> @device_a = {unified_memory = true, transparent_access = true})]>} {
  util.global private @device_a : !hal.device
  util.global private @device_b : !hal.device
  func.func @simple_quant_matmul(...) {
    ...
    %1 = hal.tensor.import on(#hal.device.affinity<@device_a>) ...
    %2 = linalg.generic ins(%1) ... -> tensor<...>
    %3 = flow.tensor.transfer %2 to #hal.device.affinity<@device_b>
    %4 = neutronstub.operator(%3, ...) {stream.affinity = #hal.device.affinity<@device_b>}
    %5 = flow.tensor.transfer %4 to #hal.device.affinity<@device_a>
    return %5
  }
}