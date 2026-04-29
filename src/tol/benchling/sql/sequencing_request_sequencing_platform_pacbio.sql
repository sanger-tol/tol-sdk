/* 
## SQL Query: PacBio Submissions Benchling Warehouse (BWH)

This SQL query retrieves all the information of PacBio submissions that is 
relevant for the messaging queueu. 
It consists of 6 different SQL CTEs, each for a different data/submission model version:

	1. v1: Container based submission.
	2. v2: Plate based submission.
	3. legacy_bnt: Data migrated from Batches and Tracking system B&T.
	4. pooled DNA samples v1: Container based model for DNA pooled samples.

The eln_dna_extract_id should be used as the foreign key to the DNA extract entity the
submission is derived from.

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) submission_sample_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) extraction_id: [character] Original DNA extract entity name. For pooled samples, the first DNA extract pooled. Origin: BWH
5) submission_sample_name: [character] Entity name. Origin: BWH
6) fluidx_container_id: [character] Container id of the DNA fluidx tube. Origin: BWH
7) tube_id: [character] Barcode of the DNA container.
7) programme_id: [character] ToLID. Origin: BWH
8) specimen_id: [character] Specimen ID. Origin: STS
9) tube_name: [character] Name of the submission tube/container.
10) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the PacBio submission. 
11) plate_name: [character] Name of submission plate.
12) library_type: [character] Library type.
13) number_of_smrt_cells_required: [double precision]
14) sheared_femto_fragment_size_bp: [double precision]
15) post_spri_concentration_ngul: [double precision]
16) post_spri_volume_ul: [jsonb]
17) nanodrop_260280: [double precision] 
18) nanodrop_260230: [double precision]
19) nanodrop_concentration_ngul: [double precision]
20) sample_prep_additional_requirements: [character]
21) library_batch_id: [character] Library batch ID from LR Benchling. Origin: BWH
22) completion_date: [Date]
23) sequencing_platform: [character] Sequencing platform: pacbio.
24) source: [character] Data source: v1, v1_pooled, v2, v2_pooled, legacy_bnt

NOTES: 

1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to
delete Vouchers, tubes archived because they were made in error, and 
invalid container names. 
3) Pooled samples must be added as an independent CTE because the filters for DNA fluidx tubes
delete them from the query output. Two CTEs are used, one for the container based and the other
for the plate based submissions.

*/

-- container based submissions
WITH 
pacbio_submissions_container_routine AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.original_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.id AS fluidx_container_id,
		t.programme_id, 
		t.specimen_id, 
		con.barcode AS tube_id,
		CASE
			WHEN pbsum.submission_date < DATE '2025-09-01'
				THEN con.name
			ELSE ssid.sanger_sample_id
		END AS sanger_sample_id,
		NULL::varchar AS plate_name,
		pbsum.sequencing_type_please_fill AS library_type,
		pbsum.smrt_cells_required AS number_of_smrt_cells_required,
		femto.average_fragment_size AS sheared_femto_fragment_size_bp,
		qubit.qubit_concentration_ngul AS post_spri_concentration_ngul,
		NULL::jsonb AS post_spri_volume_ul,
		nano._260_280_ratio AS nanodrop_260280, 
		nano._260_230_ratio AS nanodrop_260230,
		nano.nanodrop_concentration_ngul AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		NULL::varchar AS library_batch_id,
		spri.spri_type,
		spri.bead_type,
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
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON con.id = ssid.sample_tube
	LEFT JOIN femto_pacbio_prep_v2$raw AS femto
		ON femto.sample_id = subsam.id
	LEFT JOIN qubit_measurements_v2$raw AS qubit
		ON qubit.sample_id = subsam.id
	LEFT JOIN nanodrop_measurements_v2$raw AS nano
		ON nano.sample_id = subsam.id
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id
	LEFT JOIN workflow_task$raw AS wft
		ON pbsum.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE pbsum.archived$ = FALSE -- Excluding archived submission containers
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL  -- Selecting non-Voucher containers
	    AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab submissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')
		AND wfts.status_type = 'COMPLETED'
),

