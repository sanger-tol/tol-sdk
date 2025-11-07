# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_s3_to_https(s3_path):
    if s3_path.startswith('s3://'):
        no_prefix = s3_path[len('s3://'):]
        parts = no_prefix.split('/', 1)
        if len(parts) == 2:
            bucket, path = parts
            return f'https://{bucket}.cog.sanger.ac.uk/{path}'
        else:
            # Only bucket, no path
            return f'https://{parts[0]}.cog.sanger.ac.uk/'
    return s3_path
