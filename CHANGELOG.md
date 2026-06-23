<!--
SPDX-FileCopyrightText: 2026 Genome Research Ltd.

SPDX-License-Identifier: MIT
-->

# Changelog

## tol-sdk `2.3.2`
23-06-2026
- Avoid caching data in JsonDataSource and children

## tol-sdk `2.3.1`
22-06-2026
- Fix bug in GritIssueToElasticCurationConverter

## tol-sdk `2.3.0`
22-06-2026
- Added POST `add-entity` endpoint to `board_bp`
- Added POST `create-board` endpoint to `board_bp`
- Added DELETE `delete-entity` endpoint to `board_bp`
- Added PATCH `reorder` endpoint to `board_bp`
- Added GET `get-entity` endpoint to `board_bp`
- Added POST `copy` endpoint to `board_bp`
- Added more security to `board_bp` endpoints
- Added `upsert_batch` to allow for sessioned re-ordering of board entities.
- Added ability for `warden` role to bypass user needing to be owner requirements to edit boards & board entities.
- GritIssueToElasticCurationConverter now also extracts the following fields:
    - grit_treeval_jbrowse
    - grit_treeval_jb_server
    - grit_treeval_jb_scaffold
    - grit_treeval_start
    - grit_treeval_btk_pr
    - grit_treeval_btk_hp
    - grit_treeval_higlass
    - grit_treeval_hic_plot
    - grit_treeval_kmer_plot
    - grit_treeval_taxon_id
    - grit_treeval_hap1_analysis
    - grit_treeval_hap2_analysis
    - grit_treeval_merged_analysis
    - grit_contamination_total_removed
    - grit_contamination_total_removed_percent
    - grit_contamination_count_removed
    - grit_contamination_count_removed_percent
    - grit_contamination_largest_removed
    - grit_contamination_is_abnormal
- GritIssueToElasticCurationConverter now no longer exposes the following fields:
    - grit_treeval_data
    - grit_treeval
    - grit_contamination

## tol-sdk `2.2.2`
09-06-2026
- Bug fixes for the SGP STS -> Benchling flow converter

## tol-sdk `2.2.1`
09-06-2026
- Added ElasticSampleToElasticExtractionContainerUpdateConverter

## tol-sdk `2.2.0`
04-06-2026
- Reorganised action folder to avoid import dependencies
- Use tolid field rather than sample_id in GRIT issue converter

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
