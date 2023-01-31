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
"""Test that the warnings actually appear and they have the correct `stacklevel`

Needs to be run outside of `pytest` as it captures all the warnings.
"""
from contextlib import redirect_stderr
from io import StringIO

if __name__ == "__main__":
    # check that logging is properly configured
    import logging

    from pytorch_lightning import _DETAIL

    root_logger = logging.getLogger()
    lightning_logger = logging.getLogger("pytorch_lightning")
    # should have a `StreamHandler`
    assert lightning_logger.hasHandlers() and len(lightning_logger.handlers) == 1
    # set our own stream for testing
    handler = lightning_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    stderr = StringIO()
    # necessary with `propagate = False`
    lightning_logger.handlers[0].stream = stderr

    # necessary with `propagate = True`
    with redirect_stderr(stderr):
        # Lightning should not configure the root `logging` logger by default
        logging.info("test1")
        root_logger.info("test1")
        # but our logger instance
        lightning_logger.info("test2")
        # level is set to INFO
        lightning_logger.debug("test3")

    output = stderr.getvalue()
    assert output == "test2\n", repr(output)

    stderr = StringIO()
    lightning_logger.handlers[0].stream = stderr
    with redirect_stderr(stderr):
        # Lightning should not output DETAIL level logging by default
        lightning_logger.detail("test1")
        lightning_logger.setLevel(_DETAIL)
        lightning_logger.detail("test2")
        # logger should not output anything for DEBUG statements if set to DETAIL
        lightning_logger.debug("test3")
    output = stderr.getvalue()
    assert output == "test2\n", repr(output)
