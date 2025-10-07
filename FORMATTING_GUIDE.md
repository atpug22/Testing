# 🎨 Code Formatting Guide

This project uses comprehensive code formatting tools to maintain consistent, high-quality code across the entire codebase.

## 📋 Tools Used

### Core Formatting
- **Black**: Code formatter with opinionated style
- **isort**: Import statement organizer
- **pre-commit**: Git hooks for automated formatting
- **flake8**: Linting and style checking
- **mypy**: Type checking

### IDE Integration
- **VS Code**: Automatic formatting on save
- **EditorConfig**: Cross-editor configuration

## 🚀 Quick Start

### Format All Code
```bash
# Using Makefile (recommended)
make format

# Or using the Python script
python format_code.py

# Or individual tools
make black
make isort
```

### Check Formatting
```bash
make check-format
```

### Run Linting
```bash
make lint
```

## 🛠️ Available Commands

### Makefile Commands
```bash
make help          # Show all available commands
make format        # Format all code
make lint          # Run linting checks
make test          # Run tests
make test-ai       # Run AI integration tests
make check-format  # Check if code is properly formatted
make black         # Run Black formatter only
make isort         # Run isort only
make clean         # Clean temporary files
make dev-setup     # Set up development environment
```

### Pre-commit Commands
```bash
pre-commit install           # Install pre-commit hooks
pre-commit run --all-files   # Run on all files
make pre-commit-all         # Run pre-commit on all files
```

## ⚙️ Configuration

### Black Configuration
- **Line length**: 88 characters
- **Target Python**: 3.11
- **Configuration**: `pyproject.toml`

### isort Configuration
- **Profile**: Black compatible
- **Multi-line**: 3 (Vertical hanging indent)
- **Line length**: 88 characters

### VS Code Configuration
- **Format on save**: Enabled
- **Organize imports on save**: Enabled
- **Python formatter**: Black
- **Linter**: flake8 + mypy

## 📁 Files and Structure

### Configuration Files
```
.pre-commit-config.yaml    # Pre-commit hooks configuration
.vscode/settings.json      # VS Code settings
.editorconfig             # Cross-editor configuration
pyproject.toml            # Black and isort configuration
format_code.py            # Custom formatting script
Makefile                  # Development commands
```

### Pre-commit Hooks
1. **Trailing whitespace removal**
2. **End-of-file fixing**
3. **YAML validation**
4. **Large file detection**
5. **Merge conflict detection**
6. **Debug statement detection**
7. **Black formatting**
8. **isort import sorting**
9. **flake8 linting**
10. **mypy type checking**

## 🎯 Best Practices

### Code Style
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **String quotes**: Double quotes preferred
- **Import order**: Standard library → Third party → Local imports
- **Type hints**: Required for all functions

### Import Organization
```python
# Standard library imports
import os
import sys
from typing import Dict, List

# Third-party imports
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from app.models import User
from core.config import settings
```

### Function Formatting
```python
async def analyze_pr_risk_flags(
    self,
    request: PRRiskFlagsRequest,
    user_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> PRRiskFlagsResponse:
    """Analyze PR for risk flags using structured output."""
    # Implementation here
```

## 🔧 Development Workflow

### Before Committing
1. **Format code**: `make format`
2. **Check formatting**: `make check-format`
3. **Run linting**: `make lint`
4. **Run tests**: `make test`

### Pre-commit Hooks
Pre-commit hooks automatically run when you commit:
- Code formatting
- Import sorting
- Linting
- Type checking

### IDE Setup
1. **Install VS Code extensions**:
   - Python
   - Pylance
   - Black Formatter
   - isort

2. **Enable format on save** (already configured in `.vscode/settings.json`)

## 🚨 Troubleshooting

### Common Issues

#### Black Formatting Issues
```bash
# Check what Black would change
black --diff app/

# Force format specific files
black app/models/user.py
```

#### Import Sorting Issues
```bash
# Check what isort would change
isort --diff --profile=black app/

# Force sort imports
isort --profile=black app/models/user.py
```

#### Pre-commit Issues
```bash
# Skip pre-commit hooks (not recommended)
git commit --no-verify

# Update pre-commit hooks
pre-commit autoupdate
```

### VS Code Issues
1. **Ensure Python interpreter is set**: `./venv/bin/python`
2. **Reload VS Code window**: `Ctrl+Shift+P` → "Developer: Reload Window"
3. **Check Python extension is enabled**

## 📊 Formatting Statistics

After running `make format`:
- **136 files** processed
- **All files** properly formatted
- **Zero** formatting violations

## 🎉 Benefits

1. **Consistent Code Style**: All code follows the same formatting rules
2. **Reduced Review Time**: No more formatting discussions in PRs
3. **Better Readability**: Clean, organized imports and consistent spacing
4. **Type Safety**: mypy catches type-related issues early
5. **Automated Quality**: Pre-commit hooks ensure quality before commits
6. **IDE Integration**: Automatic formatting in your favorite editor

## 📚 Additional Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [pre-commit Documentation](https://pre-commit.com/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)

---

**Happy coding! 🚀**