pacbio_submissions_container_pooled AS (

	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.pooled_sample  AS extraction_id,
		subsam.name$ AS eln_submission_sample_name,
		c_pool.id AS fluidx_container_id,
		t.programme_id, 
		t.specimen_id,
		con.name AS tube_id,
		CASE
			WHEN pbsum.submission_date < DATE '2025-09-01'
				THEN con.name
			ELSE ssid.sanger_sample_id
		END AS sanger_sample_id,
		NULL::varchar AS plate_name,
		pbsum.sequencing_type_please_fill AS library_type,
		pbsum.smrt_cells_required AS number_of_smrt_cells_required,
		femto.average_fragment_size AS sheared_femto_fragment_size_bp,
		qubit.qubit_concentration_ngul AS post_spri_concentration_ngul,
		NULL::jsonb AS post_spri_volume_ul,
		nano._260_280_ratio AS nanodrop_260280, 
		nano._260_230_ratio AS nanodrop_260230,
		nano.nanodrop_concentration_ngul AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		NULL::varchar AS library_batch_id,
		spri.spri_type AS spri_type,
		spri.bead_type AS bead_type,
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
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON con.id = ssid.sample_tube
	LEFT JOIN femto_pacbio_prep_v2$raw AS femto
		ON femto.sample_id = subsam.id
	LEFT JOIN qubit_measurements_v2$raw AS qubit
		ON qubit.sample_id = subsam.id
	LEFT JOIN nanodrop_measurements_v2$raw AS nano
		ON nano.sample_id = subsam.id
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id
	LEFT JOIN workflow_task$raw AS wft
		ON pbsum.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE pbsum.archived$ = FALSE -- Excluding archived submission containers
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL  -- Selecting non-Voucher containers
	    AND (c_pool.archive_purpose$ != ('Made in error') OR c_pool.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND subsam.pooled_sample IS NOT NULL
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab sbmissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')
		AND wfts.status_type = 'COMPLETED'
),

pacbio_submissions_container_legacy_deprecated AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.original_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.id AS fluidx_container_id,
		t.programme_id,
		t.specimen_id,
		con.name AS tube_id,
		con.name AS sanger_sample_id,
		NULL::varchar AS plate_name,
		NULL::varchar AS library_type,
		NULL::float8 AS number_of_smrt_cells_required,
		femto.average_fragment_size AS sheared_femto_fragment_size_bp,
		qubit.qubit_concentration_ngul AS post_spri_concentration_ngul,
		NULL::jsonb AS post_spri_volume_ul,
		nano._260_280_ratio AS nanodrop_260280, 
		nano._260_230_ratio AS nanodrop_260230,
		nano.nanodrop_concentration_ngul AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		NULL::varchar AS library_batch_id,
		spri.spri_type AS spri_type,
		spri.bead_type AS bead_type,
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
	LEFT JOIN femto_pacbio_prep_v2$raw AS femto
		ON femto.sample_id = subsam.id -- Chunk to add femto data to legacy submissions
	LEFT JOIN qubit_measurements_v2$raw AS qubit
		ON qubit.sample_id = subsam.id -- Chunk to add qubit data to legacy submissions
	LEFT JOIN nanodrop_measurements_v2$raw AS nano
		ON nano.sample_id = subsam.id -- Chunk to add nanodrop data to legacy submissions
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id -- Chunk to add spri data to legacy submissions
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
	    AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab submissions only
),

-- plate based submissions
pacbio_submissions_plate_automated_manifest AS (
	SELECT DISTINCT	
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.originaL_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.id AS fluidx_container_id,
		t.programme_id,
		t.specimen_id,
		con.name AS tube_id,
		con.name AS sanger_sample_id,
		plt.name AS plate_name,
		pbsubm_p.library_type,
		pbsubm_p.number_of_smrt_cells_required,
		pbsubm_p.sheared_femto_fragment_size_bp,
		pbsubm_p.post_spri_concentration_ngul,
		pbsubm_p.post_spri_volume_ul,
		pbsubm_p.nanodrop_260280, 
		pbsubm_p.nanodrop_260230,
		pbsubm_p.nanodrop_concentration_ngul,
		pbsubm_p.sample_prep_additional_requirements,
		NULL::varchar AS library_batch_id,
		spri.spri_type,
		spri.bead_type,
		DATE(pbsubm_p.created_at$) AS completion_date, 
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
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id
	LEFT JOIN workflow_task$raw AS wft
		ON pbsubm_p.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE con.archived$ = FALSE -- Excluding archived submission containers
		AND pbsubm_p.archived$ = FALSE -- Exclusing archived submissions
		-- Filters to add DNA extract fluidx tubes
		AND tube.type IS NULL -- Selecting non-Voucher containers
		AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab sbmissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D Sample Processing Requests')
		AND wfts.status_type = 'COMPLETED'
),

