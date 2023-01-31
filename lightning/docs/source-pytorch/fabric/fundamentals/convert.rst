:orphan:

##############################
Convert PyTorch code to Fabric
##############################

Here are five easy steps to let :class:`~lightning_fabric.fabric.Fabric` scale your PyTorch models.

**Step 1:** Create the :class:`~lightning_fabric.fabric.Fabric` object at the beginning of your training code.

.. code-block:: python

    from lightning.fabric import Fabric

    fabric = Fabric()

**Step 2:** Call :meth:`~lightning_fabric.fabric.Fabric.setup` on each model and optimizer pair and :meth:`~lightning_fabric.fabric.Fabric.setup_dataloaders` on all your data loaders.

.. code-block:: python

    model, optimizer = fabric.setup(model, optimizer)
    dataloader = fabric.setup_dataloaders(dataloader)

**Step 3:** Remove all ``.to`` and ``.cuda`` calls since :class:`~lightning_fabric.fabric.Fabric` will take care of it.

.. code-block:: diff

  - model.to(device)
  - batch.to(device)

**Step 4:** Replace ``loss.backward()`` by ``fabric.backward(loss)``.

.. code-block:: diff

  - loss.backward()
  + fabric.backward(loss)

**Step 5:** Run the script from the terminal with

.. code-block:: bash

    lightning run model path/to/train.py

or use the :meth:`~lightning_fabric.fabric.Fabric.launch` method in a notebook.
Learn more about :doc:`launching distributed training <launch>`.

|

All steps combined, this is how your code will change:

.. code-block:: diff

      import torch
      import torch.nn as nn
      from torch.utils.data import DataLoader, Dataset

    + from lightning.fabric import Fabric

      class PyTorchModel(nn.Module):
          ...

      class PyTorchDataset(Dataset):
          ...

    + fabric = Fabric(accelerator="cuda", devices=8, strategy="ddp")
    + fabric.launch()

    - device = "cuda" if torch.cuda.is_available() else "cpu
      model = PyTorchModel(...)
      optimizer = torch.optim.SGD(model.parameters())
    + model, optimizer = fabric.setup(model, optimizer)
      dataloader = DataLoader(PyTorchDataset(...), ...)
    + dataloader = fabric.setup_dataloaders(dataloader)
      model.train()

      for epoch in range(num_epochs):
          for batch in dataloader:
              input, target = batch
    -         input, target = input.to(device), target.to(device)
              optimizer.zero_grad()
              output = model(input)
              loss = loss_fn(output, target)
    -         loss.backward()
    +         fabric.backward(loss)
              optimizer.step()
              lr_scheduler.step()


That's it! You can now train on any device at any scale with a switch of a flag.
Check out our before-and-after example for `image classification <https://github.com/Lightning-AI/lightning/blob/master/examples/fabric/image_classifier/README.md>`_ and many more :ref:`examples <Fabric Examples>` that use Fabric.

**********
Next steps
**********

.. raw:: html

    <div class="display-card-container">
        <div class="row">

.. displayitem::
    :header: Examples
    :description: See examples across computer vision, NLP, RL, etc.
    :col_css: col-md-4
    :button_link: ../fabric.html#examples
    :height: 150
    :tag: basic

.. displayitem::
    :header: Accelerators
    :description: Take advantage of your hardware with a switch of a flag
    :button_link: accelerators.html
    :col_css: col-md-4
    :height: 150
    :tag: intermediate

.. displayitem::
    :header: Build your own Trainer
    :description: Learn how to build a trainer tailored for you
    :col_css: col-md-4
    :button_link: ../fabric.html#build-your-own-trainer
    :height: 150
    :tag: intermediate

.. raw:: html

        </div>
    </div>
