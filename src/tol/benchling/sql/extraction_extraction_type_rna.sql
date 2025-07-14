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
6) extraction_id: [character] Primary key. 
7) programme_id: [character] ToLID. Origin: BWH
8) sts_id: [character] Specimen ID. Origin: STS
9) completion_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
10) extraction_name: [character] Entity name. 
11) fluidx_id: [character] Container barcode of the DNA fluidx tube. 
12) extraction_qc_result: [character] QC result: Yes = Extraction passed; No = Extraction failed. 
13) yield_ng: [double] DNA yield after extraction. 
14) volume_ul: [double] volume of DNA available in the fluidx tube.
15) location: [character] Physical locationo of the DNA extraction. Freezer shelf.
16) rack: [character] Physical locationo of the DNA extraction. Rack barcode.
17) bnt_id: [character] Batches and Tracking legacy id.
18) extraction_type: rna

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
	AND rna.extraction_protocol_deviation != 'PiMmS'
ORDER BY completion_date DESC;
