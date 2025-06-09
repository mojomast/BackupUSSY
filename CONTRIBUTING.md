# Contributing to BackupUSSY

Thank you for your interest in contributing to BackupUSSY! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

- Windows 10/11
- Python 3.7 or higher
- Git for version control
- LTO tape drive (for testing tape operations)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/backupussy.git
   cd backupussy
   ```

2. **Install Dependencies**
   ```bash
   # Run the installer
   .\install.ps1
   
   # Or manually:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize Database**
   ```bash
   python src/database_init.py
   ```

4. **Run Tests**
   ```bash
   python src/test_runner.py
   ```

## Contributing Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Keep line length under 100 characters

### Documentation

- Update README.md for new features
- Add inline comments for complex logic
- Update CHANGELOG.md for all changes
- Include docstrings with examples where helpful

### Testing

- Write tests for new functionality
- Ensure all existing tests pass
- Test on Windows 10 and 11 if possible
- Include edge cases in your tests

### Commit Messages

Use clear, descriptive commit messages:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(archive): add compression level selection
fix(gui): resolve progress bar update issue
docs(readme): update installation instructions
```

## Areas for Contribution

### High Priority

1. **Testing**: More comprehensive test coverage
2. **Documentation**: Additional examples and tutorials
3. **Error Handling**: Improved error messages and recovery
4. **Performance**: Optimization for large archives

### Medium Priority

1. **UI/UX**: Interface improvements and usability
2. **Logging**: Enhanced logging and monitoring
3. **Configuration**: More configuration options
4. **Validation**: Better input validation

### Future Features

1. **Web Interface**: Remote management capabilities
2. **Barcode Support**: Label generation and scanning
3. **Incremental Backups**: Differential archive support
4. **Network Integration**: Remote tape libraries

## Development Workflow

### Project Structure

```
src/
├── main.py              # Dependency management
├── gui.py               # Main GUI application
├── archive_manager.py   # Archive creation logic
├── tape_manager.py      # Tape operations
├── logger_manager.py    # Logging system
├── database_manager.py  # SQLite database
├── recovery_manager.py  # File recovery
├── search_interface.py  # Search functionality
├── advanced_search.py   # Advanced search GUI
├── tape_browser.py      # Tape content browser
├── tape_library.py      # Tape library management
├── database_init.py     # Database initialization
├── test_runner.py       # Test suite
└── test_recovery.py     # Recovery tests
```

### Key Components

- **Managers**: Core functionality classes
- **GUI**: PySimpleGUI interface components
- **Database**: SQLite schema and operations
- **Tests**: Comprehensive test coverage
- **Installation**: Automated setup scripts

## Submitting Changes

### Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write your code
   - Add tests
   - Update documentation

3. **Test Thoroughly**
   ```bash
   python src/test_runner.py
   .\validate_phase2.ps1
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

### PR Requirements

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] No merge conflicts
- [ ] Descriptive PR title and description

## Reporting Issues

### Bug Reports

Include the following information:

- **System Information**:
  - Windows version
  - Python version
  - BackupUSSY version
  - Tape drive model

- **Steps to Reproduce**:
  1. Specific actions taken
  2. Expected behavior
  3. Actual behavior

- **Log Files**:
  - Relevant log entries from `logs/`
  - Error messages
  - Screenshots if applicable

### Issue Template

```markdown
**System Information**
- OS: Windows 10/11
- Python: 3.x.x
- BackupUSSY: v1.x.x
- Tape Drive: Model name

**Description**
Clear description of the issue.

**Steps to Reproduce**
1. Step one
2. Step two
3. ...

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Logs**
```
Paste relevant log entries here
```

**Screenshots**
If applicable.
```

## Feature Requests

When requesting new features:

1. **Check existing issues** for similar requests
2. **Describe the use case** and problem being solved
3. **Propose a solution** if you have one in mind
4. **Consider the scope** and complexity
5. **Discuss implementation** approach

## Development Tips

### Testing

- Use the test runner: `python src/test_runner.py`
- Test with different folder sizes and types
- Validate on both Windows 10 and 11
- Test error conditions and edge cases

### Debugging

- Enable verbose logging in the application
- Use the validation script: `.\validate_phase2.ps1`
- Check log files in `logs/` directory
- Use Python debugger for complex issues

### Performance

- Profile tape operations with large datasets
- Monitor memory usage during archives
- Test with different compression settings
- Validate database performance with many records

## Getting Help

- **GitHub Issues**: Ask questions or report problems
- **Code Review**: Request feedback on your changes
- **Documentation**: Refer to README.md and inline comments
- **Testing**: Use the comprehensive test suite

## Recognition

Contributors will be acknowledged in:
- CHANGELOG.md for their contributions
- README.md credits section
- Git commit history

Thank you for helping make BackupUSSY better! 🎉

