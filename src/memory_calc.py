"""GPU memory calculation utilities.

Pure-Python module for converting between memory units, computing tensor
memory footprints, and estimating how many tensors fit in a VRAM budget.
Uses binary (IEC) convention throughout (powers of 1024).
"""

import enum
import math


class MemoryUnit(enum.Enum):
    """Memory size units using binary (IEC) convention."""

    BYTES = 1
    KB = 1024
    MB = 1024**2
    GB = 1024**3


class DType(enum.Enum):
    """Tensor data types with their per-element size in bytes."""

    FLOAT16 = ("float16", 2)
    FLOAT32 = ("float32", 4)
    FLOAT64 = ("float64", 8)
    BFLOAT16 = ("bfloat16", 2)
    INT8 = ("int8", 1)
    INT16 = ("int16", 2)
    INT32 = ("int32", 4)
    INT64 = ("int64", 8)

    def __init__(self, name_str: str, itemsize: int) -> None:
        self.name_str = name_str
        self.itemsize = itemsize


def convert_memory(value: float, from_unit: MemoryUnit, to_unit: MemoryUnit) -> float:
    """Convert a memory value between units.

    Args:
        value: The numeric amount to convert. Must be non-negative.
        from_unit: The source memory unit.
        to_unit: The target memory unit.

    Returns:
        The converted value as a float.

    Raises:
        ValueError: If value is negative.
    """
    if value < 0:
        raise ValueError(f"Memory value must be non-negative, got {value}")
    bytes_value = value * from_unit.value
    return bytes_value / to_unit.value


def tensor_size(
    shape: tuple[int, ...],
    dtype: DType,
    unit: MemoryUnit = MemoryUnit.BYTES,
) -> float:
    """Compute the memory footprint of a single tensor.

    Args:
        shape: Tuple of dimension sizes. Must be non-empty with all
            dimensions positive.
        dtype: The data type of each element.
        unit: The memory unit for the returned value. Defaults to BYTES.

    Returns:
        The tensor's memory size in the requested unit.

    Raises:
        ValueError: If shape is empty or contains a non-positive dimension.
    """
    if not shape:
        raise ValueError("Shape must not be empty")
    for dim in shape:
        if dim <= 0:
            raise ValueError(f"All dimensions must be positive, got {dim}")
    size_bytes = math.prod(shape) * dtype.itemsize
    return size_bytes / unit.value


def estimate_tensor_count(
    vram: float,
    vram_unit: MemoryUnit,
    shape: tuple[int, ...],
    dtype: DType,
) -> int:
    """Estimate how many whole tensors fit in a given VRAM budget.

    Args:
        vram: The available VRAM amount. Must be non-negative.
        vram_unit: The unit of the vram value.
        shape: Tuple of dimension sizes for each tensor.
        dtype: The data type of each tensor element.

    Returns:
        The number of whole tensors that fit (floor division).

    Raises:
        ValueError: If vram is negative, shape is empty, or dimensions
            are non-positive.
    """
    if vram < 0:
        raise ValueError(f"VRAM must be non-negative, got {vram}")
    vram_bytes = vram * vram_unit.value
    tensor_bytes = tensor_size(shape, dtype, MemoryUnit.BYTES)
    return int(vram_bytes // tensor_bytes)
