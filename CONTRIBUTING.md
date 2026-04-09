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
│   └── templates/         # Bundled project templates (single source of truth)
├── docs/                  # Framework documentation
├── scripts/               # Legacy standalone scripts
├── examples/              # Example projects and case studies
└── pyproject.toml         # Package metadata
```

## From Battle Report to Featured Example

Myco is a living substrate — its framework knowledge grows as more projects complete Gear 4 distillation. Your project experience can become part of Myco's knowledge base through a three-level contribution pipeline:

### Level 1: Discussion Post (low bar, anyone can do this)

Post in [GitHub Discussions → Show & Tell](https://github.com/Battam1111/Myco/discussions). Share your project background, which Myco features you used, and what you learned. A few paragraphs is enough. You don't need to have completed Gear 4.

### Level 2: Battle Report (medium bar, after at least one Gear 3)

Submit a [Battle Report issue](https://github.com/Battam1111/Myco/issues/new?template=battle_report.md) with project statistics, evolution timeline, key learnings, and improvement suggestions. This gives the community concrete data on how Myco performs across project types.

### Level 3: Featured Example (high bar, requires Gear 4)

If your project completes the full Myco lifecycle including Gear 4 distillation, it can become a Featured Example in `examples/`. This is the highest-impact contribution — it demonstrates Myco's core value proposition (knowledge evolving and flowing between projects).

**What a Featured Example includes:**
- Harvest snapshot: structure files from your completed project (MYCO.md, _canon.yaml, log.md, WORKFLOW.md — content can be redacted where needed)
- Evolution Timeline: how your knowledge system grew from `myco init` to Gear 4
- Gear 4 reverse link: what universal patterns were distilled, and where they now live in Myco's `docs/`
- Your Gear 4 distillation products themselves — submitted as a PR to Myco's `docs/`

**Acceptance criteria (v0.x):** The distilled knowledge must be useful to at least two project types, not just your own. The maintainer reviews this qualitatively.

See [`examples/ascc/`](examples/ascc/) for what a Featured Example looks like.

## Discussions

For questions, ideas, and open-ended conversations, use [GitHub Discussions](https://github.com/Battam1111/Myco/discussions):

- **Show & Tell**: Share what Myco evolved into on your project (Level 1 contribution)
- **Ideas**: Propose new features or directions
- **Q&A**: Ask questions about usage or architecture

## License

By contributing to Myco, you agree that your contributions will be licensed under the MIT License.
