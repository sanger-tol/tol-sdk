/* 
## SQL Query: Pooled DNA extractions Benchling Warehouse (BWH)

This SQL query retrieves all the information of pooled DNA extractions performed by the ToL Core Laboratory. 

The table produced also contains the eln_pooled_sample_id and eln_file_registry_id 
which uniquely idenfied each dna extract entity in Benchling Warehouse (BWH). 

The eln_pooled_sample_id should be used as the foreign key to the DNA extract entity to the
submission it is derived from.

The source_dna_extract_id contains a list of ids of the dna extract entities that were pooled. This is a jsob data type. 

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extractions is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extractions is derived from.
5) eln_file_registry_id: [character] id in Benchling Registry.
6) eln_pooled_sample_id: [character] Primary key. 
7) tolid: [character] Container barcode of the DNA fluidx tube. 
8) dnapool_extraction_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
9) eln_dnapool_extract_name: [character] Entity name. 
10) dnapool_fluidx_id: [character] Container barcode of the DNA fluidx tube. 
11) extractin_protocol: [character] Extraction protocol. 
12) dnapool_qc_passfail: [character] outcome of QC assessment duting decision making: pass=yes or fail=no.
13) dnapool_next_step: [jsonb] decision taken after extraction. 
14) dnapool_nanodrop_ngul: [double precision] nanodrop concentration in ng/ul.
15) dnapool_260_280_ratio: [double precision] nanodrop 260/280 ratio.
16) dnapool_260_230_ratio: [double precision] nanodrop 260/230 ratio.
17) dnapool_qubit_ngul: [double precision] qubit concentration in ng/ul.
18) dnapool_gqn: [double precision] GQN index.
19) dnapool_yield: [double precision] yield.
20) dnapool_femto_profile_description: [jsonb] Qualitative description of femto profiles.
21) source_dna_extracts: [jsonb] List of ids for pooled dna extracts.

NOTES: 

1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to
delete Vouchers, tubes archived because they were made in error, and 
invalid container names. 
3) Vouchers: The volume filter is risky but necessary. A few container might be excluded. 
4) This query follows only Benchling Data Model version 2: Results attached to the entity.
5) Tissue metadata is retrieved using the first dna extract listed in source_dna_extract_id
as a link to the tissue prep and tissue entities. 

*/

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	dnap.file_registry_id$ AS eln_file_registry_id,
	dnap.id AS eln_pooled_sample_id,
	t.tolid,
	DATE(dnap.created_at$) AS dnapool_extraction_date, -- Homogenising BnT and Benchling dates
	dnap.name$ AS eln_dnapool_extract_name,
	con.barcode AS dnapool_fluidx_id,
	source_dna.manual_vs_automatic AS extraction_type,
	source_dna.protocol_computed ->> 0 AS extraction_protocol,
	dnadc.qc_passfail AS dnapool_qc_passfail,
	dnadc.next_step AS dnapool_next_step,
	nanod.nanodrop_concentration_ngul AS dnapool_nanodrop_ngul,
	nanod._260_280_ratio AS dnapool_260_280_ratio,
	nanod._260_230_ratio AS dnapool_260_230_ratio,
	qbit.qubit_concentration_ngul AS dnapool_qubit_ngul,
	femto.gqn_dnaex AS dnapool_gqn,
	dnay.yield AS dnapool_yield,
	femto.femto_profile_description AS dnapool_femto_description,
	dnap.samples AS source_dna_extract_id,
	'pooled_dna'::varchar AS extraction_type
FROM pooled_samples$raw AS dnap
LEFT JOIN container_content$raw AS cc 
	ON cc.entity_id = dnap.id
LEFT JOIN container$raw AS con 
	ON con.id = cc.container_id
LEFT JOIN dna_decision_making_v2$raw AS dnadc 
	ON dnap.id = dnadc.sample_id
LEFT JOIN nanodrop_measurements_v2$raw AS nanod 
	ON dnap.id = nanod.sample_id
LEFT JOIN qubit_measurements_v2$raw AS qbit 
	ON dnap.id = qbit.sample_id
LEFT JOIN femto_dna_extract_v2$raw AS femto 
	ON dnap.id = femto.sample_id
LEFT JOIN yield_v2$raw AS dnay 
	ON dnap.id = dnay.sample_id
LEFT JOIN dna_extract$raw AS source_dna
	ON dnap.samples ->> 0 = source_dna.id -- Chunk: Using first pooled dna extract to link tissue metadata
LEFT JOIN tissue_prep$raw AS tp 
	ON tp.id = source_dna.tissue_prep
LEFT JOIN tissue$raw AS t 
	ON t.id = tp.tissue -- End of Chunk: Using first pooled dna extract to link tissue metadata
LEFT JOIN tube$raw AS tube 
	ON cc.container_id = tube.id 
LEFT JOIN folder$raw AS f 
	ON dnap.folder_id$ = f.id
WHERE tube.type IS NULL -- Excluding vouchers
	AND con.volume_si * 1000000 != 10
	AND (f.name IN ('Routine Throughput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
	AND (dnap.archive_purpose$ != ('Made in error') OR dnap.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
	AND con.barcode NOT LIKE 'CON%'
ORDER BY dnapool_extraction_date DESC;