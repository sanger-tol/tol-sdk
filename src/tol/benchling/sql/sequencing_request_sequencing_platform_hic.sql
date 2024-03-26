/* 
## SQL Query: HiC Submissions Benchling Warehouse (BWH)

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) tissue_prep_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) eln_file_registry_id: [character] id in Benchling Registry. Origin: BWH
5) programme_id: [character] ToLID.
6) specimen_id: [character] Origin: STS
7) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the HiC submission. 
8) fluidx_id: [character] Container barcode of the tissue prep fluidx tube. Origin: BWH
9) completion_date: [Date] Date of submission. For legacy data: merging of created_on and created_at$.
10) sequencing_platform: [character] Sequencing platform: HIC
11) bt_id: [character] B&T ID (legacy)
12) source: [character] Data source: v1, legacy_bnt

NOTES: 

1) Data Model: Result Assays attached to container level.
2) Some invalid Sanger Sample IDs are excluded in the WHERE clause. 
3) Legacy: Not all submissions have a date in created_on. Missing data filled with the date the tissue_prep was created in benchling. 
*/

WITH hic_submissions AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		tp.file_registry_id$ AS eln_file_registry,
		t.programme_id,
		t.specimen_id,
		ssid.sanger_sample_id, 
		c.barcode AS fluidx_id,
		hic.submitted_submission_date AS completion_date, 
		'hic'::varchar AS sequencing_platform,
		tp.bt_id,
		'v1'::varchar AS source
	FROM hic_submission_workflow2$raw AS hic
	LEFT JOIN container_content$raw AS cc 
		ON hic.sample_tube_id = cc.container_id
	LEFT JOIN container$raw AS c 
		ON cc.container_id = c.id
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON hic.sample_tube_id = ssid.sample_tube
	LEFT JOIN tissue_prep$raw AS tp 
		ON cc.entity_id = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id
	LEFT JOIN project$raw AS proj 
		ON tp.project_id$ = proj.id
	WHERE hic.archived$ = 'FALSE'
		AND ssid.sanger_sample_id IS NOT NULL
		AND ssid.sanger_sample_id != ''
		AND proj.name = 'ToL Core Lab'

),
hic_legacy_submissions AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		tp.file_registry_id$ AS eln_file_registry,
		t.programme_id,
		t.specimen_id,
		ssid.sanger_sample_id,
		c.barcode AS fluidx_id,
		COALESCE(DATE(tp.created_on), DATE(tp.created_at$)) AS completion_date,
		'hic'::varchar AS sequencing_platform,
		tp.bt_id,
		'legacy_bnt'::varchar AS source
	FROM sanger_sample_id$raw AS ssid
	LEFT JOIN container_content$raw AS cc 
		ON ssid.sample_tube = cc.container_id
	LEFT JOIN container$raw AS c 
		ON cc.container_id = c.id
	LEFT JOIN tissue_prep$raw AS tp 
		ON cc.entity_id = tp.id
	LEFT JOIN tissue$raw AS t 
		ON tp.tissue = t.id
    -- Selecting submisions migrated from B&T only
	WHERE tp.bt_id IS NOT NULL
		AND ssid.archived$ = FALSE
		-- Excluding not valid sanger sample ids
		AND ssid.sanger_sample_id NOT LIKE 'HOLD'

)
SELECT *
	FROM hic_submissions
	UNION
	SELECT *
	FROM hic_legacy_submissions