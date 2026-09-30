/* 
## SQL Query: LRES PacBio Submissions Benchling Warehouse (BWH)

This query retrieves information about LRES PacBio submissions from the Benchling Warehouse (BWH).
It provides details about the library preparation process for samples submitted to LRES, for samples that have been processed within the LR Benchling system.

1) sts_id: STS Sample ID
2) taxon_id: Taxon ID
3) tissue_prep_id: Benchling Tissue Prep ID
4) extraction_id: Sanger Sample ID for LRES extractions
5) programme_id: ToLID
6) specimen_id: Specimen ID
7) sanger_sample_id: Sanger Sample ID
8) library_type: Type of library, always LI for LR Benchling library preps
9) library_batch_id: Benchling Library Batch ID
10) library_container_id: Benchling Library Container ID
11) completion_date: Date the submission was completed
12) library_prep_receipt_date: Date the library prep was received in the lab
13) library_prep_completion_date: Date the library prep was completed
14) library_prep_qc_decision: QC decision for the library prep
15) sequencing_platform: Sequencing platform, always 'pacbio'
16) source: Source of the data
*/

WITH lr_lib AS (
	SELECT
		sr.sanger_sample_id,
		lpb.name$ AS library_batch_id,
		psbc.barcode AS library_container_id,
		sr.date_arrived_in_lab AS library_prep_receipt_date,
		CASE
			WHEN lps.id IS NOT NULL
				THEN DATE(lpsc.created_at$)
			ELSE DATE (psb.created_at$)
		END AS library_prep_completion_date,
		CASE 
			WHEN lps.id IS NOT NULL THEN
				CASE WHEN lpsc.final_sample_decision IS NOT NULL
					THEN lpsc.final_sample_decision
				ELSE 'Sample Status Check'
			END
			ELSE psb.decision 
		END AS library_prep_qc_decision
	FROM lr_library_preparation_sample_receipt_output$raw AS sr
	LEFT JOIN lr_long_read_library_preparation_b$raw AS lr_proc
		ON lr_proc.sanger_sample_id = sr.sanger_sample_id
	LEFT JOIN lr_library_preparation_batch$raw AS lpb
		ON lr_proc.library_preparation_batch = lpb.id
	LEFT JOIN lr_long_read_library_preparation_b_output$raw AS psb
		ON psb.sanger_sample_id = sr.sanger_sample_id
	LEFT JOIN container$raw AS psbc
		ON psb.container = psbc.id
	LEFT JOIN lr_lib_prep_sample_status_check$raw AS lps
		ON lps.sanger_sample_id = sr.sanger_sample_id
	LEFT JOIN lr_lib_prep_sample_status_check_output AS lpsc
		ON lpsc.sanger_sample_id = sr.sanger_sample_id
)

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	tp.id AS tissue_prep_id,
	ssid.sanger_sample_id AS extraction_id,
	t.programme_id,
	t.specimen_id,
	ssid.sanger_sample_id,
	CASE 
		WHEN lr_lib.library_prep_receipt_date IS NOT NULL THEN 'LI'::varchar 
	ELSE NULL
	END AS library_type,
	lr_lib.library_batch_id,
	lr_lib.library_container_id,
	-- DATE(tpsub.submitted_submission_date) AS completion_date,
	lr_lib.library_prep_receipt_date,
	lr_lib.library_prep_completion_date,
	lr_lib.library_prep_qc_decision,
	'pacbio'::varchar AS sequencing_platform,
	'v2'::varchar AS source
FROM tissue_prep$raw AS tp
LEFT JOIN tissue$raw AS t
	ON tp.tissue = t.id
LEFT JOIN container_content$raw AS cc 
	ON tp.id = cc.entity_id
LEFT JOIN container$raw AS c 
	ON cc.container_id = c.id
LEFT JOIN tissue_prep_submission_workflow_output$raw AS tpsub
	ON c.id = tpsub.sample_tube_id
LEFT JOIN container$raw AS sub_con
	ON tpsub.sample_tube_id = sub_con.id
LEFT JOIN storage$raw AS stor 
	ON c.location_id = stor.id
LEFT JOIN sanger_sample_id$raw AS ssid 
	ON c.id = ssid.sample_tube
LEFT JOIN project$raw AS proj
	ON tp.project_id$ = proj.id
LEFT JOIN folder$raw AS f 
	ON tp.folder_id$ = f.id
-- LR information joins start here
LEFT JOIN dna_extract$raw AS dna
	ON dna.tissue_prep = tp.id
	AND dna.archived$ = false
	AND dna.project_id$ = 'src_REvgPRH1dy' -- the LR project ID
LEFT JOIN lr_long_read_dna_extraction_output$raw AS output
	ON dna.id = output.sample_id
LEFT JOIN lr_dna_extraction_sample_status_check$raw AS sc
	ON sc.sanger_sample_id = ssid.sanger_sample_id
LEFT JOIN lr_dna_extraction_sample_status_check_output$raw AS ssc
	ON ssc.sample_id = dna.id
LEFT JOIN lr_lib
	ON lr_lib.sanger_sample_id = ssid.sanger_sample_id
-- end of LR information joins
WHERE sub_con.id IS NOT NULL
	AND proj.name = 'ToL Core Lab'
	AND f.name = 'Sample Prep'
	AND tpsub.downstream_application IS DISTINCT FROM 'RNA'
