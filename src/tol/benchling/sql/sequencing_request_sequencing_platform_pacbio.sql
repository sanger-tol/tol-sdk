/* 
## SQL Query: PacBio Submissions Benchling Warehouse (BWH)

This SQL query retrieves all the information of PacBio submissions that is 
relevant for the messaging queueu. 
It consists of 4 different SQL CTEs, each for a different data/submission model version:

	1. v1: Container based submission.
	2. v2: Plate based submission.
	3. legacy_bnt: Data migrated from Batches and Tracking system B&T.
	4. pooled DNA samples v1: Container based model for DNA pooled samples.

The table produced also contains the eln_submission_sample_id and eln_file_registry_id 
which uniquely idenfied each submission sample entity in Benchling Warehouse (BWH). 

The eln_dna_extract_id should be used as the foreign key to the DNA extract entity the
submission is derived from.

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) submission_sample_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) eln_file_registry_id: [character] id in Benchling Registry. Origin: BWH
5) extraction_id: [character] Original DNA extract entity name. For pooled samples, the first DNA extract pooled. Origin: BWH
6) pooled_sample_id: [character] DNA pooled sample id. Present only if the submitted sample was pooled. Origin: BWH
7) submission_sample_name: [character] Entity name. Origin: BWH
8) fluidx_id: [character] Container barcode of the DNA fluidx tube. Origin: BWH
9) programme_id: [character] ToLID. Origin: BWH
10) specimen_id: [character] Specimen ID. Origin: STS
11) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the PacBio submission. 
12) plate_name: [character] Name of submission plate.
13) pipeline: [character] name of the submission pipeline.
14) library_type: [character] Library type.
15) retention_instructions: [character] sample retention instructions
16) gb_yield_of_ccs_data_required: [double precision] CCS yield data required in GB.
17) number_of_smrt_cells_required: [double precision]
18) sheared_femto_fragment_size_bp: [double precision]
19) post_spri_concentration_ngul: [double precision]
20) post_spri_volume_ul: [jsonb]
21) nanodrop_260280: [double precision] 
22) nanodrop_260230: [double precision]
23) nanodrop_concentration_ngul: [double precision]
24) sample_prep_additional_requirements: [character]
25) include_5mc_cells_in_cpg_motifs: [character]
26) cc5_output_includes_kinetics_information: [character]
27) priority: [character]
28) completion_date: [Date]
29) sequencing_platform: [character] Sequencing platform: pacbio.
30) source: [character] Data source: v1, v2, legacy_bnt or v1_pooled

NOTES: 

1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the origininal DNA extract a few filters were applied to
delete Vouchers, tubes archived because they were made in error, and 
invalid container names. 
3) Vouchers: The volume filter is risky but necessary. A few container might be excluded. 
4) Pooled samples must be added as an independent CTE because the filters for DNA fluidx tubes
delete them from the query output. Two CTEs are used, one for the container based and the other
for the plate based submissions.

*/

