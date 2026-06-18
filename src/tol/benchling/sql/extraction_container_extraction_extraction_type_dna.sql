/* 
## SQL Query: DNA Extraction Containers (Benchling Warehouse)

This SQL query retrieves detailed information about DNA extraction containers managed by the ToL Core Laboratory, including metadata, container details, and the latest QC measurements.

The resulting table includes identifiers for tissues, tissue preps, extractions, containers, and locations, as well as the most recent QC results (Nanodrop, Qubit, Femto, Yield, and Decision Making).

Output: Table with columns:

1) taxon_id: [character] Tissue metadata. Origin: STS
2) eln_tissue_id: [character] Benchling ID for the tissue the extraction is derived from.
3) tissue_sts_id: [character] STS ID for the tissue the extraction is derived from.
4) eln_tissue_prep_id: [character] Benchling ID for the tissue prep the extraction is derived from.
5) extraction_id: [character] DNA extraction entity ID (Benchling).
6) programme_id: [character] ToLID. Origin: BWH.
7) specimen_id: [character] Specimen ID. Origin: STS.
8) creation_date: [date] Date the container was created.
9) fluidx_container_id: [character] Primary key for the FluidX container.
10) fluidx_id: [character] FluidX barcode.
11) tube_type: [character] Type of tube/container.
12) volume_ul: [numeric] Volume in microliters (0 if archived as 'Retired' or 'Expended').
13) location: [character] Storage location name.
14) rack: [character] Box/rack barcode.
15) archive_purpose: [character] Reason for archiving the DNA extraction.
16) nanodrop_concentration_ngul: [numeric] Latest Nanodrop concentration (ng/µL).
17) dna_260_280_ratio: [numeric] Latest Nanodrop 260/280 ratio.
18) dna_260_230_ratio: [numeric] Latest Nanodrop 260/230 ratio.
19) qubit_concentration_ngul: [numeric] Latest Qubit concentration (ng/µL).
20) yield_ng: [numeric] Latest yield (ng).
21) femto_date_code: [character] Latest Femto date code.
22) femto_description: [character] Latest Femto profile description.
23) gqn_index: [numeric] Latest GQN index from Femto.
24) next_step: [character] Latest decision making next step.
25) extraction_qc_result: [character] Latest extraction QC result.

NOTES:
1) Only extractions from the 'ToL Core Lab' project and relevant folders are included.
2) Containers archived as 'Made in error' or with names matching '%Nuclei isolation and tagmentation%' are excluded.
3) Latest QC results are joined from their respective measurement tables.
4) Volume is set to 0 for archived/expended extractions.
5) Data types are preserved as in the Benchling Warehouse.

*/

WITH locations AS (
    WITH RECURSIVE sg AS (
        SELECT 
            id AS location,
            location_id AS parent,
            barcode,
            name,
            ARRAY[barcode] AS barcode_path,
            ARRAY[name] AS name_path,	
            ARRAY[id] AS id_path
        FROM location$raw
        WHERE location_id IS NULL
        UNION ALL
        SELECT
            l.id,
            l.location_id,
            l.barcode,
            l.name,
            sg.barcode_path || l.barcode,
            sg.name_path || l.name,
            sg.id_path || l.id
        FROM location$raw l
        JOIN sg ON sg.location = l.location_id
    )
    SELECT
        location AS location_id,
        name,
        ARRAY_TO_STRING(name_path, ' / ') AS full_location,
        ARRAY_TO_STRING(barcode_path, ' / ') AS full_barcodes
    FROM sg
),

