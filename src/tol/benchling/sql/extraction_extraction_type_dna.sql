/* 
## SQL Query: DNA extractions Benchling Warehouse (BWH)

This SQL query retrieves all the information of DNA extractions performed by the ToL Core Laboratory. 

The table produced also contains the eln_dna_extract_id and eln_file_registry_id which uniquely idenfied each dna extract entity in Benchling Warehouse (BWH). 

The eln_dna_extract_id should be used as the foreign key to the DNA extract entity the submission is derived from.

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extraction is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extraction is derived from.
5) eln_file_registry_id: [character] id in Benchling Registry.
6) extraction_id: [character] Primary key. 
7) programme_id: [character] ToLID. Origin: BWH
8) specimen_id: [character] Specimen ID. Origin: STS
9) completion_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
10) extraction_name: [character] Entity name.
11) bnt_id: [character] Batches and Tracking legacy id.
12) manual_vs_automatic: [character] Extraction method indicator.
13) extraction_protocol: [character] DNA extraction protocol as recorded at the time of extraction.
14) extraction_type: [character] Type of extraction, set to 'dna'.
15) folder_name: [character] Folder name.
16) archive_purpose: [character] Reason for archiving the DNA extraction.

NOTES: 
1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to delete Vouchers, tubes archived because they were made in error, and invalid container names.

*/

SELECT DISTINCT
    t.sts_id,
    t.taxon_id,
    t.id AS eln_tissue_id,
    tp.id AS eln_tissue_prep_id,
    dna.file_registry_id$ AS eln_file_registry_id,
    dna.id AS extraction_id,
    t.programme_id,
    t.specimen_id,
    COALESCE(DATE(dna.created_on), DATE(dna.created_at$)) AS completion_date, -- Homogenising BnT and Benchling dates
    dna.name$ AS extraction_name,
    dna.bt_id AS bnt_id,
    dna.manual_vs_automatic AS manual_vs_automatic,
    dna.extraction_protocol,
    'dna'::varchar AS extraction_type,
    f.name AS folder_name
FROM dna_extract$raw AS dna
LEFT JOIN tissue_prep$raw AS tp
     ON tp.id = dna.tissue_prep
LEFT JOIN tissue$raw AS t
     ON t.id = tp.tissue
LEFT JOIN folder$raw AS f
     ON dna.folder_id$ = f.id
LEFT JOIN project$raw AS proj
    ON dna.project_id$ = proj.id
LEFT JOIN registration_origin$raw AS reg
	ON reg.entity_id = dna.id
LEFT JOIN entry$raw AS ent
	ON reg.origin_entry_id = ent.id
WHERE proj.name = 'ToL Core Lab'
    AND  (f.name IN ('Routine Throughput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
    AND (dna.archive_purpose$ != ('Made in error') OR dna.archive_purpose$ IS NULL)
    AND ent.name NOT LIKE '%Nuclei isolation and tagmentation%'
ORDER BY completion_date DESC
