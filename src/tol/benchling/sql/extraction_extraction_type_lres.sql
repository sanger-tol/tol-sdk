/* 
SQL Query: LRES Submissions Benchling Warehouse

Output: Table with cols: 

1) sanger_sample_id: Sanger sample identifier
2) extraction_id: Extraction identifier of the LR entity created
3) fluidx_id: Fluidx ID of the submitted tissue prep container
4) completion_date: Date the submission was completed
5) next_step: LRES, Small Arthropod MagAttract, or RNA for Core Lab.
6) extraction_type: Type of extraction (lres)

NOTES: 

1) Data Model: Result Assays attached to container level.
2) All sample information is retrived using Benchling Storage. 
*/

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	t.programme_id,
	t.specimen_id,
	tp.name$ AS eln_tissue_prep_name,
	ssid.sanger_sample_id,
	dna.id AS extraction_id,
	sub_con.barcode AS fluidx_id,
	sub_con.id AS fluidx_container_id,
	DATE(tpsub.submitted_submission_date) AS completion_date,
	DATE(dna.created_at$) AS lres_extraction_date, -- new column
	dna.name$ AS extraction_name,
-- 	AS manual_vs_automatic,
	dna.extraction_protocol AS extraction_protocol,
	CASE
		WHEN ssc.final_sample_decision IS NOT NULL
			THEN ssc.final_sample_decision
		ELSE output.decision
	END AS next_step,
	CASE 
		WHEN ssc.final_sample_decision IN ('Submit to Library Prep', 'Submit to ULI')
			THEN 'Yes'
		WHEN ssc.final_sample_decision IN ('Fail')
			THEN 'No'
		WHEN output.decision IN ('Submit to Library Prep', 'On Hold for ULI', 'Pass')
			THEN 'Yes'
		WHEN output.decision = 'On Review'
			THEN NULL
		ELSE NULL
	END AS extraction_qc_result,
	'lres'::varchar AS extraction_type
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
LEFT JOIN lr_dna_extraction_sample_status_check_output$raw AS ssc
	ON ssc.sample_id = dna.id
WHERE sub_con.id IS NOT NULL
	AND proj.name = 'ToL Core Lab'
	AND f.name = 'Sample Prep'
	AND tpsub.downstream_application IS DISTINCT FROM 'RNA'
