# Development Log

## Day 1 — Development Environment Setup

### 1. Project Objective

Explain that the project will estimate the incremental effect of customer incentives on conversion. Mention that the project uses uplift modeling rather than only predicting whether a customer will convert.

### 2. Project Directory

Explain why the project uses separate folders for:

- Raw data
- Processed data
- Jupyter notebooks
- Source code
- Saved models
- Figures
- Reports

### 3. Python Environment

Record:

- Python version
- Operating system
- Why Python was selected
- Why a virtual environment was created
- The location of the project

Explain that the virtual environment isolates this project’s dependencies from other Python projects.

### 4. Installed Libraries

For every library, explain its purpose:

- Pandas for loading and manipulating tables
- NumPy for numerical arrays and calculations
- Scikit-learn for preprocessing, splitting data, and baseline models
- LightGBM for a tree-based baseline
- PyTorch for the multi-tower neural network
- Matplotlib and Seaborn for visualization
- Jupyter for interactive experimentation

### 5. Hardware Acceleration

Record:

- PyTorch version
- MPS availability
- Why MPS is useful
- Whether training will use Apple GPU acceleration or CPU fallback

Explain that MPS allows PyTorch to use Apple Silicon GPU hardware through Metal Performance Shaders.

### 6. Installation Problem

Describe the LightGBM error in your own words:

- LightGBM was installed successfully.
- It could not start because macOS could not find `libomp.dylib`.
- `libomp` provides the OpenMP runtime required for CPU parallelism.
- Homebrew was used to install the missing dependency.
- The import test succeeded afterward.

### 7. Verification

Record the final verification result:

- All core libraries imported successfully.
- PyTorch loaded successfully.
- MPS was available.
- The environment is ready for data processing and model development.

### 8. Day 1 Conclusion

Explain that the environment setup is complete and that the next step is downloading and inspecting the Starbucks dataset.