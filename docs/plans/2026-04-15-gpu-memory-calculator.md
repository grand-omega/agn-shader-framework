# Plan: GPU Memory Calculator
Date: 2026-04-15
Status: Draft

## Problem statement

We need a pure-Python module that performs GPU memory arithmetic: converting
between byte units (bytes, KB, MB, GB), calculating the memory footprint of
tensors given their shape and dtype, and estimating how many tensors of a given
specification fit in a given VRAM budget. No actual GPU hardware is required;
this is a planning/estimation utility.

## Research findings

- No external dependencies are needed. Python's `math.prod` (3.8+) handles
  shape-element counting. The `enum` module provides a clean dtype registry.
- The project already follows a one-module-per-file layout with Google-style
  docstrings and full type hints (see `src/main.py`).
- Existing tests import from `src.*` and use plain pytest (see
  `tests/test_main.py`).
- Standard dtype sizes:
  - int8: 1 byte
  - int16 / float16 / bfloat16: 2 bytes
  - int32 / float32: 4 bytes
  - int64 / float64: 8 bytes

## Dependencies needed

None. Pure Python standard library only.

## Approach

Create a single module `src/memory_calc.py` containing:

1. **`MemoryUnit` enum** -- members `BYTES`, `KB`, `MB`, `GB` each carrying a
   multiplier (1, 1024, 1024^2, 1024^3). Uses binary (IEC) convention since
   GPU VRAM is universally reported in powers of 1024.

2. **`DType` enum** -- members for each supported dtype, each carrying its
   size in bytes. String values match common names (e.g., `"float32"`).

3. **`convert_memory(value, from_unit, to_unit) -> float`** -- pure unit
   conversion.

4. **`tensor_size(shape, dtype, unit) -> float`** -- computes the memory
   footprint of one tensor. `shape` is a tuple of ints, `dtype` is a `DType`,
   `unit` defaults to `MemoryUnit.BYTES`.

5. **`estimate_tensor_count(vram, vram_unit, shape, dtype) -> int`** --
   returns how many whole tensors fit. Uses floor division.

All functions are stateless, side-effect-free, and trivially testable.

## Task breakdown

### Task 1: Create `src/memory_calc.py` with enums and `convert_memory`

**Files to create/modify:**
- `src/memory_calc.py` -- new file

**What to implement:**

```
class MemoryUnit(enum.Enum):
    BYTES = 1
    KB = 1024
    MB = 1024 ** 2
    GB = 1024 ** 3

class DType(enum.Enum):
    FLOAT16 = ("float16", 2)
    FLOAT32 = ("float32", 4)
    FLOAT64 = ("float64", 8)
    BFLOAT16 = ("bfloat16", 2)
    INT8 = ("int8", 1)
    INT16 = ("int16", 2)
    INT32 = ("int32", 4)
    INT64 = ("int64", 8)

    # Properties: .name_str -> str, .itemsize -> int

def convert_memory(value: float, from_unit: MemoryUnit, to_unit: MemoryUnit) -> float
```

- `convert_memory` should raise `ValueError` if `value` is negative.

**Tests to write:**
- `tests/test_memory_calc.py::test_convert_bytes_to_kb`
- `tests/test_memory_calc.py::test_convert_gb_to_bytes`
- `tests/test_memory_calc.py::test_convert_same_unit`
- `tests/test_memory_calc.py::test_convert_negative_raises`

**Verification:** `uv run pytest tests/test_memory_calc.py -v`

### Task 2: Add `tensor_size` function

**Files to modify:**
- `src/memory_calc.py`

**What to implement:**

```
def tensor_size(
    shape: tuple[int, ...],
    dtype: DType,
    unit: MemoryUnit = MemoryUnit.BYTES,
) -> float
```

- Uses `math.prod(shape) * dtype.itemsize` then converts to requested unit.
- Raises `ValueError` if any dimension is non-positive.

**Tests to write:**
- `tests/test_memory_calc.py::test_tensor_size_1d`
- `tests/test_memory_calc.py::test_tensor_size_2d_float32`
- `tests/test_memory_calc.py::test_tensor_size_in_mb`
- `tests/test_memory_calc.py::test_tensor_size_empty_shape_raises`
- `tests/test_memory_calc.py::test_tensor_size_zero_dim_raises`

**Verification:** `uv run pytest tests/test_memory_calc.py -v`

### Task 3: Add `estimate_tensor_count` function

**Files to modify:**
- `src/memory_calc.py`

**What to implement:**

```
def estimate_tensor_count(
    vram: float,
    vram_unit: MemoryUnit,
    shape: tuple[int, ...],
    dtype: DType,
) -> int
```

- Converts `vram` to bytes, computes tensor size in bytes, returns
  `int(vram_bytes // tensor_bytes)`.
- Raises `ValueError` if vram is negative.

**Tests to write:**
- `tests/test_memory_calc.py::test_estimate_exact_fit`
- `tests/test_memory_calc.py::test_estimate_partial_remainder`
- `tests/test_memory_calc.py::test_estimate_large_vram_small_tensor`
- `tests/test_memory_calc.py::test_estimate_tensor_larger_than_vram`
- `tests/test_memory_calc.py::test_estimate_negative_vram_raises`

**Verification:** `uv run pytest tests/test_memory_calc.py -v`

### Task 4: Final integration pass

- Run full test suite: `uv run pytest --cov=src`
- Run linter: `uv run ruff check .`
- Run formatter: `uv run ruff format .`
- Confirm all tests pass and no lint errors.

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Floating-point precision in unit conversion | Low | Use exact integer multipliers (powers of 1024); only final result is float division. Tests should use `pytest.approx` where needed. |
| Confusion between SI (1000) and binary (1024) units | Low | Document that we use binary (IEC) convention throughout. Enum multipliers make this unambiguous. |
| `math.prod` unavailable | Very low | Requires Python 3.8+; project targets 3.12+. |

## Success criteria

1. `uv run pytest tests/test_memory_calc.py` passes all tests (minimum 14 test cases).
2. `uv run ruff check src/memory_calc.py` reports zero errors.
3. `convert_memory(1, MemoryUnit.GB, MemoryUnit.BYTES)` returns `1073741824.0`.
4. `tensor_size((1024, 1024), DType.FLOAT32)` returns `4194304.0` (4 MB in bytes).
5. `estimate_tensor_count(8, MemoryUnit.GB, (1024, 1024), DType.FLOAT32)` returns `2048`.
6. All edge cases (negative values, zero dimensions, empty shapes) raise `ValueError`.
7. No external dependencies added to `pyproject.toml`.
