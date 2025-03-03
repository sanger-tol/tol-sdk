/* 
## SQL Query: Tissues exported from STS production database into Benchling Warehouse (BWH)

This query retrieves all the metadata associated to samples imported from STS that is relevant for the ToL Core Lab processes. 

Besides, the table contains the eln_tissue_id and eln_file_registry_id which uniquely idenfied each tissue entity in Benchling Warehouse (BWH). 
The eln_tissue_id should be used as the foreign key to the tissue child entitities (i.e. tissue_prep)

Definitions of Metadata fields for STS can be read in dept here: https://github.com/darwintreeoflife/metadata

In Benchling warehouse the tissue schema gathers all these fields. Always use the .*$raw version of any schema in Benchling. 
These .*$raw tables contain all the data included the entities and fields that have been archived.
For more information: https://help.benchling.com/hc/en-us/articles/9684262336397-What-is-the-difference-between-tables-that-are-suffixed-with-raw-vs-not-

The queries must filter the data by the Benchling projects that are relevant to the ToL Core Lab: 'Core Lab Entities', 'R&D', and 'Routine Throughput'

Columns in output table: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) eln_file_registry_id: [character] id in Benchling Registry. Origin: BWH
5) eln_tissue_name: [character] Entity name. Origin: BWH
6) sts_id: [character] Origin: Foreign key to STS
7) programme_id: [character] ToLID. Origin: STS
8) tissue_fluidx_id: [character] Origin: STS. Original name: tubewell_id. 
9) scientific_name: [character] Origin: STS
10) taxon_group_phyla: [character] Origin: STS
11) taxon_id: [character] Origin: STS
12) specimen_id: [character] Origin: STS
13) organism_part: [character] Origin: STS
14) lifestage: [character] Origin: STS
15) preservation_approach: [character] Origin: STS
16) sex: [character] Origin: STS
17) size_of_tissue_in_tube: [character] Origin: STS
18) genome_size: [character] Origin: STS
19) post_run_genome_size: [double precision] Origin: STS
20) current_coverage: [double precision] Origin: STS
21) biosample_id: [character] Origin: STS
22) biospecimen_id: [character] Origin: STS
23) sample_set_id: [character] Origin: STS
24) project: [character] Origin: STS
25) date_sample_received_at_sanger: [date] Origin: STS
26) date_assigned_to_tol_lab: [date] Origin: STS
27) assigned_by: [character] Origin: STS
28) rd_sample: [character] Origin: STS
29) family_representative: [character] Origin: STS
30) priority: [integer] Origin: STS
31) location: [character] Origin: STS. Physical location of the sample.
32) tray: [character] Origin: STS. Physical location of the sample.
33) rack_id: [character] Origin: STS. Physical location of the sample.
34) tube_position: [character] Origin: STS. Physical location of the sample.
35) remaining_weight: [double precision] Origin: BWH. Data taken during laboratory processes. 
*/

SELECT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	t.file_registry_id$ AS eln_file_registry_id,
	t.sts_id,
	t.name$ AS eln_tissue_name,
	t.programme_id,
	t.tubewell_id AS tissue_fluidx_id,
	t.scientific_name,
	t.taxon_group_phyla,
	t.taxon_id,
	t.specimen_id,
	t.organism_part,
	t.lifestage, 
	t.preservation_approach, 
	t.sex,
	t.size_of_tissue_in_tube,
	t.genome_size,
	t.post_run_genome_size,
	t.current_coverage,
	t.biosample_id,
	t.biospecimen_id,
	t.sample_set_id, 
	t.project,
	t.date_sample_received_at_sanger,
	t.date_assigned_to_lab,
	t.assigned_by,
	t.rd_sample,
	t.family_representative,
	t.priority,
	t.location,
	t.tray,
	t.rack_id,
	t.tube_position,
	t.remaining_weight
FROM tissue$raw AS t
LEFT JOIN project$raw AS proj
	ON t.project_id$ = proj.id
LEFT JOIN folder$raw AS f
	ON t.folder_id$ = f.id
WHERE proj.name IN ('ToL Core Lab', 'ToL Core Restricted Entities')
	AND f.name IN ('Core Lab Entities', 'Routine Throughput', 'Benchling MS Project Move', 'ToL Core Restricted Entities') -- Filtering by ToL Core Lab folders
	AND t.archived$ = FALSE -- Avoid including archived tissues. No tissue should be archived except when made in error.