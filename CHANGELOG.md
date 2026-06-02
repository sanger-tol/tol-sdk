<!--
SPDX-FileCopyrightText: 2026 Genome Research Ltd.

SPDX-License-Identifier: MIT
-->

# Changelog

## tol-sdk `2.1.12`
28-05-2026
- Added all TUM functionality (used to be in a standalone flow)

## tol-sdk `2.1.11`
26-05-2026
- Updated SGP STS -> Benchling flow converter to handle the new SGP data structure

## tol-sdk `2.1.10`
18-05-2026
- Fixed pipeline_id being None during revalidation

## tol-sdk `2.1.9`
13-05-2026
- Deal with stats not being present in data loaders

## tol-sdk `2.1.8`
13-05-2026
- Add "recent" stat

## tol-sdk `2.1.7`
07-05-2026
- Allow DataLoaders to use requested_fields

## tol-sdk `2.1.6`
06-05-2026
- Add study as top level object
- Add location path and tube position to containers from Benchling
- JSON to Elastic converter for Genome Notes

## tol-sdk `2.1.5`
29-04-2026
- Exclude non-ToL curations in the converter
- Fix for SqlDatasource filtering two or more levels deep

## tol-sdk `2.1.4`
29-04-2026
- Allow Elastic get_stats to work with related attributes

## tol-sdk `2.1.3`
27-04-2026
- Add cardinality metadata to SqlDataSource
- Add mock containers for LRES DNA extractions

## tol-sdk `2.1.2`
21-04-2026
- Added Config dataclass to all converters

## tol-sdk `2.1.1`
21-04-2026
- Fixed actions by passing user_id as a default parameter to local actions,
  this is required for status actions and audits of which user ran a local
  action

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
