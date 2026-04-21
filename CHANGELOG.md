<!--
SPDX-FileCopyrightText: 2026 Genome Research Ltd.

SPDX-License-Identifier: MIT
-->

# Changelog

## tol-sdk `2.1.0`
20-04-2026
- Added the `:aggregations` endpoint to replace the previous one by the same name,
  which is now `:aggregations_legacy`. It uses its own config, rather than echoing the request
  to Elastic as before.

## tol-sdk `2.0.10`
16-04-2026
- Added MultipleConverter to chain multiple converters in a pipeline step
- Added PipelineUtils to better reuse standard converter/validator instantiation
- Added a Config to Treeofsex converter
- Added changelog file to track tol-sdk version updates and changes
- Changed SetStatusAction class to handle user_id and error when missing params
