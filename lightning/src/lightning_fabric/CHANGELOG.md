# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).


## [UnReleased] - 2023-MM-DD

### Added

- Added `Fabric.all_reduce` ([#16459](https://github.com/Lightning-AI/lightning/pull/16459))

- Added support for saving and loading DeepSpeed checkpoints through `Fabric.save/load()` ([#16452](https://github.com/Lightning-AI/lightning/pull/16452))


### Changed

- Checkpoint saving and loading redesign ([#16434](https://github.com/Lightning-AI/lightning/pull/16434))
  * Changed the method signatrue of `Fabric.save` and `Fabric.load`
  * Changed the method signature of `Strategy.save_checkpoint` and `Fabric.load_checkpoint`
  * `Fabric.save` accepts a state that can contain model and optimizer references
  * `Fabric.load` can now load state in-place onto models and optimizers
  * `Fabric.load` returns a dictionary of objects that weren't loaded into the state
  * `Strategy.save_checkpoint` and `Fabric.load_checkpoint` are now responsible for accessing the state of the model and optimizers

- `DataParallelStrategy.get_module_state_dict()` and `DDPStrategy.get_module_state_dict()` now correctly extracts the state dict without keys prefixed with 'module' ([#16487](https://github.com/Lightning-AI/lightning/pull/16487))

- "Native" suffix removal ([#16490](https://github.com/Lightning-AI/lightning/pull/16490))
 * `strategy="fsdp_full_shard_offload"` is now `strategy="fsdp_cpu_offload"`
 * `lightning_fabric.plugins.precision.native_amp` is now `lightning_fabric.plugins.precision.amp`

- Enabled all shorthand strategy names that can be supported in the CLI ([#16485](https://github.com/Lightning-AI/lightning/pull/16485))


### Deprecated

-


### Removed

-


### Fixed

- Fixed error handling for `accelerator="mps"` and `ddp` strategy pairing ([#16455](https://github.com/Lightning-AI/lightning/pull/16455))

- Fixed strict availability check for `torch_xla` requirement ([#16476](https://github.com/Lightning-AI/lightning/pull/16476))


## [1.9.0] - 2023-01-17

### Added

- Added `Fabric.launch()` to programmatically launch processes (e.g. in Jupyter notebook) ([#14992](https://github.com/Lightning-AI/lightning/pull/14992))
- Added the option to launch Fabric scripts from the CLI, without the need to wrap the code into the `run` method ([#14992](https://github.com/Lightning-AI/lightning/pull/14992))
- Added `Fabric.setup_module()` and `Fabric.setup_optimizers()` to support strategies that need to set up the model before an optimizer can be created ([#15185](https://github.com/Lightning-AI/lightning/pull/15185))
- Added support for Fully Sharded Data Parallel (FSDP) training in Lightning Lite ([#14967](https://github.com/Lightning-AI/lightning/pull/14967))
- Added `lightning_fabric.accelerators.find_usable_cuda_devices` utility function ([#16147](https://github.com/Lightning-AI/lightning/pull/16147))
- Added basic support for LightningModules ([#16048](https://github.com/Lightning-AI/lightning/pull/16048))
- Added support for managing callbacks via `Fabric(callbacks=...)` and emitting events through `Fabric.call()` ([#16074](https://github.com/Lightning-AI/lightning/pull/16074))
- Added Logger support ([#16121](https://github.com/Lightning-AI/lightning/pull/16121))
  * Added `Fabric(loggers=...)` to support different Logger frameworks in Fabric
  * Added `Fabric.log` for logging scalars using multiple loggers
  * Added `Fabric.log_dict` for logging a dictionary of multiple metrics at once
  * Added `Fabric.loggers` and `Fabric.logger` attributes to access the individual logger instances
  * Added support for calling `self.log` and `self.log_dict` in a LightningModule when using Fabric
  * Added access to `self.logger` and `self.loggers` in a LightningModule when using Fabric
- Added `lightning_fabric.loggers.TensorBoardLogger` ([#16121](https://github.com/Lightning-AI/lightning/pull/16121))
- Added `lightning_fabric.loggers.CSVLogger` ([#16346](https://github.com/Lightning-AI/lightning/pull/16346))
- Added support for a consistent `.zero_grad(set_to_none=...)` on the wrapped optimizer regardless of which strategy is used ([#16275](https://github.com/Lightning-AI/lightning/pull/16275))

### Changed

- Renamed the class `LightningLite` to `Fabric` ([#15932](https://github.com/Lightning-AI/lightning/pull/15932), [#15938](https://github.com/Lightning-AI/lightning/pull/15938))
- The `Fabric.run()` method is no longer abstract ([#14992](https://github.com/Lightning-AI/lightning/pull/14992))
- The `XLAStrategy` now inherits from `ParallelStrategy` instead of `DDPSpawnStrategy` ([#15838](https://github.com/Lightning-AI/lightning/pull/15838))
- Merged the implementation of `DDPSpawnStrategy` into `DDPStrategy` and removed `DDPSpawnStrategy` ([#14952](https://github.com/Lightning-AI/lightning/pull/14952))
- The dataloader wrapper returned from `.setup_dataloaders()` now calls `.set_epoch()` on the distributed sampler if one is used ([#16101](https://github.com/Lightning-AI/lightning/pull/16101))
- Renamed `Strategy.reduce` to `Strategy.all_reduce` in all strategies ([#16370](https://github.com/Lightning-AI/lightning/pull/16370))
- When using multiple devices, the strategy now defaults to "ddp" instead of "ddp_spawn" when none is set ([#16388](https://github.com/Lightning-AI/lightning/pull/16388))

### Removed

- Removed support for FairScale's sharded training (`strategy='ddp_sharded'|'ddp_sharded_spawn'`). Use Fully-Sharded Data Parallel instead (`strategy='fsdp'`) ([#16329](https://github.com/Lightning-AI/lightning/pull/16329))

### Fixed

- Restored sampling parity between PyTorch and Fabric dataloaders when using the `DistributedSampler` ([#16101](https://github.com/Lightning-AI/lightning/pull/16101))
- Fixes an issue where the error message wouldn't tell the user the real value that was passed through the CLI ([#16334](https://github.com/Lightning-AI/lightning/pull/16334))


## [1.8.6] - 2022-12-21

- minor cleaning


## [1.8.5] - 2022-12-15

- minor cleaning


## [1.8.4] - 2022-12-08

### Fixed

- Fixed `shuffle=False` having no effect when using DDP/DistributedSampler ([#15931](https://github.com/Lightning-AI/lightning/pull/15931))


## [1.8.3] - 2022-11-22

### Changed

- Temporarily removed support for Hydra multi-run ([#15737](https://github.com/Lightning-AI/lightning/pull/15737))


## [1.8.2] - 2022-11-17

### Fixed

- Fixed the automatic fallback from `LightningLite(strategy="ddp_spawn", ...)` to `LightningLite(strategy="ddp", ...)` when on an LSF cluster ([#15103](https://github.com/Lightning-AI/lightning/pull/15103))


## [1.8.1] - 2022-11-10

### Fixed

- Fix an issue with the SLURM `srun` detection causing permission errors ([#15485](https://github.com/Lightning-AI/lightning/pull/15485))
- Fixed the import of `lightning_lite` causing a warning 'Redirects are currently not supported in Windows or MacOs' ([#15610](https://github.com/Lightning-AI/lightning/pull/15610))
