# Contributing to Myco

Thank you for your interest in Myco! This project is in early development (v0.x) and we welcome contributions of all kinds.

## What We Value Most

Myco's community is different from typical open-source projects. The most valuable contributions aren't just code — they're **knowledge evolution products**:

- **Battle reports**: Used Myco on a new project type? Tell us what worked, what didn't, and what the system evolved into.
- **Wiki templates**: Discovered a wiki page structure that works well for frontend projects, data analysis, or something else? Share it.
- **Lint rules**: Found a consistency check that catches real problems? Propose it.
- **Workflow principles**: Discovered a W13, W14, or a refinement to an existing principle? Open a discussion.
- **Adapters**: Built an integration with another tool (MemPalace, Hermes, etc.)? We'd love to see it.

## How to Contribute

### Reporting Issues

Use [GitHub Issues](https://github.com/Battam1111/Myco/issues) with the appropriate template:

- **Bug Report**: Something isn't working as expected
- **Feature Request**: An idea for improvement
- **Battle Report**: Share your experience using Myco on a real project

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Make your changes
4. Test locally:
   ```bash
   pip install -e .
   myco init test-project --level 2
   myco lint --project-dir test-project
   ```
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
pip install -e .

# Verify installation
myco --version
myco init /tmp/test-project --level 1
myco lint --project-dir /tmp/test-project
```

### Code Style

- Python 3.8+ compatibility
- Type hints where they add clarity
- Minimal external dependencies (currently only PyYAML)
- Docstrings on public functions

## Project Structure

```
Myco/
├── src/myco/              # Python package (pip installable)
│   ├── cli.py             # CLI dispatcher (myco init/migrate/lint)
│   ├── init_cmd.py        # Project initialization
│   ├── migrate.py         # Hot-start migration
│   ├── lint.py            # 9-dimension consistency checker
│   ├── templates.py       # Template resolution (importlib.resources)
│   └── templates/         # Bundled project templates
├── docs/                  # Framework documentation
├── templates/             # Source templates (development reference)
├── scripts/               # Legacy standalone scripts
├── examples/              # Example projects and case studies
└── pyproject.toml         # Package metadata
```

## Discussions

For questions, ideas, and open-ended conversations, use [GitHub Discussions](https://github.com/Battam1111/Myco/discussions):

- **Show & Tell**: Share what Myco evolved into on your project
- **Ideas**: Propose new features or directions
- **Q&A**: Ask questions about usage or architecture

## License

By contributing to Myco, you agree that your contributions will be licensed under the MIT License.
