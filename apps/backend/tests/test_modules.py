import importlib

import pytest
from django.apps import apps

MODULES = [
    "identity",
    "learner",
    "curriculum",
    "content",
    "exammodels",
    "practice",
    "simulation",
    "assessment",
    "prediction",
    "calibration",
    "billing",
    "engagement",
    "reporting",
    "admin",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_has_public_and_is_installed(name: str) -> None:
    importlib.import_module(f"modules.{name}.public")
    assert apps.is_installed(f"modules.{name}")
