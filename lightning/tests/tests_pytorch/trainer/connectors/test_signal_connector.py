# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import concurrent.futures
import os
import signal
from unittest import mock

import pytest

from lightning_fabric.plugins.environments import SLURMEnvironment
from lightning_fabric.utilities.imports import _IS_WINDOWS
from pytorch_lightning import Trainer
from pytorch_lightning.demos.boring_classes import BoringModel
from pytorch_lightning.trainer.connectors.signal_connector import SignalConnector
from pytorch_lightning.utilities.exceptions import SIGTERMException
from tests_pytorch.helpers.runif import RunIf


@RunIf(skip_windows=True)
def test_signal_handlers_restored_in_teardown():
    """Test that the SignalConnector restores the previously configured handler on teardown."""
    assert signal.getsignal(signal.SIGTERM) is signal.SIG_DFL

    trainer = Trainer(plugins=SLURMEnvironment())
    connector = SignalConnector(trainer)
    connector.register_signal_handlers()

    assert signal.getsignal(signal.SIGTERM) is not signal.SIG_DFL
    connector.teardown()
    assert signal.getsignal(signal.SIGTERM) is signal.SIG_DFL


@RunIf(skip_windows=True)
def test_sigterm_handler_can_be_added(tmpdir):
    handler_ran = False

    def handler(*_):
        nonlocal handler_ran
        handler_ran = True

    signal.signal(signal.SIGTERM, handler)

    class TestModel(BoringModel):
        def training_step(self, batch, batch_idx):
            os.kill(os.getpid(), signal.SIGTERM)

    model = TestModel()
    trainer = Trainer(default_root_dir=tmpdir, max_epochs=1, limit_train_batches=2, limit_val_batches=0)

    assert not trainer.received_sigterm
    assert not handler_ran
    with pytest.raises(SIGTERMException):
        trainer.fit(model)
    assert trainer.received_sigterm
    assert handler_ran

    # reset the signal to system defaults
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


@RunIf(skip_windows=True)
@pytest.mark.parametrize("auto_requeue", (True, False))
@pytest.mark.parametrize("requeue_signal", [signal.SIGUSR1, signal.SIGUSR2, signal.SIGHUP] if not _IS_WINDOWS else [])
def test_auto_requeue_custom_signal_flag(auto_requeue, requeue_signal):
    trainer = Trainer(plugins=[SLURMEnvironment(auto_requeue=auto_requeue, requeue_signal=requeue_signal)])
    connector = SignalConnector(trainer)
    connector.register_signal_handlers()

    if auto_requeue:
        sigterm_handlers = signal.getsignal(signal.SIGTERM).signal_handlers
        assert len(sigterm_handlers) == 2
        assert sigterm_handlers[1].__qualname__ == "SignalConnector.sigterm_handler_fn"

        sigusr_handlers = signal.getsignal(requeue_signal).signal_handlers
        assert len(sigusr_handlers) == 1
        assert sigusr_handlers[0].__qualname__ == "SignalConnector.slurm_sigusr_handler_fn"
    else:
        sigterm_handlers = signal.getsignal(signal.SIGTERM).signal_handlers
        assert len(sigterm_handlers) == 1
        assert sigterm_handlers[0].__qualname__ == "SignalConnector._sigterm_notifier_fn"

        assert signal.getsignal(requeue_signal) is signal.SIG_DFL

    connector.teardown()


@RunIf(skip_windows=True)
@mock.patch("pytorch_lightning.trainer.connectors.signal_connector.call")
@mock.patch("pytorch_lightning.trainer.Trainer.save_checkpoint", mock.MagicMock())
@mock.patch.dict(os.environ, {"SLURM_JOB_ID": "12345"})
def test_auto_requeue_job(call_mock):
    call_mock.return_value = 0
    trainer = Trainer(plugins=[SLURMEnvironment()])
    connector = SignalConnector(trainer)
    connector.slurm_sigusr_handler_fn(None, None)
    call_mock.assert_called_once_with(["scontrol", "requeue", "12345"])
    connector.teardown()


@RunIf(skip_windows=True)
@mock.patch("pytorch_lightning.trainer.connectors.signal_connector.call")
@mock.patch("pytorch_lightning.trainer.Trainer.save_checkpoint", mock.MagicMock())
@mock.patch.dict(os.environ, {"SLURM_JOB_ID": "12346", "SLURM_ARRAY_JOB_ID": "12345", "SLURM_ARRAY_TASK_ID": "2"})
def test_auto_requeue_array_job(call_mock):
    call_mock.return_value = 0
    trainer = Trainer(plugins=[SLURMEnvironment()])
    connector = SignalConnector(trainer)
    connector.slurm_sigusr_handler_fn(None, None)
    call_mock.assert_called_once_with(["scontrol", "requeue", "12345_2"])
    connector.teardown()


def _registering_signals():
    trainer = Trainer()
    trainer._signal_connector.register_signal_handlers()


@RunIf(skip_windows=True)
def test_signal_connector_in_thread():
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for future in concurrent.futures.as_completed([executor.submit(_registering_signals)]):
            assert future.exception() is None


def signal_handler():
    pass


class SignalHandlers:
    def signal_handler(self):
        pass


@pytest.mark.parametrize(
    ["handler", "expected_return"],
    [
        (None, False),
        (signal.Handlers.SIG_IGN, True),
        (signal.Handlers.SIG_DFL, False),
        (signal_handler, True),
        (SignalHandlers().signal_handler, True),
    ],
)
def test_has_already_handler(handler, expected_return):
    """Test that the SignalConnector detects whether a signal handler is already attached."""
    with mock.patch("pytorch_lightning.trainer.connectors.signal_connector.signal.getsignal", return_value=handler):
        assert SignalConnector._has_already_handler(signal.SIGTERM) is expected_return
