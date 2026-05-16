# Enterprise Web Development System

A production-grade subagent system for web development with integrated Enterprise Code Compliance (ECC) tools.

## Features

- **Multi-Agent Architecture**: Specialized agents for frontend, backend, database, QA, and DevOps
- **ECC Integration**: Comprehensive security, stability, performance, and maintainability scanning
- **Quality Gates**: Automated quality checks before deployment
- **Professional Standards**: Enterprise-level code quality and security compliance

## Architecture

```
enterprise-web-dev-system/
├── .agents/              # Specialized subagents
│   ├── orchestrator/     # Central coordination
│   ├── frontend-agent/   # React/TypeScript development
│   ├── backend-agent/    # FastAPI/Python development
│   ├── database-agent/   # PostgreSQL schema design
│   ├── qa-agent/         # Testing automation
│   └── devops-agent/     # Infrastructure setup
├── ecc_tools/            # Enterprise Code Compliance
│   ├── security/         # SAST, SCA, secret scanning
│   ├── stability/        # Complexity analysis
│   ├── performance/      # Profiling and optimization
│   └── maintainability/  # Code metrics and smells
└── config/               # System configuration
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create New Project

```bash
python main.py --workflow new-project \
  --project ./my-enterprise-app \
  --requirements requirements.yaml
```

### 3. Run ECC Scan

```bash
python main.py --ecc-scan --project ./my-enterprise-app --output html
```

### 4. Add Feature

```bash
python main.py --workflow feature-dev \
  --project ./my-enterprise-app \
  --feature "user-authentication"
```

## ECC Tools

### Security (SAST)
- SQL Injection detection
- Command Injection detection
- XSS vulnerability scanning
- Hardcoded secret detection
- Path traversal detection
- SSRF detection
- Insecure deserialization detection
- Taint analysis

### Stability
- Cyclomatic complexity analysis
- Cognitive complexity analysis
- Exception handling verification
- Type annotation coverage
- Resource leak detection
- Concurrency issue detection

### Performance
- Algorithmic complexity detection
- Memory usage analysis
- Database N+1 query detection
- Caching opportunity detection
- Blocking operation detection in async code

### Maintainability
- Halstead metrics calculation
- Maintainability Index
- Code smell detection
- SOLID principles checking
- Documentation coverage

## Quality Gates

The system enforces quality gates before deployment:

- **Security**: 0 critical findings, max 5 high
- **Stability**: 0 critical issues
- **Performance**: 0 critical issues
- **Maintainability**: MI >= 70

## Configuration

Edit `config/agents.yaml` to customize:
- Agent capabilities and priorities
- Quality gate thresholds
- Communication protocols
- Logging settings

Edit `config/ecc.yaml` to customize:
- Security scanning rules
- Stability thresholds
- Performance benchmarks
- Maintainability standards

## License

MIT License - Enterprise Edition
