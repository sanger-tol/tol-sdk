/* 
## SQL Query: HiC Submissions Benchling Warehouse (BWH)

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) tissue_prep_id: [character] Foreign key to other entities and results in Benchling. Origin: BWH
4) submission_sample_name: [character] The name of the entity that is being submitted
4) programme_id: [character] ToLID.
5) specimen_id: [character] Origin: STS
6) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the HiC submission. 
7) tube_id: [character] Container barcode of the tissue prep fluidx tube. Origin: BWH
8) completion_date: [Date] Date of submission. For legacy data: merging of created_on and created_at$.
9) sequencing_platform: [character] Sequencing platform: HIC
10) bt_id: [character] B&T ID (legacy)
11) source: [character] Data source: v1, legacy_bnt

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
		tp.name$ AS submission_sample_name,
		t.programme_id,
		t.specimen_id,
		ssid.sanger_sample_id, 
		c.barcode AS tube_id,
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
	LEFT JOIN workflow_task$raw AS wft
		ON hic.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
	WHERE hic.archived$ = 'FALSE'
		AND ssid.sanger_sample_id IS NOT NULL
		AND ssid.sanger_sample_id != ''
		AND proj.name = 'ToL Core Lab'
		AND wfts.status_type = 'COMPLETED'

),
hic_legacy_submissions AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		tp.id AS tissue_prep_id,
		tp.name$ as submission_sample_name,
		t.programme_id,
		t.specimen_id,
		ssid.sanger_sample_id,
		c.barcode AS tube_id,
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