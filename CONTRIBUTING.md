# Contributing to GitHub Contributors Analyzer

Thank you for your interest in contributing to GitHub Contributors Analyzer! This document provides guidelines and information for contributors.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/GH-Contributors-Analyzer.git
   cd GH-Contributors-Analyzer
   ```
3. **Set up the development environment**:
   ```bash
   make setup
   ```

## 🛠️ Development Workflow

### Setting Up Your Environment

```bash
# Install dependencies
make install

# Start MongoDB for testing
make start-db

# Copy environment template
cp .env.example .env
# Edit .env with your GitHub token
```

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Run tests** to ensure everything works:
   ```bash
   make test
   ```

4. **Format your code**:
   ```bash
   make format
   ```

5. **Run linting**:
   ```bash
   make lint
   ```

6. **Run type checking**:
   ```bash
   make type-check
   ```

### Submitting Changes

1. **Commit your changes** with a clear message:
   ```bash
   git commit -am "Add feature: description of your changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub

## 📋 Coding Standards

- **Python Style**: Follow PEP 8, enforced by `black` and `flake8`
- **Type Hints**: Use type hints for all functions and methods
- **Docstrings**: Document all public functions and classes
- **Async/Await**: Use async/await for I/O operations
- **Error Handling**: Proper exception handling with logging

## 🧪 Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting
- Use mocks for external API calls
- Test both success and error scenarios

## 📝 Documentation

- Update README.md if you add new features
- Add docstrings to new functions and classes
- Update type hints and examples

## 🐛 Bug Reports

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs

## 💡 Feature Requests

For feature requests, please:
- Check if it already exists in issues
- Describe the use case
- Explain why it would be valuable
- Consider implementation complexity

## 📞 Getting Help

- Check the README.md for setup instructions
- Look at existing issues and discussions
- Create an issue for questions or problems

Thank you for contributing! 🎉
