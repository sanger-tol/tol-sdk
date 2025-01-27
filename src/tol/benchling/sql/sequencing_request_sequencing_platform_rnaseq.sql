/* 
SQL Query: RNAseq Submissions Benchling Warehouse

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) extraction_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) eln_file_registry_id: [character] id in Benchling Registry. Origin: BWH
5) programme_id: [character] ToLID.
6) specimen_id: [character] ToLID.
7) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the HiC submission. 
8) fluidx_id: [character] Container barcode of the tissue prep fluidx tube. Origin: BWH
9) completion_date: [Date] Date of submission. For legacy data: created_on.
10) sequencing_platform: [character] Sequencing platform: RNASEQ
11) source: [character] Data source: legacy_bnt, v1

NOTES: 

1) Data Model: Result Assays attached to container level.
*/

WITH rnaseq_submissions AS (

	SELECT DISTINCT 
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		rna.id AS extraction_id,
		rna.file_registry_id$ AS eln_file_registry,
		t.programme_id,
		t.specimen_id,
		ssid.sanger_sample_id, 
		con.barcode AS fluidx_id,
		rnaseq_out.submitted_submission_date AS completion_date, 
		'rnaseq'::varchar AS sequencing_platform,
		rna.bt_id,
		'v1'::varchar AS source
	FROM rnaseq_sumbission$raw AS rnaseq
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON rnaseq.same_tube_id = ssid.sample_tube
	LEFT JOIN rna_extract$raw AS rna 
		ON rnaseq.sample_id = rna.id
	LEFT JOIN tissue_prep AS tp
		ON rna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	LEFT JOIN container_content$raw AS cc 
		ON rna.id = cc.entity_id
	LEFT JOIN container$raw AS con 
		ON cc.container_id = con.id
	LEFT JOIN rnaseq_sumbission_output$raw AS rnaseq_out
		ON rnaseq.id = rnaseq_out.workflow_task_id$
	LEFT JOIN folder$raw AS f 
			ON rna.folder_id$ = f.id
		LEFT JOIN project$raw AS proj
			ON rna.project_id$ = proj.id
	WHERE rnaseq.archived$ = FALSE
		-- Selects Fluidx only and excludes well:plate ids
		AND con.plate_id IS NULL
	  	AND ssid.sanger_sample_id IS NOT NULL
		AND proj.name = 'ToL Core Lab'
		AND f.name IN ('Routine Throughput', 'RNA', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')


),
rnaseq_legacy_submissions AS (
		
	SELECT DISTINCT 
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		rna.id AS extraction_id,
		rna.file_registry_id$ AS eln_file_registry,
		t.programme_id,
		t.specimen_id,
		ssid.sanger_sample_id, 
		c.barcode AS fluidx_id,
		rna.created_on AS completion_date, 
		'rnaseq'::varchar AS sequencing_platform,
		rna.bt_id,
		'legacy_bnt'::varchar AS source
	FROM sanger_sample_id$raw AS ssid
	LEFT JOIN container_content$raw AS cc 
		ON ssid.sample_tube = cc.container_id
	LEFT JOIN container$raw AS c 
		ON cc.container_id = c.id
	LEFT JOIN rna_extract$raw AS rna 
		ON cc.entity_id = rna.id
	LEFT JOIN tissue_prep AS tp
		ON rna.tissue_prep = tp.id
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	LEFT JOIN folder$raw AS f 
		ON rna.folder_id$ = f.id
	LEFT JOIN project$raw AS proj
		ON rna.project_id$ = proj.id
	-- Selecting submisions migrated from B&T only
	WHERE rna.bt_id IS NOT NULL
		AND ssid.archived$ = FALSE
		AND proj.name = 'ToL Core Lab'
		AND f.name IN ('Routine Throughput', 'RNA', 'Submissions', 'Core Lab Entities', 'Benchling MS Project Move')

	
)
SELECT *
	FROM rnaseq_submissions
	UNION
	SELECT * 
	FROM rnaseq_legacy_submissions
