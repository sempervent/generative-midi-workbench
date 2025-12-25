# Project Template

A clean, stack-agnostic GitHub template repository with MkDocs (Material theme) for documentation, automatic GitHub Pages deployment, and quality-of-life defaults.

## Features

- 📚 **MkDocs with Material theme** - Modern, responsive documentation
- 🚀 **GitHub Pages deployment** - Automatic deployment via GitHub Actions
- 🔧 **Pre-commit hooks** - Keep the repo clean with automated checks
  - YAML/JSON linting, markdown formatting, Python docstring checks
  - Conventional commits enforcement with Commitizen
- ✨ **Conventional Commits** - Structured commit messages with Commitizen
- 🤖 **Dependabot** - Automated dependency updates for Actions and Docker
- 📝 **Issue templates** - Structured bug reports and feature requests
- 🐳 **Docker support** - Dockerized local docs for tool-agnostic teams
- ⚙️ **Makefile** - Simple commands for common tasks
- 🔍 **CI Workflows** - Automated linting and validation on every PR

## Using this template

1. Click **Use this template** → **Create a new repository**.

2. Edit `mkdocs.yml` (update `site_name`, `repo_url`, `site_url`, and `repo_name`) and the pages under `docs/`.

3. Configure GitHub Pages:
   - Go to **Settings** → **Pages**
   - Under **Build and deployment**, select **Source: GitHub Actions**
   - After the first push to `main`, your site will auto-deploy

4. Push to `main`. GitHub Pages will auto-deploy via Actions.

5. Install development tools (optional but recommended):

   ```bash
   # Install pre-commit (for hooks)
   pip install pre-commit
   make install-hooks

   # Install Commitizen (for conventional commits and versioning)
   pip install commitizen
   # Or with pipx
   pipx install commitizen
   ```

6. Local preview:

   ```bash
   # Option A: pipx (recommended)
   pipx install mkdocs-material
   mkdocs serve
   
   # Option B: pip
   python -m pip install --upgrade pip
   pip install mkdocs mkdocs-material
   mkdocs serve
   
   # Option C: Docker
   docker build -t mkdocs-local -f Dockerfile.docs .
   docker run --rm -it -p 8000:8000 -v "$PWD":/site mkdocs-local
   ```

## Quick Start Commands

```bash
# Build documentation
make docs

# Start local development server
make dev

# Run pre-commit checks
make check

# Install pre-commit hooks (run once)
make install-hooks

# Commit using conventional commits (interactive)
make commit

# Bump version (creates tag and updates CHANGELOG)
make version

# Generate changelog from commits
make changelog
```

## Quality of Life Features

### Conventional Commits with Commitizen

This template includes [Commitizen](https://commitizen-tools.readthedocs.io/) for enforcing conventional commits:

```bash
# Use the interactive commit helper
make commit

# Or install the hook to enforce on every commit
make install-hooks
```

Commit types follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI configuration changes
- `chore`: Other changes

### Pre-commit Hooks

Automatic checks run before commits:
- ✅ YAML/JSON validation and linting
- ✅ Markdown linting and formatting
- ✅ Python docstring style checks (Google convention)
- ✅ Conventional commit message validation
- ✅ Large file detection
- ✅ Private key detection
- ✅ Merge conflict detection

Install hooks:
```bash
make install-hooks
```

### Automated Version Management

Bump versions and generate changelogs automatically:

```bash
# Bump version (patch/minor/major based on commits)
make version

# Generate CHANGELOG.md from commit history
make changelog
```

### Dependabot

Automatically keep dependencies updated:
- ✅ GitHub Actions updates (weekly)
- ✅ Docker image updates (weekly)
- ✅ Python dependencies (when added - uncomment in `.github/dependabot.yml`)

### CI/CD Workflows

- **`docs-lint.yml`**: Lints markdown files and validates MkDocs config on PRs
- **`pre-commit.yml`**: Runs full pre-commit checks in CI
- **`pages.yml`**: Builds and deploys documentation to GitHub Pages

## Project Structure

```
project-template/
├── docs/                    # Documentation source files
│   ├── index.md
│   └── getting-started.md
├── .github/
│   ├── workflows/
│   │   ├── pages.yml       # GitHub Pages deployment workflow
│   │   ├── docs-lint.yml   # Documentation linting workflow
│   │   └── pre-commit.yml  # Pre-commit checks in CI
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   ├── CODEOWNERS          # Code ownership rules
│   └── dependabot.yml      # Dependabot configuration
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── .cz.toml                # Commitizen configuration
├── .markdownlint.json      # Markdown linting rules
├── mkdocs.yml             # MkDocs configuration
├── Makefile                 # Common tasks
├── Dockerfile.docs         # Docker image for local docs
├── .editorconfig          # Editor configuration
├── .gitignore             # Git ignore rules
├── CHANGELOG.md           # Auto-generated changelog
├── LICENSE                # MIT License
└── README.md              # This file
```

## Customization

### Adding More Documentation Pages

1. Create new `.md` files in the `docs/` directory
2. Add them to the `nav` section in `mkdocs.yml`

### Adding Language-Specific Files

This template is intentionally stack-agnostic. You can add language-specific files after creating a repo from the template:

- **Python**: Add `requirements.txt`, `setup.py`, or `pyproject.toml`
- **Node.js**: Add `package.json`, `package-lock.json`
- **Rust**: Add `Cargo.toml`
- etc.

### Versioned Documentation

To add versioning to your documentation later, consider using the [mike](https://github.com/jimporter/mike) plugin for MkDocs.

## License

MIT License - see [LICENSE](LICENSE) file for details.