pacbio_submissions_plate_automated_manifest_pooled AS (

	SELECT DISTINCT	
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS eln_submission_sample_id,
		subsam.pooled_sample AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_pool.id AS fluidx_container_id,
		t.programme_id,
		t.specimen_id,
		con.name AS tube_id,
		con.name AS sanger_sample_id,
		plt.name AS plate_name,
		pbsubm_p.library_type,
		pbsubm_p.number_of_smrt_cells_required,
		pbsubm_p.sheared_femto_fragment_size_bp,
		pbsubm_p.post_spri_concentration_ngul,
		pbsubm_p.post_spri_volume_ul,
		pbsubm_p.nanodrop_260280, 
		pbsubm_p.nanodrop_260230,
		pbsubm_p.nanodrop_concentration_ngul,
		pbsubm_p.sample_prep_additional_requirements,
		NULL::varchar AS library_batch_id,
		spri.spri_type AS spri_type,
		spri.bead_type AS bead_type,
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
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id
	LEFT JOIN workflow_task$raw AS wft
		ON pbsubm_p.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE subsam.pooled_sample IS NOT NULL
		AND proj.name = 'ToL Core Lab'
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D Sample Processing Requests')
		AND pbsubm_p.archived$ = FALSE
		AND wfts.status_type = 'COMPLETED'
),

pacbio_submissions_plate_routine AS (

	SELECT 
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.original_dna_extract AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_dna.id AS fluidx_container_id,
		t.programme_id,
		t.specimen_id,
		c_subsam.name AS tube_id,
		ssid.sanger_sample_id AS sanger_sample_id,
		plate.name$ AS plate_name,
		pbsubm_p.sequencing_type AS library_type,
		pbsubm_p.number_of_smrt_cells_required,
		femto.average_fragment_size AS sheared_femto_fragment_size_bp,
		qubit.qubit_concentration_ngul AS post_spri_concentration_ngul,
		NULL::JSONB AS post_spri_volume_ul,
		nano._260_280_ratio AS nanodrop_260280,
		nano._260_230_ratio AS nanodrop_260230,
		nano.nanodrop_concentration_ngul AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		lpb.name$ AS library_batch_id,
		spri.spri_type AS spri_type,
		spri.bead_type AS bead_type,
		pbsubm_p.created_at$ AS completion_date,
		'pacbio'::varchar AS sequencing_platform,
		'v2'::varchar AS SOURCE
	FROM pacbio_sequencing_submission_plate_output$raw AS pbsubm_p
	LEFT JOIN submission_samples$raw AS subsam 
		ON pbsubm_p.submission_sample = subsam.id
	LEFT JOIN container_content$raw AS cc_subsam -- Chunk to connect SubSam to the well
		ON subsam.id = cc_subsam.entity_id
	LEFT JOIN container$raw AS c_subsam
		ON cc_subsam.container_id = c_subsam.id -- End of connecting SubSam to well
	LEFT JOIN dna_extract$raw AS dna 
		ON subsam.original_dna_extract = dna.id
	LEFT JOIN tissue_prep$raw AS tp 
		ON dna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id
	LEFT JOIN container$raw AS con 
		ON pbsubm_p.plate_well_id ->>0 = con.id
	LEFT JOIN container_content$raw AS cc_dna -- Chunk to add DNA fluidx id
		ON dna.id = cc_dna.entity_id
	LEFT JOIN container$raw AS c_dna 
		ON cc_dna.container_id = c_dna.id
	LEFT JOIN tube$raw AS tube 
		ON c_dna.id = tube.id -- End of DNA fluidx id Chunk
	LEFT JOIN "_96w_pacbio_plate$raw" AS plate 
		ON con.plate_id = plate.id
	LEFT JOIN sanger_sample_id$raw AS ssid
		ON con.id = ssid.sample_tube
	LEFT JOIN femto_pacbio_prep_v2$raw AS femto
		ON femto.sample_id = subsam.id
	LEFT JOIN qubit_measurements_v2$raw AS qubit
		ON qubit.sample_id = subsam.id
	LEFT JOIN nanodrop_measurements_v2$raw AS nano
		ON nano.sample_id = subsam.id
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id
	LEFT JOIN lr_long_read_library_preparation_b$raw AS lr_proc -- Chunk to add LR lib prep batch ID
		ON lr_proc.sanger_sample_id = ssid.sanger_sample_id
	LEFT JOIN lr_library_preparation_batch$raw AS lpb
		ON lr_proc.library_preparation_batch = lpb.id -- End of chunk to add LR lib prep batch ID
	LEFT JOIN project$raw AS proj 
		ON subsam.project_id$ = proj.id
	 LEFT JOIN folder$raw AS f 
        ON subsam.folder_id$ = f.id
	LEFT JOIN workflow_task$raw AS wft
		ON pbsubm_p.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE pbsubm_p.archived$ = FALSE -- Excluding archived submissions
		AND tube.type IS NULL  -- Selecting non-Voucher containers
	    AND (c_dna.archive_purpose$ != ('Made in error') OR c_dna.archive_purpose$ IS NULL) -- Excluding containers made by mistake
		AND c_dna.barcode LIKE 'F%' -- Selecting only valid FluidX IDs
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab submissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')
		AND wfts.status_type = 'COMPLETED'
),

