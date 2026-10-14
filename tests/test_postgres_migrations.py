import os
import subprocess

import pytest


@pytest.mark.integration
def test_alembic_upgrade_head_against_postgresql():
    """Validate the complete migration chain against an operator-provided PostgreSQL database."""
    if os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1":
        pytest.skip("set RUN_POSTGRES_MIGRATION_TESTS=1 to run against PostgreSQL")

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
