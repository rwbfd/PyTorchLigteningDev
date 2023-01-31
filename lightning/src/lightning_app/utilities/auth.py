# Copyright The Lightning team.
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

from typing import Dict


def _credential_string_to_basic_auth_params(credential_string: str) -> Dict[str, str]:
    """Returns the name/ID pair for each given Secret name.

    Raises a `ValueError` if any of the given Secret names do not exist.
    """
    if credential_string.count(":") != 1:
        raise ValueError(
            "Credential string must follow the format username:password; "
            + f"the provided one ('{credential_string}') does not."
        )

    username, password = credential_string.split(":")

    if not username:
        raise ValueError("Username cannot be empty.")

    if not password:
        raise ValueError("Password cannot be empty.")

    return {"username": username, "password": password}
