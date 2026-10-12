from pathlib import Path


def pytest_configure(config):
    Path("work").mkdir(exist_ok=True)
