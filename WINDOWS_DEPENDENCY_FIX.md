# Fix for onnxruntime Installation Error on Windows

## Problem

When running `uv sync`, the build failed with:

```
error: Distribution `onnxruntime==1.24.0.dev20251031003 @ registry+https://pypi.org/simple` 
can't be installed because it doesn't have a source distribution or wheel for the current platform

You're on Windows (`win_amd64`), but `onnxruntime` (v1.24.0.dev20251031003) only has wheels 
for the following platforms: `manylinux_2_27_x86_64`, `manylinux_2_28_x86_64`, `macosx_14_0_arm64`
```

## Root Cause

The issue occurs because:

1. **Transitive Dependency**: A dependency (likely `sentence-transformers` or `unstructured`) was pulling in `onnxruntime==1.24.0.dev*`, a development pre-release version
2. **Windows Incompatibility**: This dev version only has wheels for Linux and macOS, not Windows
3. **Pre-release Resolution**: uv was configured to allow pre-release versions (`if-necessary-or-explicit`), causing it to use this incompatible development version

## Solution

### Changes Made

1. **Updated `pyproject.toml`**:
   - Added platform-specific constraint for `onnxruntime`: `"onnxruntime>=1.18.0,<1.24.0.dev; sys_platform == 'win32'"`
   - Pinned `tokenizers` to stable versions: `"tokenizers>=0.15.0,<0.22.0rc"` (to avoid pre-releases that require Rust)
   - Added `langsmith>=0.4.56` explicitly for LangSmith integration
   - Added comprehensive comments explaining Windows compatibility constraints

2. **Created `uv.toml`**:
   - Set `prerelease = "if-necessary"` to minimize use of pre-release versions
   - Documented that this prevents accidental installation of development wheels

### Key Configuration

```toml
[project]
dependencies = [
    # ... other dependencies ...
    # Pin onnxruntime and tokenizers to stable versions to avoid Windows compatibility issues
    # onnxruntime dev releases don't have Windows wheels
    # tokenizers pre-releases require Rust compilation
    "onnxruntime>=1.18.0,<1.24.0.dev; sys_platform == 'win32'",
    "tokenizers>=0.15.0,<0.22.0rc",
]

[tool.uv]
# Ensure uv resolves stable versions to avoid Windows compatibility issues
# See: uv.toml for detailed configuration
```

## How to Use

### Initial Setup

```bash
# Clear old venv if corrupted
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# Install with uv
uv sync
```

### If Still Having Issues

If file permission issues persist (Access denied errors), this is likely antivirus interference:

```bash
# Try with a slower installation rate to avoid lock contention
uv sync --no-build-isolation
```

## Result

✅ Dependencies now resolve correctly on Windows with stable versions only

## Files Modified

- `pyproject.toml` - Added version constraints and LangSmith dependency
- `uv.toml` - Created to configure uv prerelease handling

## Related Issues

- **onnxruntime**: Upstream issue with dev releases lacking Windows wheels
- **tokenizers**: Pre-releases require Rust compiler, stable versions have pre-built wheels
- **File permissions**: Windows antivirus (Windows Defender, etc.) may temporarily lock DLL files during installation

## Prevention

To prevent similar issues in the future:

1. Always pin dev/transitive dependencies that cause platform-specific issues
2. Use `sys_platform` markers for platform-specific constraints
3. Configure uv to prefer stable versions: `prerelease = "if-necessary"`
4. Regularly audit `uv.lock` for unexpected pre-release versions
