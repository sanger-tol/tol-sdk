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
8) rna_extraction_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
9) eln_rna_extract_name: [character] Entity name. 
10) rna_fluidx_id: [character] Container barcode of the DNA fluidx tube. 
11) extraction_protocol: [character] Extraction protocol. 
12) rna_qc_passfail: [character] outcome of QC assessment duting decision making: pass=yes or fail=no.
13) rna_next_step: [jsonb] decision taken after extraction. 
14) rna_nanodrop_ngul: [double precision] nanodrop concentration in ng/ul.
15) rna_260_280_ratio: [double precision] nanodrop 260/280 ratio.
16) rna_260_230_ratio: [double precision] nanodrop 260/230 ratio.
17) rna_qubit_ngul: [double precision] qubit concentration in ng/ul.
18) rna_yield: [double precision] yield.
19) rna_bnt_id: [character] Batches and Tracking legacy id.
20) extraction_type: rna

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
	COALESCE(DATE(rna.created_on), DATE(rna.created_at$)) AS rna_extraction_date, -- Homogenising BnT and Benchling dates
	rna.name$ AS eln_rna_extract_name,
	con.barcode AS rna_fluidx_id,
	rna.extraction_protocol_deviation AS extraction_protocol,
	rnadc.qc_passfail AS rna_qc_passfail,
	rnadc.next_step AS rna_next_step,
	nanod.nanodrop_concentration_ngul AS rna_nanodrop_ngul,
	nanod._260_280_ratio AS rna_260_280_ratio,
	nanod._260_230_ratio AS rna_260_230_ratio,
	qbit.qubit_concentration_ngul AS rna_qubit_ngul,
	rnay.yield AS rna_yield,
	rna.bt_id AS rna_bnt_id,
	'rna'::varchar AS extraction_type
FROM rna_sample$raw AS rna
LEFT JOIN container_content$raw AS cc 
	ON cc.entity_id = rna.id
LEFT JOIN container$raw AS con 
	ON con.id = cc.container_id
LEFT JOIN rna_extract_and_qc2$raw AS rnadc 
	ON con.id = rnadc.rna_extract_tube_id
LEFT JOIN nanodrop_measurements_v2$raw AS nanod 
	ON rna.id = nanod.sample_id
LEFT JOIN qubit_measurements_v2$raw AS qbit 
	ON rna.id = qbit.sample_id
LEFT JOIN yield_v2$raw AS rnay 
	ON rna.id = rnay.sample_id
LEFT JOIN tissue_prep$raw AS tp 
	ON tp.id = rna.tissue_prep
LEFT JOIN tissue$raw AS t 
	ON t.id = tp.tissue
LEFT JOIN tube$raw AS tube 
	ON cc.container_id = tube.id 
LEFT JOIN folder$raw AS f 
	ON rna.folder_id$ = f.id
WHERE tube.type IS NULL -- Excluding vouchers
	AND (f.name IN ('Routine Throughput', 'RNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
	AND (rna.archive_purpose$ != ('Made in error') OR rna.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
	AND con.plate_id IS NULL -- Delete well rows.
ORDER BY rna_extraction_date DESC;
