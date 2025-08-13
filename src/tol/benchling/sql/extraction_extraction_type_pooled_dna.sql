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
6) extraction_id: [character] Primary key. 
7) programme_id: [character] ToLID. Origin: BWH
8) specimen_id: [character] Specimen ID. Origin: STS
9) completion_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
10) extraction_name: [character] Entity name. 
11) fluidx_id: [character] Container barcode of the DNA fluidx tube. 
12) extraction_qc_result: [character] QC result: Yes = Extraction passed; No = Extraction failed. 
13) yield_ng: [double] DNA yield after extraction. 
14) femto_description:[character] Categorical description of the femto pulse profile. 
15) volume_ul: [double] volume of DNA available in the fluidx tube.
16) tube_type: [character] Type of tube. Marked NULL or voucher.
17) location: [character] Physical locationo of the DNA extraction. Freezer shelf.
18) rack: [character] Physical locationo of the DNA extraction. Rack barcode.
19) source_extractions_id: [jsonb] List of ids for pooled dna extracts.
20) extraction_type: [character] pooled_dna.

NOTES: 

1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to
delete Vouchers, tubes archived because they were made in error, and 
invalid container names.
3) Tissue metadata is retrieved using the first dna extract listed in source_dna_extract_id
as a link to the tissue prep and tissue entities. 

*/

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	dnap.file_registry_id$ AS eln_file_registry_id,
	dnap.id AS extraction_id,
	t.programme_id,
	t.specimen_id,
	DATE(dnap.created_at$) AS completion_date, -- Homogenising BnT and Benchling dates
	dnap.name$ AS extraction_name,
	con.barcode AS fluidx_id,
	con.id AS fluidx_container_id,
	dnadc.qc_passfail AS extraction_qc_result,
	dnay.yield AS yield_ng,
	femto.femto_profile_description AS femto_description,
	con.volume_si * 1000000 AS volume_ul,
	tube.type AS tube_type,
	loc.name AS location,
	box.barcode AS rack, 
	dnap.samples AS source_extractions_id,
	'pooled_dna'::varchar AS extraction_type
FROM pooled_samples$raw AS dnap
LEFT JOIN container_content$raw AS cc 
	ON cc.entity_id = dnap.id
LEFT JOIN container$raw AS con 
	ON con.id = cc.container_id
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
LEFT JOIN dna_decision_making_v2$raw AS dnadc  -- Results chunk
	ON dnap.id = dnadc.sample_id
LEFT JOIN femto_dna_extract_v2$raw AS femto 
	ON dnap.id = femto.sample_id
LEFT JOIN yield_v2$raw AS dnay 
	ON dnap.id = dnay.sample_id -- End Results chunk
LEFT JOIN box$raw AS box -- Location chunk
	ON con.box_id = box.id 
LEFT JOIN location$raw AS loc
	ON loc.id = box.location_id -- End of location chunk
WHERE (f.name IN ('Routine Throughput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
	AND (dnap.archive_purpose$ != ('Made in error') OR dnap.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
	AND con.barcode NOT LIKE 'CON%'
ORDER BY completion_date DESC;