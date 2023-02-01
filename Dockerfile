# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

FROM python:3.8

# copy package files
COPY setup.cfg pyproject.toml /app/

COPY ./src /app/src

WORKDIR /app

# install package
RUN pip install .[all]

# install the testing requirements
COPY requirements-test.txt /app/

RUN pip install -r /app/requirements-test.txt

# copy tests
COPY ./test /test

WORKDIR /test
