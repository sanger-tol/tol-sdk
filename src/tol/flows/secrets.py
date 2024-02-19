# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from prefect.blocks.system import Secret


def convert_env_key(env_key: str) -> str:
    return env_key.lower().replace('_', '-')


def get(key: str) -> str:
    secret_key = convert_env_key(key)
    secret: Secret = Secret.load(secret_key)

    return secret.get()
