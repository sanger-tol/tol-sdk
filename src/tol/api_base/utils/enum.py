# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from enum import Enum


class IdSchemes(str, Enum):
    """
    An enum describing the possible types of
    identifier value protocol
    """

    AUTO_INCREMENT = 0  # need not be specified, sequentially generated
    EXTERNAL = 1  # e.g. NCBI Taxonomy ID for species
    USER_SPECIFIED_UUID = 2  # a unique value specified by the user
