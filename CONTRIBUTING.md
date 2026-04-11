# Contributing to Myco

Thank you for your interest in Myco! This project is in early development (v0.x) and we welcome contributions of all kinds.

## What We Value Most

Myco's community is different from typical open-source projects. The most valuable contributions aren't just code — they're **knowledge evolution products**: artifacts that improve Myco's ability to evolve knowledge across any project type.

There are four formal contribution types, each with a clear acceptance bar. Code contributions are also welcome, but these four types are what drive Myco's core value forward.

---

## Four Formal Contribution Types

### 1. Adapters
**What:** A YAML manifest in `docs/adapters/` that defines how an external tool integrates with Myco's four-layer architecture.

**Why this matters:** Every adapter makes Myco accessible to a new user segment. A Hermes user who finds an adapter can migrate in 30 minutes instead of 3 hours.

**Format:** Follow the schema in [`docs/adapters/README.md`](docs/adapters/README.md). Include `import_steps`, `layer_mapping`, `lint_checks`, `value_proposition`, and `roadmap`.

**Acceptance criteria:**
- Tested manually on ≥1 real project (your own counts)
- All lint checks in the YAML actually pass after running `myco lint`
- `docs/adapters/README.md` table updated with your adapter entry

**Effort estimate:** 1-2 hours. This is the fastest path to a merged contribution. Start here.

---

### 2. Wiki Templates
**What:** A `.md` file in `examples/templates/` defining a wiki page structure for a specific project type or domain.

**Why this matters:** The blank wiki page is one of Myco's highest-friction moments. A good template for "data science project" or "API integration" eliminates that friction.

**Format:** W8-compliant header (`type: template | date: today`), descriptive sections with comments explaining what belongs where, Back-to footer. See existing wiki pages for reference.

**Acceptance criteria:**
- Used on ≥1 real project (not just drafted in the abstract)
- W8 header fields filled correctly (type, date, cross-references)
- Comments explain the *why* of each section, not just the label

**Effort estimate:** 30 minutes if you already have a working wiki page from your own project.

---

### 3. Lint Rules
**What:** A proposed new consistency check for `myco lint`, submitted as a GitHub Discussion + (optionally) a pull request to `src/myco/lint.py`.

**Why this matters:** Lint rules are Myco's immune system. Each new rule is a pattern of failure that was caught in the real world.

**Submission path:**
1. Open a Discussion in [Ideas](https://github.com/Battam1111/Myco/discussions) describing: what inconsistency the rule catches, what real bug it would have caught, and what a failing example looks like
2. If the discussion gets traction (≥3 upvotes or maintainer approval), open a PR

**Acceptance criteria:**
- Must have caught ≥1 real bug in a real project (not a hypothetical)
- False positive rate must be low (doesn't flag valid structures)
- Clearly documented: what it checks, why it matters, what failure looks like

**Effort estimate:** Discussion post = 20 minutes. Implementation PR = 2-4 hours depending on complexity.

---

### 4. Workflow Principles
**What:** A proposed new W-number principle (W13, W14, …) or refinement to an existing principle (W1-W12), submitted as a GitHub Discussion.

**Why this matters:** The W1-W12 principles are Myco's core protocol. A new principle validated across multiple project types strengthens the universal framework.

**Submission path:** Open a Discussion in [Ideas](https://github.com/Battam1111/Myco/discussions) with: the principle's name and one-sentence statement, the failure mode it prevents, and at least two project types where it applies.

**Acceptance criteria:**
- Demonstrated validity on ≥2 distinct project types (not just your own)
- Doesn't conflict with or duplicate W1-W12
- Clear statement: "W13: [Name] — [One sentence]. Violation looks like: [example]."

**Effort estimate:** 30-60 minutes. Maintainer may request a follow-up 传统手艺 debate before accepting.

---

## Your First Contribution

**Fastest path:** Write an adapter for a tool you already use.

If you use Hermes Agent, OpenClaw, Obsidian, MemPalace, or any other knowledge/memory tool alongside Myco, you already have everything needed for an adapter contribution. The adapter YAML captures what you learned doing the integration manually. It's the most direct way to contribute real value with minimal effort.

Start here: read [`docs/adapters/README.md`](docs/adapters/README.md), copy an existing adapter YAML, and fill in your tool's details.

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
│   ├── lint.py            # 15-dimension consistency checker (L0-L14, contract v0.8.0)
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
