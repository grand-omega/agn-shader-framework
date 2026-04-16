"""Tests for the GPU memory calculator module."""

import pytest

from src.memory_calc import DType, MemoryUnit, convert_memory, estimate_tensor_count, tensor_size


class TestConvertMemory:
    """Tests for convert_memory function."""

    def test_convert_bytes_to_kb(self) -> None:
        assert convert_memory(1024, MemoryUnit.BYTES, MemoryUnit.KB) == 1.0

    def test_convert_gb_to_bytes(self) -> None:
        assert convert_memory(1, MemoryUnit.GB, MemoryUnit.BYTES) == 1073741824.0

    def test_convert_same_unit(self) -> None:
        assert convert_memory(42.5, MemoryUnit.MB, MemoryUnit.MB) == 42.5

    def test_convert_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            convert_memory(-1, MemoryUnit.BYTES, MemoryUnit.KB)


class TestTensorSize:
    """Tests for tensor_size function."""

    def test_tensor_size_1d(self) -> None:
        # 1024 elements * 1 byte each = 1024 bytes
        assert tensor_size((1024,), DType.INT8) == 1024.0

    def test_tensor_size_2d_float32(self) -> None:
        # 1024 * 1024 * 4 bytes = 4194304 bytes
        assert tensor_size((1024, 1024), DType.FLOAT32) == 4194304.0

    def test_tensor_size_in_mb(self) -> None:
        # 1024 * 1024 * 4 bytes = 4 MB
        assert tensor_size((1024, 1024), DType.FLOAT32, MemoryUnit.MB) == 4.0

    def test_tensor_size_empty_shape_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            tensor_size((), DType.FLOAT32)

    def test_tensor_size_zero_dim_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            tensor_size((1024, 0), DType.FLOAT32)


class TestEstimateTensorCount:
    """Tests for estimate_tensor_count function."""

    def test_estimate_exact_fit(self) -> None:
        # 8 GB / (1024*1024*4 bytes = 4 MB) = 2048 tensors
        assert estimate_tensor_count(8, MemoryUnit.GB, (1024, 1024), DType.FLOAT32) == 2048

    def test_estimate_partial_remainder(self) -> None:
        # 5 bytes / 2 bytes per tensor = 2 (floor)
        assert estimate_tensor_count(5, MemoryUnit.BYTES, (1,), DType.FLOAT16) == 2

    def test_estimate_large_vram_small_tensor(self) -> None:
        # 1 GB / 1 byte = 1073741824 tensors
        assert estimate_tensor_count(1, MemoryUnit.GB, (1,), DType.INT8) == 1073741824

    def test_estimate_tensor_larger_than_vram(self) -> None:
        # 1 byte of VRAM, tensor needs 4 bytes -> 0
        assert estimate_tensor_count(1, MemoryUnit.BYTES, (1,), DType.FLOAT32) == 0

    def test_estimate_negative_vram_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            estimate_tensor_count(-1, MemoryUnit.GB, (1024,), DType.FLOAT32)
