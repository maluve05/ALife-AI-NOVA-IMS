# Contributing Guidelines

Thank you for your interest in contributing to the **Artificial Life & AI Simulation Platform** at NOVA IMS!

---

## 1. Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/maluve05/ALife-AI-NOVA-IMS.git
   cd ALife-AI-NOVA-IMS
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

---

## 2. Code Standards & Style

* **PEP 8**: Follow standard Python style guidelines.
* **Type Annotations**: Use Python `typing` type hints on all public functions, methods, and classes.
* **Docstrings**: Include descriptive docstrings detailing mathematical logic, input args, and return types.
* **Clean Formatting**: Use `ruff` or `black` for formatting.

---

## 3. Testing & Verification

Before opening a pull request, ensure all unit and integration tests pass:

```bash
# Run unit tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run headless simulation test
python main.py --headless --ticks 30 --seed 42

# Run telemetry analytics test
python Alife_Simulation/analyze.py --csv simulation_1.csv --no-plot
```

---

## 4. Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Commit your changes with clear, descriptive commit messages.
3. Push to your branch and open a Pull Request with a summary of the changes and validation results.
