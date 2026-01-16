# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import glob

from flask import Blueprint


def system_blueprint(
    url_prefix: str = '/system',
    env_map: dict[str, str] = {'environment': 'ENVIRONMENT'},
    env_vars: dict[str, str] = {}
) -> Blueprint:
    """
    A flask Blueprint that groups system endpoints.

    By default includes:
    - /healthz      - used for health probes in kubernetes
    - /environment  - indicates the deployment environment
    - /package-versions  - indicates the deployment package versions

    Parameters:
    - url_prefix    - the prefix under which to serve this blueprint's
                      endpoints
    - env_map       - maps keys in the /environment output to keys in
                      the env_vars dict
    - env_vars      - a dict containing environment variables (defaults
                      to os.environ)
    """

    system_blueprint = Blueprint('system', __name__, url_prefix=url_prefix)

    @system_blueprint.route('/healthz')
    def healthz():
        return {
            'healthy': True
        }, 200

    @system_blueprint.route('/environment')
    def environment():
        return {
            k: env_vars.get(v) for k, v in env_map.items()
        }, 200

    @system_blueprint.route('/package-versions')
    def package_versions():
        glob_paths = glob.glob('./**/requirements.txt', recursive=True)
        with open(glob_paths[0], 'r') as f:
            requirements = f.readlines()
            for requirement in requirements:
                if 'tol-sdk' in requirement:
                    tol_sdk_version = requirement.split('==')[1].strip()
                    break
            f.close()

        result = {'tol_sdk': tol_sdk_version,}

        return result, 200

    return system_blueprint
