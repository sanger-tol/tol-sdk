/* 
## SQL Query: DNA extractions Benchling Warehouse (BWH)

This SQL query retrieves all the information of DNA extractions performed by the ToL Core Laboratory. 

The table produced also contains the eln_dna_extract_id and eln_file_registry_id 
which uniquely idenfied each dna extract entity in Benchling Warehouse (BWH). 

The eln_dna_extract_id should be used as the foreign key to the DNA extract entity the
submission is derived from.

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extractions is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extractions is derived from.
5) eln_file_registry_id: [character] id in Benchling Registry.
6) eln_dna_extract_id: [character] Primary key. 
7) tolid: [character] Container barcode of the DNA fluidx tube. 
8) dna_extraction_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
9) eln_dna_extract_name: [character] Entity name. 
10) dna_fluidx_id: [character] Container barcode of the DNA fluidx tube. 
11) extractin_protocol: [character] Extraction protocol. 
12) dna_qc_passfail: [character] outcome of QC assessment duting decision making: pass=yes or fail=no.
13) dna_next_step: [jsonb] decision taken after extraction. 
14) dna_nanodrop_ngul: [double precision] nanodrop concentration in ng/ul.
15) dna_260_280_ratio: [double precision] nanodrop 260/280 ratio.
16) dna_260_230_ratio: [double precision] nanodrop 260/230 ratio.
17) dna_qubit_ngul: [double precision] qubit concentration in ng/ul.
18) dna_gqn: [double precision] GQN index.
19) dna_yield: [double precision] yield.
20) dna_femto_profile_description: [jsonb] Qualitative description of femto profiles.
21) dna_bnt_id: [character] Batches and Tracking legacy id.
22) extraction_type: [character] dna

NOTES: 

1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to
delete Vouchers, tubes archived because they were made in error, and 
invalid container names. 
3) Vouchers: The volume filter is risky but necessary. A few container might be excluded. 
4) This query follows only Benchling Data Model version 2: Results attached to the entity.

*/

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	dna.file_registry_id$ AS eln_file_registry_id,
	dna.id AS eln_dna_extract_id,
	t.tolid,
	COALESCE(DATE(dna.created_on), DATE(dna.created_at$)) AS dna_extraction_date, -- Homogenising BnT and Benchling dates
	dna.name$ AS eln_dna_extract_name,
	con.barcode AS dna_fluidx_id,
	dna.manual_vs_automatic AS extraction_type,
	dna.protocol_computed ->> 0 AS extraction_protocol,
	dnadc.qc_passfail AS dna_qc_passfail,
	dnadc.next_step AS dna_next_step,
	nanod.nanodrop_concentration_ngul AS dna_nanodrop_ngul,
	nanod._260_280_ratio AS dna_260_280_ratio,
	nanod._260_230_ratio AS dna_260_230_ratio,
	qbit.qubit_concentration_ngul AS dna_qubit_ngul,
	femto.gqn_dnaex AS dna_gqn,
	dnay.yield AS dna_yield,
	femto.femto_profile_description AS dna_femto_description,
	dna.bt_id AS dna_bnt_id,
	'dna'::varchar AS extraction_type
FROM dna_extract$raw AS dna
LEFT JOIN container_content$raw AS cc 
	ON cc.entity_id = dna.id
LEFT JOIN container$raw AS con 
	ON con.id = cc.container_id
LEFT JOIN dna_decision_making_v2$raw AS dnadc 
	ON dna.id = dnadc.sample_id
LEFT JOIN nanodrop_measurements_v2$raw AS nanod 
	ON dna.id = nanod.sample_id
LEFT JOIN qubit_measurements_v2$raw AS qbit 
	ON dna.id = qbit.sample_id
LEFT JOIN femto_dna_extract_v2$raw AS femto 
	ON dna.id = femto.sample_id
LEFT JOIN yield_v2$raw AS dnay 
	ON dna.id = dnay.sample_id
LEFT JOIN tissue_prep$raw AS tp 
	ON tp.id = dna.tissue_prep
LEFT JOIN tissue$raw AS t 
	ON t.id = tp.tissue
LEFT JOIN tube$raw AS tube 
	ON cc.container_id = tube.id 
LEFT JOIN folder£raw AS f 
	ON dna.folder_id$ = f.id
WHERE tube.type IS NULL -- Excluding vouchers
	AND con.volume_si * 1000000 != 10
	AND (f.name IN ('Routine Throughput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
	AND (dna.archive_purpose$ != ('Made in error') OR dna.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
	AND con.barcode NOT LIKE 'CON%'
ORDER BY dna_extraction_date DESC;

