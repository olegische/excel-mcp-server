"""Setup script for building Cython extensions for the excel_mcp project.

This script handles the compilation of Python source files to C++ using Cython,
providing both optimization and code obfuscation benefits.
"""

import os
from typing import List, Tuple

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

# Compiler directives for maximum obfuscation
COMPILER_DIRECTIVES = {
    "language_level": "3",
    "embedsignature": False,  # Hide function signatures
    "binding": False,  # Remove introspection metadata
    "linetrace": False,  # Disable line tracing
    "c_string_type": "unicode",
    "c_string_encoding": "utf8",
    "infer_types": True,  # Automatic type inference for optimization
    "emit_code_comments": False,  # Remove comments from C code
    "nonecheck": False,  # Disable None checks for speed
    "optimize.use_switch": True,  # Optimize if-elif-else constructs
    "boundscheck": False,  # Disable array bounds checking
    "wraparound": False,  # Disable negative index wrapping
    "cdivision": True,  # Use C division (faster)
}


def get_py_files() -> List[Tuple[str, str]]:
    """Recursively collect Python files from the src/excel_mcp directory.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing:
            - module_path: Python import path
            - file_path: actual file location
    """
    py_files = []
    for root, _, files in os.walk("src/excel_mcp"):
        for file in files:
            if file.endswith(".py"):
                py_path = os.path.join(root, file)
                module_path = (
                    os.path.relpath(py_path, "src").replace("/", ".").replace(".py", "")
                )
                py_files.append((module_path, py_path))

    # Log for debugging
    print("Compiling modules:")
    for module, path in py_files:
        print(f"  - {module} ({path})")

    return py_files


extensions = [
    Extension(
        module,
        [path],
        language="c++",
        extra_compile_args=[
            "-O3",  # Maximum optimization
            "-march=native",  # Optimize for target CPU
            "-mtune=native",  # Fine-tune for target CPU
            "-fPIC",  # Position Independent Code
            "-ffast-math",  # Aggressive math optimization
            "-funroll-loops",  # Loop unrolling
            "-flto",  # Link Time Optimization
        ],
        extra_link_args=[
            "-Wl,-s",  # Strip symbols during linking
        ],
    )
    for module, path in get_py_files()
]

setup(
    name="excel_mcp",
    ext_modules=cythonize(
        extensions,
        compiler_directives=COMPILER_DIRECTIVES,
        nthreads=os.cpu_count(),  # Parallel compilation
    ),
    zip_safe=False,
)
