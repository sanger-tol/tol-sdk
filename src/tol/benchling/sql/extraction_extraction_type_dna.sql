/* 
## SQL Query: DNA extractions Benchling Warehouse (BWH)

This SQL query retrieves all the information of DNA extractions performed by the ToL Core Laboratory. 

The table produced also contains the eln_dna_extract_id and eln_file_registry_id which uniquely idenfied each dna extract entity in Benchling Warehouse (BWH). 

The eln_dna_extract_id should be used as the foreign key to the DNA extract entity the submission is derived from.

Vouchers are also included in the output table, and a unique extraction_id is created for each voucher by appending _voucher1, _voucher2, etc to the original extraction id.

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extractions is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extractions is derived from.
5) eln_file_registry_id: [character] id in Benchling Registry.
6) extraction_id: [character] Primary key. For each voucher, a unique id is created by appending _voucher1, _voucher2, etc to the original extraction id.
7) programme_id: [character] ToLID. Origin: BWH
8) specimen_id: [character] Specimen ID. Origin: STS
9) completion_date: [date] Extraction date. This field coalesces created_at$ and created_on fields. Created_on is for bnt legacy data.
10) extraction_name: [character] Entity name. 
11) fluidx_id: [character] Fluidx ID.
12) fluidx_container_id: [character] Fluidx container unique ID.
13) volume_ul: [double] volume of DNA available in the fluidx tube.
14) location: [character] Physical locationo of the DNA extraction. Freezer shelf.
15) rack: [character] Physical locationo of the DNA extraction. Rack barcode.
16) bnt_id: [character] Batches and Tracking legacy id.
17) manual_vs_automatic: [character].
18) extraction_protocol: [character] DNA extraction protocol as recorded at the time of extraction
19) tube_type: [character] Type of tube. Marked NULL or voucher.
20) extraction_type: [character] dna.
21) name: [character] Folder name.
22) archive_purpose: [character] Reason for archiving the DNA extraction.
23) nanodrop_concentration_ngul: [double] Concentration of DNA as measured by Nanodrop.
24) dna_260_280_ratio: [double] Ratio of absorbance at 260:280nm as measured by spectrophotometer.
25) dna_260_230_ratio: [double] Ratio of absorbance at 260:230nm as measured by spectrophotometer.
26) qubit_concentration_ngul: [double] Concentration of DNA as measured by Qubit.
27) yield_ng: [double] DNA yield after extraction.
28) femto_date_code: [character] Femto date code.
29) femto_description:[character] Categorical description of the femto pulse profile. 
30) gqn_index: [character] Genomic Quality Number (GQN) index, calculated by the Femto software.
31) next_step: [json] The next step decision made after evaluating the DNA quality.
32) extraction_qc_result: [character] QC result: Yes = Extraction passed; No = Extraction failed. 

NOTES: 
1) Data types were casted explicitly to conserved the data type stored in BWH.
2) To add the Fluidx ID of the original DNA extract a few filters were applied to delete archived tubes because they were made in error, and invalid container names.

*/

WITH latest_nanodrop_conc AS (    
    SELECT
        sample_id,
        nanodrop_concentration_ngul,
        _260_280_ratio AS "dna_260_280_ratio",
        _260_230_ratio AS "dna_260_230_ratio"
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY sample_id ORDER BY created_at$ DESC) AS rn
        FROM nanodrop_measurements_v2$raw
    ) ranked_nanod
    WHERE rn = 1
),

latest_qubit_conc AS (
    SELECT
        sample_id,
        qubit_concentration_ngul
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY sample_id ORDER BY created_at$ DESC) AS rn
        FROM qubit_measurements_v2$raw
    ) ranked_qubit
    WHERE rn = 1
),

latest_yield AS (
    SELECT
        sample_id,
        yield
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY sample_id ORDER BY created_at$ DESC) AS rn
        FROM yield_v2$raw
    ) ranker_yield
    WHERE rn = 1
),

latest_femto AS (
    SELECT
        sample_id,
        femto_date_code,
        femto_profile_description AS femto_description,
        gqn_dnaex
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY sample_id ORDER BY created_at$ DESC) AS rn
        FROM femto_dna_extract_v2$raw
    ) ranked_femto
    WHERE rn = 1
),

latest_decision_making AS (
    SELECT
        sample_id,
        next_step,
        qc_passfail AS extraction_qc_result
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY sample_id ORDER BY created_at$ DESC) AS rn
        FROM dna_decision_making_v2$raw
    ) ranked_dnad
    WHERE rn = 1
),