-- Latest nanodrop per (sample, tube). Unnest the sample_tube_id jsonb array so each measurement is attributed to the container it was taken on
latest_nanodrop_conc AS (
    SELECT
        sample_id,
        tube_id,
        nanodrop_concentration_ngul,
        dna_260_280_ratio,
        dna_260_230_ratio
    FROM (
        SELECT
            nanod.sample_id,
            tube.value AS tube_id, -- specific container this result belongs to
            nanod.nanodrop_concentration_ngul,
            nanod._260_280_ratio AS dna_260_280_ratio,
            nanod._260_230_ratio AS dna_260_230_ratio,
            ROW_NUMBER() OVER (
                PARTITION BY nanod.sample_id, tube.value
                ORDER BY nanod.created_at$ DESC
            ) AS rn
        FROM nanodrop_measurements_v2$raw AS nanod
        -- unnest the array of tube IDs; LEFT JOIN keeps rows even if no tube recorded
        LEFT JOIN LATERAL jsonb_array_elements_text(nanod.sample_tube_id) AS tube(value) ON TRUE
    ) ranked
    WHERE ranked.rn = 1
),

-- Latest qubit per (sample, tube)
latest_qubit_conc AS (
    SELECT
        sample_id,
        tube_id,
        qubit_concentration_ngul
    FROM (
        SELECT
            qbit.sample_id,
            tube.value AS tube_id,
            qbit.qubit_concentration_ngul,
            ROW_NUMBER() OVER (
                PARTITION BY qbit.sample_id, tube.value
                ORDER BY qbit.created_at$ DESC
            ) AS rn
        FROM qubit_measurements_v2$raw AS qbit
        LEFT JOIN LATERAL jsonb_array_elements_text(qbit.sample_tube_id) AS tube(value) ON TRUE
    ) ranked
    WHERE ranked.rn = 1
),

-- Latest yield per (sample, tube)
latest_yield AS (
    SELECT
        sample_id,
        tube_id,
        yield
    FROM (
        SELECT
            dnay.sample_id,
            tube.value AS tube_id,
            dnay.yield,
            ROW_NUMBER() OVER (
                PARTITION BY dnay.sample_id, tube.value
                ORDER BY dnay.created_at$ DESC
            ) AS rn
        FROM yield_v2$raw AS dnay
        LEFT JOIN LATERAL jsonb_array_elements_text(dnay.sample_tube_id) AS tube(value) ON TRUE
    ) ranked
    WHERE ranked.rn = 1
),

-- Latest femto per (sample, tube)
latest_femto AS (
    SELECT
        sample_id,
        tube_id,
        femto_date_code,
        femto_description,
        gqn_dnaex
    FROM (
        SELECT
            femto.sample_id,
            tube.value AS tube_id,
            femto.femto_date_code,
            femto.femto_profile_description AS femto_description,
            femto.gqn_dnaex,
            ROW_NUMBER() OVER (
                PARTITION BY femto.sample_id, tube.value
                ORDER BY femto.created_at$ DESC
            ) AS rn
        FROM femto_dna_extract_v2$raw AS femto
        LEFT JOIN LATERAL jsonb_array_elements_text(femto.sample_tube_id) AS tube(value) ON TRUE
    ) ranked
    WHERE ranked.rn = 1
),

-- Latest decision making per (sample, tube). This schema stores the current tube
-- in sample_tube_id (jsonb array).
latest_decision_making AS (
    SELECT
        sample_id,
        tube_id,
        next_step,
        extraction_qc_result
    FROM (
        SELECT
            dnad.sample_id,
            tube.value AS tube_id,
            dnad.next_step,
            dnad.qc_passfail AS extraction_qc_result,
            ROW_NUMBER() OVER (
                PARTITION BY dnad.sample_id, tube.value
                ORDER BY dnad.created_at$ DESC
            ) AS rn
        FROM dna_decision_making_v2$raw AS dnad
        LEFT JOIN LATERAL jsonb_array_elements_text(dnad.sample_tube_id) AS tube(value) ON TRUE
    ) ranked
    WHERE ranked.rn = 1
),

