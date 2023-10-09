/* 
## SQL Query: RNA extractions Benchling Warehouse (BWH)

This SQL query retrieves all the information of RNA extractions performed by the ToL Core Laboratory. 

The table produced also contains the eln_rna_extract_id and eln_file_registry_id 
which uniquely idenfied each rna extract entity in Benchling Warehouse (BWH). 

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extractions is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extractions is derived from.
5) eln_file_registry_id: [character] id in Benchling Registry.
6) eln_rna_extract_id: [character] Primary key. 
7) tolid: [character] Container barcode of the DNA fluidx tube. 
8) completion_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
9) eln_rna_extract_name: [character] Entity name. 
10) rna_fluidx_id: [character] Container barcode of the DNA fluidx tube. 
11) rna_bnt_id: [character] Batches and Tracking legacy id.
12) extraction_type: rna

NOTES: 

1) The query explicitly excludes wells as containers to avoid having duplicated rows without qc_passfail and next steps results. 
   All the information is correctly displayed for tubes.  
2) This query follows only Benchling Data Model version 2: Results attached to the entity.

*/

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	rna.file_registry_id$ AS eln_file_registry_id,
	rna.id AS eln_rna_extract_id,
	t.tolid,
	COALESCE(DATE(rna.created_on), DATE(rna.created_at$)) AS completion_date, -- Homogenising BnT and Benchling dates
	rna.name$ AS eln_rna_extract_name,
	con.barcode AS rna_fluidx_id,
	con.barcode AS primary_identifier,
	rna.bt_id AS rna_bnt_id,
	'rna'::varchar AS extraction_type
FROM rna_sample$raw AS rna
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
LEFT JOIN folder AS f 
	ON rna.folder_id$ = f.id
WHERE tube.type IS NULL -- Excluding vouchers
	AND (f.name IN ('Routine Throuput', 'RNA', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D') OR f.name IS NULL)
	AND (rna.archive_purpose$ != ('Made in error') OR rna.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
	AND con.barcode NOT LIKE '%P%' -- Delete well rows.
ORDER BY completion_date DESC;
