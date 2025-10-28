"""Tasks for maintaining the project.

Execute 'invoke --list' for guidance on using Invoke
"""

import platform
import webbrowser
from pathlib import Path

from invoke import Collection
from invoke import Context
from invoke import task
from invokelint import _clean
from invokelint import dist
from invokelint import lint
from invokelint import path
from invokelint import style
from invokelint import test

ns = Collection()
ns.add_collection(_clean, name="clean")
ns.add_collection(dist)
ns.add_collection(lint)
ns.add_collection(path)
ns.add_collection(style)
ns.add_collection(test)

ROOT_DIR = Path(__file__).parent
COVERAGE_DIR = ROOT_DIR.joinpath("htmlcov")
COVERAGE_REPORT = COVERAGE_DIR.joinpath("index.html")


@task(help={"publish": "Publish the result via coveralls", "xml": "Export report as xml format"})
def coverage(context: Context, *, publish: bool = False, xml: bool = False) -> None:
    """Create coverage report."""
    pty = platform.system() == "Linux"
    context.run("coverage run --concurrency=multiprocessing -m pytest", pty=pty)
    context.run("coverage combine", pty=pty)
    context.run("coverage report -m", pty=pty)
    if publish:
        # Publish the results via coveralls
        context.run("coveralls", pty=pty)
        return
    # Build a local report
    if xml:
        context.run("coverage xml", pty=pty)
    else:
        context.run("coverage html", pty=pty)
        webbrowser.open(COVERAGE_REPORT.as_uri())


ns.add_task(coverage)
