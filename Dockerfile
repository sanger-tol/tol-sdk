# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

FROM python:3.12

WORKDIR /app

# copy package files
COPY pyproject.toml ./

# create the stub directory
RUN mkdir -p src/tol && touch src/tol/__init__.py

# install package (editable, so that we don't have to reinstall after copying src/)
RUN pip install -e .[all]

# install the testing requirements
COPY requirements-test.txt .
COPY requirements requirements
RUN pip install -r requirements-test.txt

# copy in the source
COPY src src

WORKDIR /test

# copy tests
COPY test .
