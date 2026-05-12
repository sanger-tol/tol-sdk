/* 
## SQL Query: RNA extractions Benchling Warehouse (BWH)

This SQL query retrieves all the information of RNA extractions performed by the ToL Core Laboratory. 

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extraction is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extraction is derived from.
5) extraction_id: [character] Primary key for extraction records; in RNA request rows this is the Sanger sample id.
6) programme_id: [character] ToLID. Origin: BWH
7) specimen_id: [character] Specimen ID. Origin: STS
8) completion_date: [date] RNA extraction or RNA request completion date.
9) extraction_name: [character] Entity name (NULL for RNA request rows).
10) fluidx_id: [character] Container barcode of the RNA FluidX tube.
11) fluidx_container_id: [character] Benchling id of the RNA FluidX container.
12) rna_qc_passfail: [character] RNA QC result from rna_extract_and_qc2 (NULL for RNA request rows).
13) rna_yield: [double] RNA yield.
14) volume_ul: [double] Volume available in the FluidX tube in microlitres.
15) location: [character] Physical location of the RNA extraction/request tube (freezer shelf/location).
16) rack: [character] Physical location of the RNA extraction/request tube (rack barcode).
17) bnt_id: [character] Batches and Tracking legacy id.
18) eln_tissue_prep_name: [character] Tissue prep entity name (NULL for extraction rows).
19) sanger_sample_id: [character] Sanger sample id (present for RNA request rows).
20) extraction_type: [character] Constant value: rna.

NOTES: 

1) The query explicitly excludes wells as containers to avoid having duplicated rows without qc_passfail and next steps results. 
   All the information is correctly displayed for tubes.  
2) This query follows only Benchling Data Model version 2: Results attached to the entity.

*/

WITH rna_extractions AS (
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		t.id AS eln_tissue_id,
		tp.id AS eln_tissue_prep_id,
		rna.id AS extraction_id,
		t.programme_id,
		t.specimen_id,
		COALESCE(DATE(rna.created_on), DATE(rna.created_at$)) AS completion_date, -- Homogenising BnT and Benchling dates
		rna.name$ AS extraction_name,
		con.barcode AS fluidx_id,
		con.id AS fluidx_container_id,
		rnadc.qc_passfail AS rna_qc_passfail,
		rnay.yield AS rna_yield,
		CASE
			WHEN con.archive_purpose$ IN ('Retired', 'Expended') THEN 0 -- Retired or expended RNA extractions have a weight of 0
			ELSE con.volume_si * 1000000
		END AS volume_ul,
		loc.name AS location,
		box.barcode AS rack,
		rna.bt_id AS bnt_id,
		NULL::varchar AS eln_tissue_prep_name,
		NULL::varchar AS sanger_sample_id,
		'rna'::varchar AS extraction_type
	FROM rna_extract$raw AS rna
	LEFT JOIN container_content$raw AS cc 
		ON cc.entity_id = rna.id
	LEFT JOIN container$raw AS con 
		ON con.id = cc.container_id
	LEFT JOIN rna_extract_and_qc2$raw AS rnadc 
		ON con.id = rnadc.rna_extract_tube_id
	LEFT JOIN tissue_prep$raw AS tp 
		ON tp.id = rna.tissue_prep
	LEFT JOIN tissue$raw AS t 
		ON t.id = tp.tissue
	LEFT JOIN tube$raw AS tube 
		ON cc.container_id = tube.id 
	LEFT JOIN folder$raw AS f 
		ON rna.folder_id$ = f.id
	LEFT JOIN project$raw AS proj
		ON rna.project_id$ = proj.id
	LEFT JOIN yield_v2$raw AS rnay 
		ON rna.id = rnay.sample_id 
	LEFT JOIN box$raw AS box -- Location chunk
		ON con.box_id = box.id 
	LEFT JOIN location$raw AS loc
		ON loc.id = box.location_id -- End of location chunk
	WHERE tube.type IS NULL -- Excluding vouchers
		AND proj.name = 'ToL Core Lab'
		AND f.name IN ('Routine Throughput', 'RNA', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D', 'ToL Core Restricted Entities')
		AND (rna.archive_purpose$ != ('Made in error') OR rna.archive_purpose$ IS NULL)
		AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
		AND con.plate_id IS NULL -- Delete well rows.
		AND rna.extraction_protocol_deviation IS DISTINCT FROM 'PiMmS'
	ORDER BY completion_date DESC
),

rna_requests AS (
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		t.id AS eln_tissue_id,
		tp.id AS eln_tissue_prep_id,
		ssid.sanger_sample_id AS extraction_id,
		t.programme_id,
		t.specimen_id,
		DATE(tpsub.submitted_submission_date) AS completion_date,
		NULL::varchar AS extraction_name,
		sub_con.barcode AS fluidx_id,
		sub_con.id AS fluidx_container_id,
		NULL::varchar AS rna_qc_passfail,
		NULL::float8 AS rna_yield,
		NULL::float8 AS volume_ul,
		loc.name AS location,
		box.barcode AS rack,
		tp.bt_id AS bnt_id,
		ssid.sanger_sample_id,
		'rna'::varchar AS extraction_type,
		tp.name$ AS eln_tissue_prep_name
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
	LEFT JOIN box$raw AS box -- Location chunk
		ON sub_con.box_id = box.id 
	LEFT JOIN location$raw AS loc
		ON loc.id = box.location_id -- End of location chunk
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON c.id = ssid.sample_tube
	LEFT JOIN project$raw AS proj
		ON tp.project_id$ = proj.id
	LEFT JOIN folder$raw AS f 
		ON tp.folder_id$ = f.id
	WHERE sub_con.id IS NOT NULL
		AND proj.name = 'ToL Core Lab'
		AND f.name = 'Sample Prep'
		AND tpsub.downstream_application = 'RNA'
)

SELECT *
FROM rna_extractions
UNION
SELECT *
FROM rna_requests
