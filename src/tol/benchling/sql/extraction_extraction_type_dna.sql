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
6) extraction_id: [character] Primary key. 
7) programme_id: [character] ToLID. Origin: BWH
8) completion_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
9) extraction_name: [character] Entity name. 
10) extraction_qc_result: [character] QC result: Yes = Extraction passed; No = Extraction failed. 
11) yield_ng: [double] DNA yield after extraction. 
12) femto_description:[character] Categorical description of the femto pulse profile. 
13) volume_ul: [double] volume of DNA available in the fluidx tube.
14) shelf: [character] Physical locationo of the DNA extraction. Freezer shelf.
15) rack: [character] Physical locationo of the DNA extraction. Rack barcode.
16) bnt_id: [character] Batches and Tracking legacy id.
17) extraction_type: [character] dna

NOTES: 

1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to
delete Vouchers, tubes archived because they were made in error, and 
invalid container names. 
3) Vouchers: The volume filter is risky but necessary. A few container might be excluded. 

*/

SELECT DISTINCT
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	dna.file_registry_id$ AS eln_file_registry_id,
	dna.id AS extraction_id,
	t.programme_id,
	COALESCE(DATE(dna.created_on), DATE(dna.created_at$)) AS completion_date, -- Homogenising BnT and Benchling dates
	dna.name$ AS extraction_name,
	con.barcode AS fluidx_id,
	dnadc.qc_passfail AS extraction_qc_result,
	dnay.yield AS yield_ng,
	femto.femto_profile_description AS femto_description,
	con.volume_si * 1000000 AS volume_ul,
	loc.name AS shelf, 
	box.barcode AS rack,
	dna.bt_id AS bnt_id,
	'dna'::varchar AS extraction_type, f.name, dna.archive_purpose$
FROM dna_extract$raw AS dna
LEFT JOIN container_content$raw AS cc 
	ON cc.entity_id = dna.id
LEFT JOIN container$raw AS con 
	ON con.id = cc.container_id
LEFT JOIN tissue_prep$raw AS tp 
	ON tp.id = dna.tissue_prep
LEFT JOIN tissue$raw AS t 
	ON t.id = tp.tissue
LEFT JOIN tube$raw AS tube 
	ON cc.container_id = tube.id 
LEFT JOIN folder AS f 
	ON dna.folder_id$ = f.id
LEFT JOIN project$raw AS proj
	ON dna.project_id$ = proj.id
LEFT JOIN dna_decision_making_v2$raw AS dnadc  -- Results chunk
	ON dna.id = dnadc.sample_id
LEFT JOIN femto_dna_extract_v2$raw AS femto 
	ON dna.id = femto.sample_id
LEFT JOIN yield_v2$raw AS dnay 
	ON dna.id = dnay.sample_id -- End Results chunk
LEFT JOIN box$raw AS box -- Location chunk
	ON con.box_id = box.id 
LEFT JOIN location$raw AS loc
	ON loc.id = box.location_id -- End of location chunk
WHERE tube.type IS NULL -- Excluding vouchers
	AND con.volume_si * 1000000 != 10
	AND proj.name = 'ToL Core Lab'
	AND f.name IN ('Routine Throuput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move', 'R&D', 'ToL Core Restricted Entities')
	AND (dna.archive_purpose$ != ('Made in error') OR dna.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
	AND con.barcode NOT LIKE 'CON%'
ORDER BY completion_date DESC

