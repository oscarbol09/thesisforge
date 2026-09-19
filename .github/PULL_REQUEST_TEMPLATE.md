## 📌 Description

Please include a summary of the change and which issue it fixes. Also include relevant context, motivation, and design decisions.

Fixes # (issue)

---

## 🛠️ Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 📚 Documentation update (docs, tutorials, guidelines)
- [ ] ⚡ Performance optimization
- [ ] 🛡️ Security enhancement (SSRF, sanitization, encryption)
- [ ] 🧪 Testing improvement (new unit, integration, or property tests)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)

---

## ✅ Quality Checklist

Please ensure the following checks pass before requesting a review:

- [ ] **Tests:** My changes include unit, integration, or property tests, and the full suite passes:
  ```bash
  pytest tests/ -v --cov=thesisforge
  ```
- [ ] **Type Checking:** Strict type analysis passes with zero errors:
  ```bash
  mypy --strict src/
  ```
- [ ] **Linting & Formatting:** Code adheres to style guides with Ruff:
  ```bash
  ruff check src/ tests/
  ruff format --check src/ tests/
  ```
- [ ] **Security:** Bandit SAST audit reports zero medium/high severity issues:
  ```bash
  bandit -r src/ -ll
  ```
- [ ] **Async Non-blocking:** No blocking calls (`requests.get`, `time.sleep`, sync I/O) in `async def`.
- [ ] **UTC Timestamps:** All datetime instantiations use `timezone.utc`.
- [ ] **Documentation:** I have updated relevant docstrings and documentation files (if applicable).
