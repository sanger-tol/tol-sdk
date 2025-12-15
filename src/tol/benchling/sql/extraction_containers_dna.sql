/* 
## SQL Query: DNA Extraction Containers (Benchling Warehouse)

This SQL query retrieves detailed information about DNA extraction containers managed by the ToL Core Laboratory, including metadata, container details, and the latest QC measurements.

The resulting table includes identifiers for tissues, tissue preps, extractions, containers, and locations, as well as the most recent QC results (Nanodrop, Qubit, Femto, Yield, and Decision Making).

Output: Table with columns:

1) taxon_id: [character] Tissue metadata. Origin: STS
2) eln_tissue_id: [character] Benchling ID for the tissue the extraction is derived from.
3) eln_tissue_prep_id: [character] Benchling ID for the tissue prep the extraction is derived from.
4) extraction_id: [character] DNA extraction entity ID (Benchling).
5) programme_id: [character] ToLID. Origin: BWH.
6) specimen_id: [character] Specimen ID. Origin: STS.
7) creation_date: [date] Date the container was created.
8) fluidx_container_id: [character] Primary key for the FluidX container.
9) fluidx_id: [character] FluidX barcode.
10) tube_type: [character] Type of tube/container.
11) volume_ul: [numeric] Volume in microliters (0 if archived as 'Retired' or 'Expended').
12) location: [character] Storage location name.
13) rack: [character] Box/rack barcode.
14) archive_purpose: [character] Reason for archiving the DNA extraction.
15) nanodrop_concentration_ngul: [numeric] Latest Nanodrop concentration (ng/µL).
16) dna_260_280_ratio: [numeric] Latest Nanodrop 260/280 ratio.
17) dna_260_230_ratio: [numeric] Latest Nanodrop 260/230 ratio.
18) qubit_concentration_ngul: [numeric] Latest Qubit concentration (ng/µL).
19) yield_ng: [numeric] Latest yield (ng).
20) femto_date_code: [character] Latest Femto date code.
21) femto_description: [character] Latest Femto profile description.
22) gqn_index: [numeric] Latest GQN index from Femto.
23) next_step: [character] Latest decision making next step.
24) extraction_qc_result: [character] Latest extraction QC result.

NOTES:
1) Only extractions from the 'ToL Core Lab' project and relevant folders are included.
2) Containers archived as 'Made in error' or with names matching '%Nuclei isolation and tagmentation%' are excluded.
3) Latest QC results are joined from their respective measurement tables.
4) Volume is set to 0 for archived/expended extractions.
5) Data types are preserved as in the Benchling Warehouse.

*/

WITH latest_nanodrop_conc AS (    
    SELECT
        nanod.sample_id,
        nanod.nanodrop_concentration_ngul,
        nanod._260_280_ratio AS "dna_260_280_ratio",
        nanod._260_230_ratio AS "dna_260_230_ratio"
    FROM nanodrop_measurements_v2$raw AS nanod
    WHERE nanod.created_at$ = (        
        SELECT MAX(sub.created_at$)
        FROM nanodrop_measurements_v2$raw AS sub
        WHERE sub.sample_id = nanod.sample_id
    )
),

latest_qubit_conc AS (
    SELECT
        qbit.sample_id,
        qbit.qubit_concentration_ngul
    FROM qubit_measurements_v2$raw as qbit
    WHERE qbit.created_at$ = (
        SELECT MAX(sub.created_at$)
        FROM qubit_measurements_v2$raw AS sub
        WHERE sub.sample_id = qbit.sample_id
    )
),

latest_yield AS (
    SELECT
        dnay.sample_id,
        dnay.yield
    FROM yield_v2$raw as dnay
    WHERE dnay.created_at$ = (
        SELECT MAX(sub.created_at$)
        FROM yield_v2$raw AS sub
        WHERE sub.sample_id = dnay.sample_id
    )
),

latest_femto AS (
    SELECT
        femto.sample_id,
        femto.femto_date_code,
        femto.femto_profile_description AS femto_description,
        femto.gqn_dnaex
    FROM femto_dna_extract_v2$raw AS femto
    WHERE femto.created_at$ = (
        SELECT MAX(sub.created_at$)
        FROM femto_dna_extract_v2$raw as sub
        WHERE sub.sample_id = femto.sample_id
    )
),

latest_decision_making AS (
    SELECT
        dnad.sample_id,
        dnad.next_step,
        qc_passfail AS extraction_qc_result
    FROM dna_decision_making_v2$raw AS dnad
    WHERE dnad.created_at$ = (
        SELECT MAX(sub.created_at$)
        FROM dna_decision_making_v2$raw AS sub
        WHERE sub.sample_id = dnad.sample_id
    )
)

SELECT DISTINCT
    t.taxon_id,
    t.id AS eln_tissue_id,
    tp.id AS eln_tissue_prep_id,
    dna.id AS extraction_id,
    t.programme_id,
    t.specimen_id,
    DATE(con.created_at) AS creation_date,
    con.id AS fluidx_container_id, -- primary key
    con.barcode AS fluidx_id,
    tube.type AS tube_type,
    CASE
        WHEN con.archive_purpose$ IN ('Retired', 'Expended') THEN 0 -- Retired or expended DNA extractions have a weight of 0
        ELSE con.volume_si * 1000000
    END AS volume_ul,
    loc.name AS location,
    box.barcode AS rack,
    con.archive_purpose$ AS archive_purpose,
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
INNER JOIN container_content$raw AS cc -- Start of container/tube join
     ON cc.entity_id = dna.id
LEFT JOIN container$raw AS con
     ON con.id = cc.container_id
LEFT JOIN tube$raw AS tube
     ON cc.container_id = tube.id -- End of container/tube join
LEFT JOIN box$raw AS box -- Location chunk
    ON con.box_id = box.id
LEFT JOIN location$raw AS loc
    ON loc.id = box.location_id -- End of location chunk
LEFT JOIN tissue_prep$raw AS tp
     ON tp.id = dna.tissue_prep
LEFT JOIN tissue$raw AS t
     ON t.id = tp.tissue
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
    AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
    AND ent.name NOT LIKE '%Nuclei isolation and tagmentation%'