dna_extractions AS (
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
        con.barcode AS fluidx_id,
        con.id AS fluidx_container_id,
        CASE
            WHEN con.archive_purpose$ IN ('Retired', 'Expended') THEN 0 -- Retired or expended DNA extractions have a weight of 0
            ELSE con.volume_si * 1000000
        END AS volume_ul,
        loc.name AS location,
        box.barcode AS rack,
        dna.bt_id AS bnt_id,
        dna.manual_vs_automatic AS manual_vs_automatic,
        dna.extraction_protocol,
        tube.type AS tube_type,
        'dna'::varchar AS extraction_type,
        f.name,
        dna.archive_purpose$,
        latest_nanodrop_conc.nanodrop_concentration_ngul,
        latest_nanodrop_conc.dna_260_280_ratio,
        latest_nanodrop_conc.dna_260_230_ratio,
        latest_qubit_conc.qubit_concentration_ngul,
        latest_yield.yield AS yield_ng,
        latest_femto.femto_date_code,
        latest_femto.femto_description,
        latest_femto.gqn_dnaex AS gqn_index,
        latest_decision_making.next_step,
        latest_decision_making.extraction_qc_result
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
    LEFT JOIN folder$raw AS f
        ON dna.folder_id$ = f.id
    LEFT JOIN project$raw AS proj
        ON dna.project_id$ = proj.id
    LEFT JOIN latest_nanodrop_conc -- Results chunk
        ON dna.id = latest_nanodrop_conc.sample_id
    LEFT JOIN latest_qubit_conc
        ON dna.id = latest_qubit_conc.sample_id
    LEFT JOIN latest_yield
        ON dna.id = latest_yield.sample_id
    LEFT JOIN latest_femto
        ON dna.id = latest_femto.sample_id
    LEFT JOIN latest_decision_making
        ON dna.id = latest_decision_making.sample_id -- End Results chunk
    LEFT JOIN box$raw AS box -- Location chunk
        ON con.box_id = box.id
    LEFT JOIN location$raw AS loc
        ON loc.id = box.location_id -- End of location chunk
    WHERE proj.name = 'ToL Core Lab'
		AND tube.type IS NULL
        AND (f.name IN ('Routine Throughput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
        AND (dna.archive_purpose$ != ('Made in error') OR dna.archive_purpose$ IS NULL)
        AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
        AND con.barcode NOT LIKE 'CON%'
),

vouchers AS ( 
	SELECT DISTINCT
        t.sts_id,
        t.taxon_id,
        t.id AS eln_tissue_id,
        tp.id AS eln_tissue_prep_id,
        dna.file_registry_id$ AS eln_file_registry_id,
        -- Create unique extraction_id for vouchers
        CONCAT(dna.id, '_voucher', ROW_NUMBER() OVER (PARTITION BY dna.id ORDER BY con.id)) AS extraction_id,
        t.programme_id,
        t.specimen_id,
        COALESCE(DATE(dna.created_on), DATE(dna.created_at$)) AS completion_date, -- Homogenising BnT and Benchling dates
        dna.name$ AS extraction_name,
        con.barcode AS fluidx_id,
        con.id AS fluidx_container_id,
        CASE
            WHEN con.archive_purpose$ IN ('Retired', 'Expended') THEN 0 -- Retired or expended DNA extractions have a weight of 0
            ELSE con.volume_si * 1000000
        END AS volume_ul,
        loc.name AS location,
        box.barcode AS rack,
        dna.bt_id AS bnt_id,
        dna.manual_vs_automatic AS manual_vs_automatic,
        dna.extraction_protocol,
        tube.type AS tube_type,
        'dna'::varchar AS extraction_type,
        f.name,
        dna.archive_purpose$,
        NULL::double precision AS nanodrop_concentration_ngul,
        NULL::double precision AS dna_260_280_ratio,
        NULL::double precision AS dna_260_230_ratio,
        latest_qubit_conc.qubit_concentration_ngul,
        NULL::double precision AS yield_ng,
        NULL::varchar AS femto_date_code,
        NULL::jsonb AS femto_description,
        NULL::double precision AS gqn_index,
        NULL::jsonb AS next_step,
        NULL::varchar AS extraction_qc_result
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
    LEFT JOIN folder$raw AS f
        ON dna.folder_id$ = f.id
    LEFT JOIN project$raw AS proj
        ON dna.project_id$ = proj.id
    LEFT JOIN box$raw AS box -- Location chunk
        ON con.box_id = box.id
    LEFT JOIN location$raw AS loc
        ON loc.id = box.location_id -- End of location chunk
    LEFT JOIN latest_qubit_conc -- Results chunk
        ON dna.id = latest_qubit_conc.sample_id -- End of results chunk
    WHERE proj.name = 'ToL Core Lab'
		AND tube.type = 'voucher'
        AND (f.name IN ('Routine Throughput', 'DNA', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
        AND (dna.archive_purpose$ != ('Made in error') OR dna.archive_purpose$ IS NULL)
        AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
        AND con.barcode NOT LIKE 'CON%'
    ),

combined_results AS (
    SELECT * FROM dna_extractions
    UNION ALL
    SELECT * FROM vouchers
)

SELECT * FROM combined_results
ORDER BY extraction_id;