WITH pacbio_submissions_v1 AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.file_registry_id$ AS eln_file_registry_id,
		subsam.original_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.barcode AS fluidx_id,
		t.programme_id, 
		t.specimen_id, 
		con.name AS sanger_sample_id, 
		NULL::varchar AS plate_name,
		NULL::varchar AS pipeline,
		pbsum.sequencing_type_please_fill AS library_type,
		NULL::varchar AS retention_instructions,
		NULL::float8 AS gb_yield_of_ccs_data_required,
		NULL::float8 AS number_of_smrt_cells_required,
		NULL::float8 AS sheared_femto_fragment_size_bp,
		NULL::float8 AS post_spri_concentration_ngul,
		NULL::jsonb AS post_spri_volume_ul,
		NULL::float8 AS nanodrop_260280, 
		NULL::float8 AS nanodrop_260230,
		NULL::float8 AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		NULL::varchar AS include_5mc_cells_in_cpg_motifs,
		NULL::varchar AS cc5_output_includes_kinetics_information,
		NULL::varchar AS priority,
		pbsum.submission_date AS completion_date, 
		'pacbio'::varchar AS sequencing_platform,
		'v1'::varchar AS source
	FROM pacbio_sequencing_submission2$raw AS pbsum
	LEFT JOIN container$raw AS con 
		ON pbsum.sample_tube_id = con.id
	LEFT JOIN container_content$raw AS cc 
		ON pbsum.sample_tube_id = cc.container_id
	LEFT JOIN submission_samples$raw AS subsam 
		ON cc.entity_id = subsam.id
	LEFT JOIN dna_extract$raw AS dna 
		ON subsam.original_dna_extract = dna.id
	LEFT JOIN tissue_prep$raw AS tp -- Chunk to add Tissue metadata
		ON dna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id -- End of Tissue metadata Chunk
	LEFT JOIN container_content$raw AS cc_dna -- Chunk to add DNA fluidx id
		ON dna.id = cc_dna.entity_id
	LEFT JOIN container$raw AS c_dna 
		ON cc_dna.container_id = c_dna.id
	LEFT JOIN tube$raw AS tube 
		ON c_dna.id = tube.id -- End of DNA fluidx id Chunk
	LEFT JOIN project$raw AS proj
		ON subsam.project_id$ = proj.id
	 LEFT JOIN folder$raw AS f 
        ON subsam.folder_id$ = f.id
	WHERE pbsum.archived$ = FALSE -- Excluding archived submission containers
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL  -- Selecting non-Voucher containers
		AND c_dna.volume_si * 1000000 != 10 -- Excluding vouchers without Voucher type in tube.type
	    AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab sbmissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')

),
pacbio_legacy_submissions AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.file_registry_id$ AS eln_file_registry_id,
		subsam.original_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.barcode AS fluidx_id,
		t.programme_id,
		t.specimen_id,
		con.name AS sanger_sample_id,
		NULL::varchar AS plate_name,
		NULL::varchar AS pipeline,
		NULL::varchar AS library_type,
		NULL::varchar AS retention_instructions,
		NULL::float8 AS gb_yield_of_ccs_data_required,
		NULL::float8 AS number_of_smrt_cells_required,
		NULL::float8 AS sheared_femto_fragment_size_bp,
		NULL::float8 AS post_spri_concentration_ngul,
		NULL::jsonb AS post_spri_volume_ul,
		NULL::float8 AS nanodrop_260280, 
		NULL::float8 AS nanodrop_260230,
		NULL::float8 AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		NULL::varchar AS include_5mc_cells_in_cpg_motifs,
		NULL::varchar AS cc5_output_includes_kinetics_information,
		NULL::varchar AS priority,
		subsam.created_at$ AS completion_date, 
		'pacbio'::varchar AS sequencing_platform,
		'legacy_bnt'::varchar AS source
	FROM submission_samples$raw AS subsam
	LEFT JOIN container_content$raw AS cc 
		ON subsam.id = cc.entity_id
	LEFT JOIN container$raw AS con 
		ON cc.container_id = con.id
	LEFT JOIN dna_extract$raw AS dna 
		ON subsam.original_dna_extract = dna.id
	LEFT JOIN tissue_prep$raw AS tp -- Chunk to add Tissue metadata
		ON dna.tissue_prep = tp.id 
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id -- End of Tissue metadata Chunk
	LEFT JOIN container_content$raw AS cc_dna -- Chunk to add DNA fluidx id
		ON dna.id = cc_dna.entity_id
	LEFT JOIN container$raw AS c_dna 
		ON cc_dna.container_id = c_dna.id
	LEFT JOIN tube$raw AS tube 
		ON c_dna.id = tube.id -- End of DNA fluidx id Chunk
	LEFT JOIN project$raw AS proj
		ON subsam.project_id$ = proj.id
	WHERE subsam.bt_id IS NOT NULL -- Selecting submisions migrated from B&T only
		AND con.barcode NOT LIKE 'F%' -- Excluding samples not submitted. Select only Sanger Sample IDs
		AND con.archived$ = FALSE -- Excluding submission-containers made by mistake
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL -- Selecting non-Voucher containers
		AND c_dna.volume_si * 1000000 != 10 -- Excluding vouchers without Voucher type in tube.type
	    AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab sbmissions only

),
pacbio_submissions_v2 AS (
	
	SELECT DISTINCT	
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.file_registry_id$ AS eln_file_registry_id,
		subsam.originaL_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.barcode AS fluidx_id,
		t.programme_id,
		t.specimen_id,
		con.name AS sanger_sample_id,
		plt.name AS plate_name,
		pbsubm_p.pipeline,
		pbsubm_p.library_type,
		pbsubm_p.retention_instructions,
		pbsubm_p.gb_yield_of_ccs_data_required,
		pbsubm_p.number_of_smrt_cells_required,
		pbsubm_p.sheared_femto_fragment_size_bp,
		pbsubm_p.post_spri_concentration_ngul,
		pbsubm_p.post_spri_volume_ul,
		pbsubm_p.nanodrop_260280, 
		pbsubm_p.nanodrop_260230,
		pbsubm_p.nanodrop_concentration_ngul,
		pbsubm_p.sample_prep_additional_requirements,
		pbsubm_p.include_5mc_cells_in_cpg_motifs,
		pbsubm_p.cc5_output_includes_kinetics_information,
		pbsubm_p.priority,
		pbsubm_p.created_at$ AS completion_date, 
		'pacbio'::varchar AS sequencing_platform,
		'v2'::varchar AS source
	FROM pacbio_submission_plate_output$raw AS pbsubm_p
	LEFT JOIN submission_samples$raw AS subsam 
		ON pbsubm_p.sample_name = subsam.id
	LEFT JOIN dna_extract$raw AS dna 
		ON subsam.original_dna_extract = dna.id
	LEFT JOIN tissue_prep$raw AS tp -- Chunk to add Tissue metadata
		ON dna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id -- End of Tissue metadata Chunk
	LEFT JOIN container$raw AS con 
		ON pbsubm_p.sanger_uuid ->> 0 = con.id
	LEFT JOIN plate$raw AS plt 
		ON con.plate_id = plt.id
	LEFT JOIN container_content$raw AS cc_dna -- Chunk to add DNA fluidx id
		ON dna.id = cc_dna.entity_id
	LEFT JOIN container$raw AS c_dna 
		ON cc_dna.container_id = c_dna.id
	LEFT JOIN tube$raw AS tube 
		ON c_dna.id = tube.id -- End of DNA fluidx id Chunk
	LEFT JOIN project$raw AS proj
		ON subsam.project_id$ = proj.id
	LEFT JOIN folder$raw AS f 
		ON subsam.folder_id$ = f.id
	WHERE con.archived$ = FALSE -- Excluding archived submission containers
		AND pbsubm_p.archived$ = FALSE -- Exclusing archived submissions
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL -- Selecting non-Voucher containers
		-- AND c_dna.volume_si * 1000000 != 10 -- Excluding vouchers without Voucher type in tube.type (commented out as some tubes do have 10ul volume!)
		AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab sbmissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D Sample Processing Requests')

		
),
pacbio_submissions_pooled_v1 AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.file_registry_id$ AS eln_file_registry_id,
		subsam.pooled_sample  AS extraction_id,
		subsam.name$ AS eln_submission_sample_name,
		c_pool.barcode AS fluidx_id,
		t.programme_id, 
		t.specimen_id, 
		con.name AS sanger_sample_id, 
		NULL::varchar AS plate_name,
		NULL::varchar AS pipeline,
		pbsum.sequencing_type_please_fill AS library_type,
		NULL::varchar AS retention_instructions,
		NULL::float8 AS gb_yield_of_ccs_data_required,
		NULL::float8 AS number_of_smrt_cells_required,
		NULL::float8 AS sheared_femto_fragment_size_bp,
		NULL::float8 AS post_spri_concentration_ngul,
		NULL::jsonb AS post_spri_volume_ul,
		NULL::float8 AS nanodrop_260280, 
		NULL::float8 AS nanodrop_260230,
		NULL::float8 AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		NULL::varchar AS include_5mc_cells_in_cpg_motifs,
		NULL::varchar AS cc5_output_includes_kinetics_information,
		NULL::varchar AS priority,
		pbsum.submission_date AS completion_date, 
		'pacbio'::varchar AS sequencing_platform,
		'v1_pooled'::varchar AS source
	FROM pacbio_sequencing_submission2$raw AS pbsum
	LEFT JOIN container$raw AS con 
		ON pbsum.sample_tube_id = con.id
	LEFT JOIN container_content$raw AS cc 
		ON pbsum.sample_tube_id = cc.container_id
	LEFT JOIN submission_samples$raw AS subsam 
		ON cc.entity_id = subsam.id
	LEFT JOIN pooled_samples$raw AS pool 
		ON subsam.pooled_sample = pool.id
	LEFT JOIN dna_extract$raw AS dna -- Chunk to add Tissue metadata
		ON pool.samples ->> 0 = dna.id
	LEFT JOIN tissue_prep$raw AS tp 
		ON dna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id -- End of Tissue metadata Chunk
	LEFT JOIN container_content$raw AS cc_pool -- Chunk to add DNA fluidx id
		ON pool.id = cc_pool.entity_id
	LEFT JOIN container$raw AS c_pool 
		ON cc_pool.container_id = c_pool.id
	LEFT JOIN tube$raw AS tube 
		ON c_pool.id = tube.id -- End of DNA fluidx id Chunk
	LEFT JOIN project$raw AS proj
		ON subsam.project_id$ = proj.id
	LEFT JOIN folder$raw AS f 
		ON subsam.folder_id$ = f.id
	WHERE pbsum.archived$ = FALSE -- Excluding archived submission containers
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL  -- Selecting non-Voucher containers
	    AND (c_pool.archive_purpose$ != ('Made in error') OR c_pool.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND subsam.pooled_sample IS NOT NULL
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab sbmissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')
),
pacbio_submissions_pooled_v2 AS (

	SELECT DISTINCT	
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS eln_submission_sample_id,
		subsam.file_registry_id$ AS eln_file_registry_id,
		subsam.pooled_sample AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_pool.barcode AS fluidx_id,
		t.programme_id,
		t.specimen_id,
		con.name AS sanger_sample_id,
		plt.name AS plate_name,
		pbsubm_p.pipeline,
		pbsubm_p.library_type,
		pbsubm_p.retention_instructions,
		pbsubm_p.gb_yield_of_ccs_data_required,
		pbsubm_p.number_of_smrt_cells_required,
		pbsubm_p.sheared_femto_fragment_size_bp,
		pbsubm_p.post_spri_concentration_ngul,
		pbsubm_p.post_spri_volume_ul,
		pbsubm_p.nanodrop_260280, 
		pbsubm_p.nanodrop_260230,
		pbsubm_p.nanodrop_concentration_ngul,
		pbsubm_p.sample_prep_additional_requirements,
		pbsubm_p.include_5mc_cells_in_cpg_motifs,
		pbsubm_p.cc5_output_includes_kinetics_information,
		pbsubm_p.priority,
		DATE(pbsubm_p.created_at$) AS completion_date, 
		'pacbio'::varchar AS sequencing_platform,
		'v2_pooled'::varchar AS source
	FROM pacbio_submission_plate_output$raw AS pbsubm_p
	LEFT JOIN submission_samples$raw AS subsam 
		ON pbsubm_p.sample_name = subsam.id
	LEFT JOIN pooled_samples$raw AS pool 
		ON subsam.pooled_sample = pool.id
	LEFT JOIN dna_extract$raw AS dna -- Chunk to add Tissue metadata
		ON pool.samples ->> 0 = dna.id
	LEFT JOIN tissue_prep$raw AS tp 
		ON dna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id -- End of Tissue metadata Chunk
	LEFT JOIN container_content$raw AS cc_pool -- Chunk to add DNA fluidx id
		ON pool.id = cc_pool.entity_id
	LEFT JOIN container$raw AS c_pool 
		ON cc_pool.container_id = c_pool.id
	LEFT JOIN tube$raw AS tube 
		ON c_pool.id = tube.id -- End of DNA fluidx id Chunk
	LEFT JOIN container$raw AS con -- To add sanger uuid
		ON pbsubm_p.sanger_uuid ->> 0 = con.id
	LEFT JOIN plate$raw AS plt 
		ON con.plate_id = plt.id
	LEFT JOIN project$raw AS proj
		ON subsam.project_id$ = proj.id
	LEFT JOIN folder$raw AS f 
		ON subsam.folder_id$ = f.id
	WHERE subsam.pooled_sample IS NOT NULL
		AND proj.name = 'ToL Core Lab'
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D Sample Processing Requests')
		AND pbsubm_p.archived$ = FALSE
	
)
SELECT *
FROM pacbio_submissions_v1
UNION  
SELECT *
FROM pacbio_submissions_v2
UNION 
SELECT *
FROM pacbio_legacy_submissions
UNION 
SELECT *
FROM pacbio_submissions_pooled_v1
UNION 
SELECT *
FROM pacbio_submissions_pooled_v2
ORDER BY source DESC