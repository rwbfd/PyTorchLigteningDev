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

from copy import deepcopy

import torch

from lightning_fabric import Fabric
from pytorch_lightning.demos.boring_classes import BoringModel, ManualOptimBoringModel


def test_fabric_boring_lightning_module_automatic():
    """Test that basic LightningModules written for 'automatic optimization' work with Fabric."""

    fabric = Fabric(accelerator="cpu", devices=1)

    module = BoringModel()
    parameters_before = deepcopy(list(module.parameters()))

    optimizers, _ = module.configure_optimizers()
    dataloader = module.train_dataloader()

    model, optimizer = fabric.setup(module, optimizers[0])
    dataloader = fabric.setup_dataloaders(dataloader)

    batch = next(iter(dataloader))
    output = model.training_step(batch, 0)
    fabric.backward(output["loss"])
    optimizer.step()

    assert all(not torch.equal(before, after) for before, after in zip(parameters_before, model.parameters()))


def test_fabric_boring_lightning_module_manual():
    """Test that basic LightningModules written for 'manual optimization' work with Fabric."""

    fabric = Fabric(accelerator="cpu", devices=1)

    module = ManualOptimBoringModel()
    parameters_before = deepcopy(list(module.parameters()))

    optimizers, _ = module.configure_optimizers()
    dataloader = module.train_dataloader()

    model, optimizer = fabric.setup(module, optimizers[0])
    dataloader = fabric.setup_dataloaders(dataloader)

    batch = next(iter(dataloader))
    model.training_step(batch, 0)  # .backward() and optimizer.step() happen inside training_step()

    assert all(not torch.equal(before, after) for before, after in zip(parameters_before, model.parameters()))
