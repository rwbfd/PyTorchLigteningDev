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
from unittest import mock
from unittest.mock import Mock, PropertyMock

import pytest
import torch
from torch import nn

from lightning_fabric.strategies import SingleDeviceStrategy


@pytest.mark.parametrize("is_rank_zero", [True, False])
def test_save_checkpoint_rank_zero_only(is_rank_zero, tmp_path):
    """Test that the checkpoint only gets saved on global rank 0 in the base implementation in Strategy."""
    strategy = SingleDeviceStrategy()  # surrogate class to test implementation in base class
    save_checkpoint_mock = Mock()
    strategy.checkpoint_io.save_checkpoint = save_checkpoint_mock
    with mock.patch(
        "lightning_fabric.strategies.single_device.SingleDeviceStrategy.is_global_zero",
        new_callable=PropertyMock(return_value=is_rank_zero),
    ):
        strategy.save_checkpoint(tmp_path, {"anything": 1})
    assert save_checkpoint_mock.call_count == int(is_rank_zero)


def test_save_checkpoint_empty_state(tmp_path):
    """Test that one can save an empty state with the base implementation in Strategy."""
    strategy = SingleDeviceStrategy()  # surrogate class to test implementation in base class
    save_checkpoint_mock = Mock()
    strategy.checkpoint_io.save_checkpoint = save_checkpoint_mock

    state = {}
    strategy.save_checkpoint(tmp_path, state)
    save_checkpoint_mock.assert_called_with(checkpoint=state, path=tmp_path, storage_options=None)


def test_save_checkpoint_convert_stateful_objects(tmp_path):
    """Test that when modules and optimizers are at the top-level in the state, their `state_dict()` gets used."""
    strategy = SingleDeviceStrategy()  # surrogate class to test implementation in base class
    save_checkpoint_mock = Mock()
    strategy.checkpoint_io.save_checkpoint = save_checkpoint_mock

    model = nn.Linear(3, 3)
    optimizer = torch.optim.Adam(model.parameters())

    anything = {"cocofruit": 1}
    state = {"model": model, "optimizer": optimizer, "anything": anything}
    expected = {"model": model.state_dict(), "optimizer": optimizer.state_dict(), "anything": anything}
    strategy.save_checkpoint(tmp_path, state)
    assert save_checkpoint_mock.call_args[1]["checkpoint"].keys() == expected.keys()
    saved_model_state = save_checkpoint_mock.call_args[1]["checkpoint"]["model"]
    assert all(torch.equal(p0, p1) for p0, p1 in zip(saved_model_state.values(), expected["model"].values()))
    assert save_checkpoint_mock.call_args[1]["checkpoint"]["optimizer"] == expected["optimizer"]
    assert save_checkpoint_mock.call_args[1]["checkpoint"]["anything"] == expected["anything"]


def test_load_checkpoint_out_of_place(tmp_path):
    """Test that one can load the full checkpoint into memory just like `torch.load()`."""
    strategy = SingleDeviceStrategy()  # surrogate class to test implementation in base class
    load_checkpoint_mock = Mock()
    strategy.checkpoint_io.load_checkpoint = load_checkpoint_mock

    checkpoint = strategy.load_checkpoint(tmp_path, state=None)
    assert checkpoint == load_checkpoint_mock()

    checkpoint = strategy.load_checkpoint(tmp_path, state={})
    assert checkpoint == load_checkpoint_mock()


def test_load_checkpoint_in_place(tmp_path):
    """Test that the object's state gets reloaded in-place."""
    strategy = SingleDeviceStrategy()  # surrogate class to test implementation in base class

    # objects with initial state
    saved_model = nn.Linear(2, 2)
    saved_optimizer = torch.optim.Adam(saved_model.parameters(), lr=0.1)
    saved_state = {"model": saved_model, "optimizer": saved_optimizer, "int": 1, "dict": {"cocofruit": 2}}
    strategy.save_checkpoint(tmp_path / "checkpoint", state=saved_state)

    # same objects with different state
    model = nn.Linear(2, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.3)
    state = {"model": model, "optimizer": optimizer, "int": 10, "dict": {"cocofruit": 20}}
    assert not torch.equal(model.weight, saved_model.weight)
    assert optimizer.state_dict() != saved_optimizer.state_dict()

    remainder = strategy.load_checkpoint(tmp_path / "checkpoint", state)
    assert torch.equal(model.weight, saved_model.weight)
    assert optimizer.state_dict() == saved_optimizer.state_dict()
    assert state["int"] == saved_state["int"]
    assert state["dict"] == saved_state["dict"]
    assert not remainder

    # partial load - only model, no optimizer
    model = nn.Linear(2, 2)
    state = {"model": model}
    remainder = strategy.load_checkpoint(tmp_path / "checkpoint", state)
    assert torch.equal(model.weight, saved_model.weight)
    assert list(remainder.keys()) == ["optimizer", "int", "dict"]


def test_load_checkpoint_strict_loading(tmp_path):
    """Test that an error is raised if a key is requested to be restored but does not exist in the checkpoint."""
    strategy = SingleDeviceStrategy()  # surrogate class to test implementation in base class
    saved_state = {"a": 1, "b": 2}
    requested_state = {"a": 1, "b": 2, "c": 3}  # key `c` does not exist in the saved state
    load_checkpoint_mock = Mock(return_value=saved_state)
    strategy.checkpoint_io.load_checkpoint = load_checkpoint_mock
    with pytest.raises(KeyError, match="contains a key 'c' that does not exist"):
        strategy.load_checkpoint(tmp_path, requested_state)
