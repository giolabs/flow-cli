# Contributing to Flow CLI

We love your input! We want to make contributing to Flow CLI as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/flowstore/flow-cli.git
   cd flow-cli
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all checks:
```bash
make lint
```

Format code:
```bash
make format
```

## Testing

We use pytest for testing. Run tests with:

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run fast (parallel)
make test-fast

# Run specific test file
pytest tests/test_doctor.py
```

### Writing Tests

- Write unit tests for all new functionality
- Use meaningful test names that describe what is being tested
- Mock external dependencies
- Test edge cases and error conditions
- Aim for >80% code coverage

Example test structure:
```python
class TestCommandName:
    """Test suite for command_name command"""
    
    def test_success_case(self, cli_runner, mock_deps):
        """Test successful execution"""
        # Test implementation
        
    def test_error_case(self, cli_runner, mock_deps):
        """Test error handling"""
        # Test implementation
        
    def test_performance(self, cli_runner, performance_timer):
        """Test performance requirements"""
        # Performance test
```

## Documentation

- Update documentation for any new features
- Add docstrings to all functions and classes
- Update README.md if necessary
- Update command help text

Generate documentation:
```bash
python scripts/generate_docs.py
```

## Commit Messages

Use clear and meaningful commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
Add deployment keystore generation

- Implement Android keystore creation with keytool
- Add iOS certificate setup instructions
- Include security warnings and .gitignore protection
- Update deployment workflow documentation

Closes #123
```

## Branching Strategy

- `main`: Stable release branch
- `develop`: Development branch for next release
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Emergency fixes for production

## Release Process

1. Create release branch from `develop`
2. Update version numbers
3. Update CHANGELOG.md
4. Run full test suite
5. Create PR to `main`
6. Tag release after merge
7. Merge back to `develop`

## Issue and Bug Reports

Use GitHub Issues to report bugs. Please include:

1. **Environment details:**
   - Operating system and version
   - Python version
   - Flow CLI version
   - Flutter version

2. **Clear reproduction steps:**
   - What you did
   - What you expected to happen
   - What actually happened

3. **Additional context:**
   - Error messages (full stack trace)
   - Relevant configuration
   - Sample project (if applicable)

### Bug Report Template

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment:**
 - OS: [e.g. macOS 13.0]
 - Python Version: [e.g. 3.11.0]
 - Flow CLI Version: [e.g. 1.0.0]
 - Flutter Version: [e.g. 3.13.0]

**Additional context**
Add any other context about the problem here.
```

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists
2. Check if there's already an issue for it
3. Provide clear use cases
4. Consider implementation complexity
5. Be open to discussion and iteration

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## Code Review Process

All submissions require review. We use GitHub pull requests for this purpose.

### Review Criteria

- **Functionality**: Does the code work as intended?
- **Tests**: Are there adequate tests?
- **Performance**: Does it meet performance requirements?
- **Security**: Are there any security concerns?
- **Documentation**: Is it properly documented?
- **Style**: Does it follow our coding standards?

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass and provide good coverage
- [ ] Documentation is updated
- [ ] No breaking changes (or properly communicated)
- [ ] Performance is acceptable
- [ ] Security considerations addressed

## Community Guidelines

### Our Pledge

We are committed to making participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated promptly and fairly.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Questions?

Feel free to open an issue for any questions about contributing!

## Acknowledgments

Thank you for considering contributing to Flow CLI! Your contributions help make Flutter development better for everyone.