pacbio_submissions_plate_routine_pooled AS (
	SELECT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		subsam.id AS submission_sample_id,
		subsam.pooled_sample AS extraction_id,
		subsam.name$ AS submission_sample_name,
		c_pool.id AS fluidx_container_id,
		t.programme_id,
		t.specimen_id,
		c_subsam.name AS tube_id,
		ssid.sanger_sample_id AS sanger_sample_id,
		plate.name$ AS plate_name,
		pbsubm_p.sequencing_type AS library_type,
		pbsubm_p.number_of_smrt_cells_required,
		femto.average_fragment_size AS sheared_femto_fragment_size_bp,
		qubit.qubit_concentration_ngul AS post_spri_concentration_ngul,
		NULL::JSONB AS post_spri_volume_ul,
		nano._260_280_ratio AS nanodrop_260280,
		nano._260_230_ratio AS nanodrop_260230,
		nano.nanodrop_concentration_ngul AS nanodrop_concentration_ngul,
		NULL::varchar AS sample_prep_additional_requirements,
		lpb.name$ AS library_batch_id,
		spri.spri_type AS spri_type,
		spri.bead_type AS bead_type,
		pbsubm_p.created_at$ AS completion_date,
		'pacbio'::varchar AS sequencing_platform,
		'v2'::varchar AS SOURCE
	FROM pacbio_sequencing_submission_plate_output$raw AS pbsubm_p
	LEFT JOIN submission_samples$raw AS subsam 
		ON pbsubm_p.submission_sample = subsam.id
	LEFT JOIN container_content$raw AS cc_subsam -- Connect SubSam to the well
		ON subsam.id = cc_subsam.entity_id
	LEFT JOIN container$raw AS c_subsam
		ON cc_subsam.container_id = c_subsam.id -- End of chunk to connect subsam to the well
	LEFT JOIN container$raw AS con -- Chunk to get plate ID
		ON pbsubm_p.plate_well_id ->>0 = con.id
	LEFT JOIN "_96w_pacbio_plate$raw" AS plate 
		ON con.plate_id = plate.id -- End of chunk to get the plate ID
	LEFT JOIN sanger_sample_id$raw AS ssid
		ON con.id = ssid.sample_tube
	LEFT JOIN femto_pacbio_prep_v2$raw AS femto
		ON femto.sample_id = subsam.id
	LEFT JOIN qubit_measurements_v2$raw AS qubit
		ON qubit.sample_id = subsam.id
	LEFT JOIN nanodrop_measurements_v2$raw AS nano
		ON nano.sample_id = subsam.id
	LEFT JOIN spri_info_v2$raw AS spri
		ON spri.sample_id = subsam.id
	LEFT JOIN pooled_samples$raw AS pool 
		ON subsam.pooled_sample = pool.id
	LEFT JOIN container_content$raw AS cc_pool -- Chunk to connect pooled sample to the FluidX tube
		ON pool.id = cc_pool.entity_id
	LEFT JOIN container$raw AS c_pool
		ON cc_pool.container_id = c_pool.id -- End of chunk to connect pooled sample to the FluidX tube
	LEFT JOIN dna_extract$raw AS dna -- Chunk to add Tissue metadata
		ON pool.samples ->> 0 = dna.id
	LEFT JOIN tissue_prep$raw AS tp 
		ON dna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id -- End of Tissue metadata Chunk
	LEFT JOIN lr_long_read_library_preparation_b$raw AS lr_proc -- Chunk to add LR lib prep batch ID
		ON lr_proc.sanger_sample_id = ssid.sanger_sample_id
	LEFT JOIN lr_library_preparation_batch$raw AS lpb
		ON lr_proc.library_preparation_batch = lpb.id -- End of chunk to add LR lib prep batch ID
	LEFT JOIN project$raw AS proj
		ON subsam.project_id$ = proj.id
	 LEFT JOIN folder$raw AS f 
        ON subsam.folder_id$ = f.id
	LEFT JOIN workflow_task$raw AS wft
		ON pbsubm_p.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE subsam.pooled_sample IS NOT NULL
	    AND pbsubm_p.archived$ = FALSE
		AND proj.name = 'ToL Core Lab' -- Selecting ToL Core Lab submissions only
		AND f.name IN ('Routine Throughput', 'PacBio prep', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')
		AND wfts.status_type = 'COMPLETED'
)

SELECT *
FROM pacbio_submissions_container_routine
UNION  
SELECT *
FROM pacbio_submissions_container_pooled
UNION 
SELECT *
FROM pacbio_submissions_container_legacy_deprecated
UNION 
SELECT *
FROM pacbio_submissions_plate_automated_manifest
UNION 
SELECT *
FROM pacbio_submissions_plate_automated_manifest_pooled
UNION
SELECT *
FROM pacbio_submissions_plate_routine
UNION 
SELECT *
FROM pacbio_submissions_plate_routine_pooled
ORDER BY source DESC
