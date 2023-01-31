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
from unittest.mock import Mock

import pytest
import torch

from lightning_fabric.plugins.precision.amp import MixedPrecision


def test_amp_precision_default_scaler():
    precision = MixedPrecision(precision=16, device=Mock())
    assert isinstance(precision.scaler, torch.cuda.amp.GradScaler)


def test_amp_precision_scaler_with_bf16():
    with pytest.raises(ValueError, match="`precision='bf16'` does not use a scaler"):
        MixedPrecision(precision="bf16", device=Mock(), scaler=Mock())

    precision = MixedPrecision(precision="bf16", device=Mock())
    assert precision.scaler is None


def test_amp_precision_forward_context():
    """Test to ensure that the context manager correctly is set to bfloat16 on CPU and CUDA."""
    precision = MixedPrecision(precision=16, device="cuda")
    assert precision.device == "cuda"
    assert isinstance(precision.scaler, torch.cuda.amp.GradScaler)
    assert torch.get_default_dtype() == torch.float32
    with precision.forward_context():
        # check with str due to a bug upstream: https://github.com/pytorch/pytorch/issues/65786
        assert str(torch.get_autocast_gpu_dtype()) in ("torch.float16", "torch.half")

    precision = MixedPrecision(precision="bf16", device="cpu")
    assert precision.device == "cpu"
    assert precision.scaler is None
    with precision.forward_context():
        # check with str due to a bug upstream: https://github.com/pytorch/pytorch/issues/65786
        assert str(torch.get_autocast_cpu_dtype()) == str(torch.bfloat16)

    context_manager = precision._autocast_context_manager()
    assert isinstance(context_manager, torch.autocast)
    # check with str due to a bug upstream: https://github.com/pytorch/pytorch/issues/65786
    assert str(context_manager.fast_dtype) == str(torch.bfloat16)


def test_amp_precision_backward():
    precision = MixedPrecision(precision="mixed", device="cuda")
    precision.scaler = Mock()
    precision.scaler.scale = Mock(side_effect=(lambda x: x))
    tensor = Mock()
    model = Mock()
    precision.backward(tensor, model, "positional-arg", keyword="arg")
    precision.scaler.scale.assert_called_once_with(tensor)
    tensor.backward.assert_called_once_with("positional-arg", keyword="arg")


def test_amp_precision_optimizer_step_with_scaler():
    precision = MixedPrecision(precision="mixed", device="cuda")
    precision.scaler = Mock()
    optimizer = Mock()

    precision.optimizer_step(optimizer, keyword="arg")
    precision.scaler.step.assert_called_once_with(optimizer, keyword="arg")
    precision.scaler.update.assert_called_once()


def test_amp_precision_optimizer_step_without_scaler():
    precision = MixedPrecision(precision="bf16", device="cuda")
    assert precision.scaler is None
    optimizer = Mock()

    precision.optimizer_step(optimizer, keyword="arg")
    optimizer.step.assert_called_once_with(keyword="arg")
