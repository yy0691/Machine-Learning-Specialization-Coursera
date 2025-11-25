# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains solutions and notes for the **Machine Learning Specialization** by Andrew NG on Coursera. It includes Jupyter notebooks, Python utility functions, and translation tools for educational machine learning content.

## Repository Structure

### Course Organization
The repository is organized into three main courses:

- **C1 - Supervised Machine Learning - Regression and Classification/** (3 weeks)
  - Linear regression, logistic regression, regularization
- **C2 - Advanced Learning Algorithms/** (4 weeks) 
  - Neural networks, TensorFlow, decision trees
- **C3 - Unsupervised Learning, Recommenders, Reinforcement Learning/** (3 weeks)
  - K-means, anomaly detection, recommender systems, reinforcement learning

### Directory Structure
```
├── C[1-3] - [Course Name]/
│   ├── week[1-4]/
│   │   ├── Optional Labs/           # Educational notebooks
│   │   ├── C[X]W[Y]A[Z]/           # Programming assignments
│   │   └── Practice Quiz - [Topic]/ # Quiz materials
├── notebooks-zh/                   # Chinese translations
├── resources/                      # Images and assets
└── translate_notebooks.py         # Translation utility
```

## Development Environment

### Dependencies
This project uses Python with the following key libraries:
- **NumPy**: Scientific computing and linear algebra
- **Matplotlib**: Plotting and visualization  
- **TensorFlow**: Neural networks (C2 course)
- **scikit-learn**: Machine learning algorithms

### Jupyter Notebooks
All course content is delivered via Jupyter notebooks (.ipynb files):
- **Optional Labs**: Educational examples with step-by-step explanations
- **Programming Assignments**: Graded exercises with test utilities
- **Solutions**: Complete implementations with detailed comments

## Key Components

### Utility Libraries
Each week contains Python utility files providing:
- **lab_utils_common.py**: Common functions across all labs (plotting, cost calculation)
- **utils.py**: Assignment-specific helper functions
- **public_tests.py**: Unit tests for programming assignments
- Specialized utilities (e.g., `lab_utils_multi.py`, `recsys_utils.py`)

### Translation Infrastructure
- **translate_notebooks.py**: Automated translation tool for Chinese localization
- **notebooks-zh/**: Chinese translations maintaining original structure
- **翻译开发计划.md**: Translation development plan

## Common Development Tasks

### Running Notebooks
```bash
# Start Jupyter notebook server
jupyter notebook

# Run specific notebook
jupyter nbconvert --execute --to notebook [notebook_name].ipynb
```

### Working with Translations
```bash
# Run translation script
python translate_notebooks.py

# Install translation dependencies
pip install googletrans==4.0.0rc1
```

### File Navigation
- Assignment notebooks are in `C[X]/week[Y]/C[X]W[Y]A[Z]/` directories
- Utility functions are co-located with notebooks that use them
- Images and plots are referenced with relative paths to `./images/`

## Code Patterns and Conventions

### Notebook Structure
1. **Markdown cells**: Educational content, problem descriptions, mathematical formulas
2. **Code cells**: Implementation with detailed comments
3. **Output cells**: Results, plots, and validation output

### Function Naming
- `compute_*`: Mathematical computations (cost, gradient, prediction)
- `plt_*`: Plotting and visualization functions  
- `*_utils`: Utility modules for specific topics

### Mathematical Notation
- Uses LaTeX notation in markdown cells for formulas
- Variable names match mathematical notation (w, b, X, y, m)
- Extensive use of NumPy for vectorized operations

### Import Patterns
```python
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('./deeplearning.mplstyle')  # Consistent styling
```

## Special Considerations

### File Dependencies
- Notebooks depend on co-located utility files and style sheets
- Image paths are relative to notebook location
- Some notebooks require specific data files or pretrained models

### Translation Workflow
- Original English notebooks are in main directories
- Chinese translations preserve exact structure in `notebooks-zh/`
- Translation script handles markdown and code comments separately

### Assignment Structure  
- Programming assignments include test utilities and starter code
- Students implement specific functions marked with "### START CODE HERE ###"
- Public tests validate implementations without revealing full solutions

## Architecture Notes

This is an educational repository focused on learning machine learning concepts through hands-on implementation. The notebooks progress from basic linear regression to advanced topics like neural networks and reinforcement learning, with each building on previous concepts. The modular utility structure allows for code reuse across related assignments while maintaining clear separation between courses and topics.