/* 
SQL Query: RNAseq Submissions Benchling Warehouse

Output: Table with cols: 

1) sanger_sample_id
2) tolid
3) fluidx_id: Fluidx ID of the original RNA extract the submission comes from. 
4) submission_type: Submission type code: RNASEQ

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_rna_extract_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) eln_file_registry_id: [character] id in Benchling Registry. Origin: BWH
5) tolid: [character] ToLID
6) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the HiC submission. 
7) tissue_prep_fluidx_id: [character] Container barcode of the tissue prep fluidx tube. Origin: BWH
8) completion_date: [Date] Date of submission. For legacy data: created_on.
9) sequencing_platform: [character] Sequencing platform: RNASEQ
10) source: [character] Data source: v1, legacy_bnt

NOTES: 

1) Data Model: Result Assays attached to container level.
2) Some invalid Fluidx IDs are excluded in the WHERE clause. 
*/

WITH rnaseq_submissions AS (

	SELECT DISTINCT 
		t.sts_id,
		t.taxon_id,
		rna.id AS eln_rna_extract_id,
		rna.file_registry_id$ AS eln_file_registry,
		t.tolid,
		ssid.sanger_sample_id, 
		c.barcode AS rna_fluidx_id,
		rnaseq_out.submitted_submission_date AS completion_date, 
		'rnaseq'::varchar AS sequencing_platform,
		'v1'::varchar AS source
	FROM rnaseq_sumbission$raw AS rnaseq
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON rnaseq.same_tube_id = ssid.sample_tube
	LEFT JOIN rna_sample$raw AS rna 
		ON rnaseq.sample_id = rna.id
	LEFT JOIN tissue_prep AS tp
		ON rna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	LEFT JOIN container_content$raw AS cc 
		ON rna.id = cc.entity_id
	LEFT JOIN container$raw AS c 
		ON cc.container_id = c.id
	LEFT JOIN rnaseq_sumbission_output$raw AS rnaseq_out
		ON rnaseq.id = rnaseq_out.workflow_task_id$
	WHERE rnaseq.archived$ = FALSE
		-- Selecting only valid FluidX IDs
		AND c.barcode LIKE 'F%'
	  	AND ssid.sanger_sample_id IS NOT NULL

),
rnaseq_legacy_submissions AS (
		
	SELECT DISTINCT 
		t.sts_id,
		t.taxon_id,
		rna.id AS eln_rna_extract_id,
		rna.file_registry_id$ AS eln_file_registry,
		t.tolid,
		ssid.sanger_sample_id, 
		c.barcode AS fluidx_id,
		rna.created_on AS completion_date, 
		'rnaseq'::varchar AS sequencing_platform,
		'legacy_bnt'::varchar AS source--,
-- 		rna.bt_id
	FROM sanger_sample_id$raw AS ssid
	LEFT JOIN container_content$raw AS cc 
		ON ssid.sample_tube = cc.container_id
	LEFT JOIN container$raw AS c 
		ON cc.container_id = c.id
	LEFT JOIN rna_sample$raw AS rna 
		ON cc.entity_id = rna.id
	LEFT JOIN tissue_prep AS tp
		ON rna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	-- Selecting submisions migrated from B&T only
	WHERE rna.bt_id IS NOT NULL
		AND ssid.archived$ = FALSE
	
)
SELECT *
	FROM rnaseq_submissions
	UNION
	SELECT * 
	FROM rnaseq_legacy_submissions
	
