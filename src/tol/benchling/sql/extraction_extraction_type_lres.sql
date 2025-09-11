
/* 
SQL Query: LRES Submissions Benchling Warehouse

Output: Table with cols: 

1) sanger_sample_id
2) programme_id
3) specimen_id
4) fluidx_id: Fluidx ID of the tissue prep submitted. 
5) submission_type: Submission type code: PACBIO

NOTES: 

1) Data Model: Result Assays attached to container level.
2) All sample information is retrived using Benchling Storage. 
   By lab procedure, all LRES submission tubes are located at SciOps ToL Lab
   in Benchling Storage App.
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
	ssid.sanger_sample_id AS extraction_id,
	c.barcode AS fluidx_id,
	c.id AS fluidx_container_id,
	DATE(tpsub.submitted_submission_date) AS completion_date,
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
LEFT JOIN storage$raw AS stor 
	ON c.location_id = stor.id
LEFT JOIN sanger_sample_id$raw AS ssid 
	ON c.id = ssid.sample_tube
WHERE stor.name$ = 'SciOps ToL Lab'