import os
import shutil
import signal
import threading
from datetime import datetime
from pathlib import Path
from threading import Thread

import psutil
import py
import pytest

from lightning_app.storage.path import _storage_root_dir
from lightning_app.utilities.app_helpers import _collect_child_process_pids
from lightning_app.utilities.component import _set_context
from lightning_app.utilities.packaging import cloud_compute
from lightning_app.utilities.packaging.app_config import _APP_CONFIG_FILENAME
from lightning_app.utilities.state import AppState

os.environ["LIGHTNING_DISPATCHED"] = "1"

original_method = Thread._wait_for_tstate_lock


def fn(self, *args, timeout=None, **kwargs):
    original_method(self, *args, timeout=1, **kwargs)


Thread._wait_for_tstate_lock = fn


def pytest_sessionfinish(session, exitstatus):
    """Pytest hook that get called after whole test run finished, right before returning the exit status to the
    system."""
    # kill all the processes and threads created by parent
    # TODO this isn't great. We should have each tests doing it's own cleanup
    current_process = psutil.Process()
    for child in current_process.children(recursive=True):
        try:
            params = child.as_dict() or {}
            cmd_lines = params.get("cmdline", [])
            # we shouldn't kill the resource tracker from multiprocessing. If we do,
            # `atexit` will throw as it uses resource tracker to try to clean up
            if cmd_lines and "resource_tracker" in cmd_lines[-1]:
                continue
            child.kill()
        except psutil.NoSuchProcess:
            pass

    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is not main_thread:
            t.join(0)

    for child_pid in _collect_child_process_pids(os.getpid()):
        os.kill(child_pid, signal.SIGTERM)


@pytest.fixture(scope="function", autouse=True)
def cleanup():
    from lightning_app.utilities.app_helpers import _LightningAppRef

    yield
    _LightningAppRef._app_instance = None
    shutil.rmtree("./storage", ignore_errors=True)
    shutil.rmtree(_storage_root_dir(), ignore_errors=True)
    shutil.rmtree("./.shared", ignore_errors=True)
    if os.path.isfile(_APP_CONFIG_FILENAME):
        os.remove(_APP_CONFIG_FILENAME)
    _set_context(None)


@pytest.fixture(scope="function", autouse=True)
def clear_app_state_state_variables():
    """Resets global variables in order to prevent interference between tests."""
    yield
    import lightning_app.utilities.state

    lightning_app.utilities.state._STATE = None
    lightning_app.utilities.state._LAST_STATE = None
    AppState._MY_AFFILIATION = ()
    if hasattr(cloud_compute, "_CLOUD_COMPUTE_STORE"):
        cloud_compute._CLOUD_COMPUTE_STORE.clear()


@pytest.fixture
def another_tmpdir(tmp_path: Path) -> py.path.local:
    random_dir = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    tmp_path = os.path.join(tmp_path, random_dir)
    return py.path.local(tmp_path)


@pytest.fixture
def caplog(caplog):
    """Workaround for https://github.com/pytest-dev/pytest/issues/3697.

    Setting ``filterwarnings`` with pytest breaks ``caplog`` when ``not logger.propagate``.
    """
    import logging

    root_logger = logging.getLogger()
    root_propagate = root_logger.propagate
    root_logger.propagate = True

    propagation_dict = {
        name: logging.getLogger(name).propagate
        for name in logging.root.manager.loggerDict
        if name.startswith("lightning_app")
    }
    for name in propagation_dict.keys():
        logging.getLogger(name).propagate = True

    yield caplog

    root_logger.propagate = root_propagate
    for name, propagate in propagation_dict.items():
        logging.getLogger(name).propagate = propagate