corelab_extraction_containers AS (

    SELECT DISTINCT
        t.taxon_id,
        t.id AS eln_tissue_id,
        t.sts_id AS tissue_sts_id,
        tp.id AS eln_tissue_prep_id,
        dna.id AS extraction_id,
        t.programme_id,
        t.specimen_id,
        DATE(con.created_at) AS creation_date,
        con.id AS fluidx_container_id, -- primary key
        con.barcode AS fluidx_id,
        tube.type AS tube_type,
        CASE
            WHEN con.archived$ THEN 0 -- Archived DNA extractions have a weight of 0
            ELSE con.volume_si * 1000000
        END AS volume_ul,
		CASE
			WHEN con.archived$ THEN NULL
			ELSE CONCAT(locations.full_location, ' / ', box.barcode) 
		END AS location_path,
        chr(ascii('A') + con.row_index) || (con.column_index + 1) AS tube_position,
		con.archived$ AS archived,
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
	LEFT JOIN locations
		ON locations.location_id = box.location_id
    LEFT JOIN tissue_prep$raw AS tp
        ON tp.id = dna.tissue_prep
    LEFT JOIN tissue$raw AS t
        ON t.id = tp.tissue
    -- Results chunk: now matched on BOTH the DNA extract entity AND the specific container, so each tube only shows results recorded against it
    LEFT JOIN latest_nanodrop_conc
        ON dna.id = latest_nanodrop_conc.sample_id
        AND con.id = latest_nanodrop_conc.tube_id
    LEFT JOIN latest_qubit_conc
        ON dna.id = latest_qubit_conc.sample_id
        AND con.id = latest_qubit_conc.tube_id
    LEFT JOIN latest_yield
        ON dna.id = latest_yield.sample_id
        AND con.id = latest_yield.tube_id
    LEFT JOIN latest_femto
        ON dna.id = latest_femto.sample_id
        AND con.id = latest_femto.tube_id
    LEFT JOIN latest_decision_making
        ON dna.id = latest_decision_making.sample_id
        AND con.id = latest_decision_making.tube_id -- End Results chunk
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
        AND COALESCE(ent.name, '') NOT LIKE '%Nuclei isolation and tagmentation%'
    ),

mock_lres_extractions_containers AS (
	SELECT DISTINCT
        t.taxon_id,
        t.id AS eln_tissue_id,
        t.sts_id AS tissue_sts_id,
        tp.id AS eln_tissue_prep_id,
        ssid.sanger_sample_id AS extraction_id,
        t.programme_id,
        t.specimen_id,
        DATE(tpsub.submitted_submission_date) AS creation_date,
        ssid.sanger_sample_id AS fluidx_container_id, -- primary key
        NULL::varchar AS fluidx_id,
        NULL::varchar AS tube_type,
        NULL::float AS volume_ul,
        'lres'::varchar AS location_path,
        NULL::varchar AS tube_position,
		NULL::boolean AS archived,
        NULL::varchar AS archive_purpose,
        NULL::float AS nanodrop_concentration_ngul,
        NULL::float AS dna_260_280_ratio,
        NULL::float AS dna_260_230_ratio,
        NULL::float AS qubit_concentration_ngul,
        NULL::float AS yield_ng,
        NULL::varchar AS femto_date_code,
        NULL::jsonb AS femto_description,
        NULL::float AS gqn_index,
        NULL::jsonb AS next_step,
        NULL::varchar AS extraction_qc_result
	FROM tissue_prep$raw AS tp
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	LEFT JOIN container_content$raw AS cc 
		ON tp.id = cc.entity_id
	LEFT JOIN container$raw AS c 
		ON cc.container_id = c.id
	LEFT JOIN tissue_prep_submission_workflow_output$raw AS tpsub
		ON c.id = tpsub.sample_tube_id
	LEFT JOIN container$raw AS sub_con
		ON tpsub.sample_tube_id = sub_con.id
	LEFT JOIN storage$raw AS stor 
		ON c.location_id = stor.id
	LEFT JOIN sanger_sample_id$raw AS ssid 
		ON c.id = ssid.sample_tube
	LEFT JOIN project$raw AS proj
		ON tp.project_id$ = proj.id
	LEFT JOIN folder$raw AS f 
		ON tp.folder_id$ = f.id
	WHERE sub_con.id IS NOT NULL
		AND proj.name = 'ToL Core Lab'
		AND f.name = 'Sample Prep'
		AND tpsub.downstream_application IS DISTINCT FROM 'RNA'
)

SELECT * FROM corelab_extraction_containers
UNION ALL
SELECT * FROM mock_lres_extractions_containers
