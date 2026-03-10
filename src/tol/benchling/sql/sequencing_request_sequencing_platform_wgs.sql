-- Change this one to be only for WGS, mirroring the ONT one

/* 
## SQL Query: WGS Submissions Benchling Warehouse (BWH)

Output: Table with cols:

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) tissue_prep_id: [character] Foreign key to tissue prep entity. Origin: BWH
4) extraction_id: [character] Foreign key to extraction entity. Origin: BWH
5) submission_sample_id: [character] Foreign key to the entity being submitted. Could be DNA extraction or SubSam. Origin: BWH
6) bt_id: [character] B&T ID (legacy)
7) programme_id: [character] ToLID.
8) specimen_id: [character] Origin: STS
9) submission_sample_name: [character] The name of the entity that is being submitted
10) sequencing_platform: [character] Sequencing platform: WGS
11) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the WGS submission. 
12) tube_id: [character] Container barcode of submission tube. Origin: BWH
13) completion_date: [Date] Date of submission. Origin: BWH
14) source: [character] Data source: v1

Notes:
1. Data Sources: 
   - Submissions are categorized by workflow (individual tubes, pooled DNA, and subsampled DNA) for better traceability.
2. Filtering Criteria:
   - Archived submissions and invalid Sanger Sample IDs are excluded to ensure data quality.
   - Completed workflow tasks are required for inclusion.
3. Pooled DNA Workflow:
   - Pooled DNA submissions are processed separately to account for their unique metadata structure.
   - The first DNA extract in a pooled sample is used to link tissue metadata.
4. Combined Results:
   - Metadata from different workflows is unified using `COALESCE` to provide consistent output for shared fields.
*/ 


WITH dna_extr_submissions AS (
    SELECT
		dna.id,
        t.sts_id,
        t.taxon_id,
        tp.id AS tissue_prep_id,
        t.programme_id,
        t.specimen_id,
		dna_sub.display_id$ AS submission_display_id,
        dna.id AS submission_sample_id,
		dna.name$ AS submission_sample_name,
        dna_sub_out.submission_platform AS sequencing_platform,
        ssid.sanger_sample_id,
        c.barcode AS tube_id,
        dna_sub.executed_on$ AS completion_date,
        tp.bt_id,
        'v1'::varchar AS source
    FROM dna_extract_submission$raw AS dna_sub
    LEFT JOIN dna_extract_submission_output$raw AS dna_sub_out
        ON dna_sub.sample_tube_id = dna_sub_out.sample_tube_id
    LEFT JOIN workflow_task_status$raw AS status
        ON dna_sub.workflow_task_status_id$ = status.id
    LEFT JOIN container_content$raw AS cc
        ON dna_sub.sample_tube_id = cc.container_id
    LEFT JOIN container$raw AS c
        ON cc.container_id = c.id
    LEFT JOIN sanger_sample_id$raw AS ssid
        ON dna_sub.sample_tube_id = ssid.sample_tube
    LEFT JOIN dna_extract$raw AS dna
        ON cc.entity_id = dna.id
    LEFT JOIN tissue_prep$raw AS tp
        ON tp.id = dna.tissue_prep
    LEFT JOIN tissue$raw AS t
        ON t.id = tp.tissue
    LEFT JOIN project$raw AS proj
        ON tp.project_id$ = proj.id
    WHERE dna_sub.archived$ = 'FALSE'
      AND ssid.sanger_sample_id IS NOT NULL
      AND ssid.sanger_sample_id != ''
      AND status.status_type = 'COMPLETED'
	  AND dna_sub_out.submission_platform = 'WGS'
),
pooled_dna_extr_submissions AS (
    SELECT
		dnap.id,
        t.sts_id,
        t.taxon_id,
        tp.id AS tissue_prep_id,
        t.programme_id,
        t.specimen_id,
		sub.display_id$ AS submission_display_id,
        dnap.id AS submission_sample_id,
		dnap.name$ AS submission_sample_name,
        dna_sub_out.submission_platform AS sequencing_platform,
        ssid.sanger_sample_id,
        tube.name$ AS tube_id,
        sub.executed_on$ AS completion_date,
        tp.bt_id,
        'v1'::varchar AS source
    FROM pooled_samples$raw AS dnap
    LEFT JOIN container_content$raw AS cc
        ON dnap.id = cc.entity_id
    LEFT JOIN container AS c
        ON cc.container_id = c.id
    LEFT JOIN dna_extract$raw AS source_dna
        ON dnap.samples ->> 0 = source_dna.id
    LEFT JOIN tissue_prep$raw AS tp
        ON tp.id = source_dna.tissue_prep
    LEFT JOIN tissue$raw AS t
        ON t.id = tp.tissue
    LEFT JOIN tube$raw AS tube
        ON cc.container_id = tube.id
    LEFT JOIN folder$raw AS f
        ON dnap.folder_id$ = f.id
    LEFT JOIN sanger_sample_id$raw AS ssid
        ON tube.id = ssid.sample_tube
    LEFT JOIN dna_extract_submission$raw AS sub
        ON tube.id = sub.sample_tube_id
    LEFT JOIN dna_extract_submission_output$raw AS dna_sub_out
        ON sub.sample_tube_id = dna_sub_out.sample_tube_id
    LEFT JOIN workflow_task_status$raw AS status
        ON sub.workflow_task_status_id$ = status.id
    WHERE dnap.archived$ = 'FALSE'
      AND sub.archived$ = 'FALSE'
      AND ssid.sanger_sample_id IS NOT NULL
      AND ssid.sanger_sample_id != ''
      AND status.status_type = 'COMPLETED'
	  AND dna_sub_out.submission_platform = 'WGS'
),
subsam_submissions AS (
    SELECT
		subsam.original_dna_extract,
        t.sts_id,
        t.taxon_id,
        tp.id AS tissue_prep_id,
        t.programme_id,
        t.specimen_id,
		sub.display_id$ AS submission_display_id,
        subsam.id AS submission_sample_id,
		subsam.name$ AS submission_sample_name,
        dna_sub_out.submission_platform AS sequencing_platform,
        ssid.sanger_sample_id,
        tube.name$ AS tube_id,
        sub.executed_on$ AS completion_date,
        tp.bt_id,
        'v1'::varchar AS source
    FROM submission_samples$raw AS subsam
    LEFT JOIN dna_extract$raw AS dna
        ON subsam.original_dna_extract = dna.id
    LEFT JOIN tissue_prep$raw AS tp
        ON tp.id = dna.tissue_prep
    LEFT JOIN tissue$raw AS t
        ON t.id = tp.tissue
    LEFT JOIN project$raw AS proj
        ON tp.project_id$ = proj.id
    LEFT JOIN container_content$raw AS cc
        ON subsam.id = cc.entity_id
    LEFT JOIN container$raw AS c
        ON cc.container_id = c.id
    LEFT JOIN tube$raw AS tube
        ON c.name = tube.name$
    LEFT JOIN sanger_sample_id$raw AS ssid
        ON tube.id = ssid.sample_tube
    LEFT JOIN dna_extract_submission$raw AS sub
        ON tube.id = sub.sample_tube_id
    LEFT JOIN dna_extract_submission_output$raw AS dna_sub_out
        ON sub.sample_tube_id = dna_sub_out.sample_tube_id
    LEFT JOIN workflow_task_status$raw AS status
        ON sub.workflow_task_status_id$ = status.id
    WHERE sub.id IS NOT NULL
      AND sub.archived$ = 'FALSE'
      AND ssid.sanger_sample_id IS NOT NULL
      AND ssid.sanger_sample_id != ''
      AND status.status_type = 'COMPLETED'
      AND proj.name = 'ToL Core Lab'
	  AND dna_sub_out.submission_platform = 'WGS'
),
subsam_from_pdna_submissions AS (
		SELECT
		source_dna.id AS dna_id,
		subsam.name$,
        t.sts_id,
        t.taxon_id,
        tp.id AS tissue_prep_id,
        t.programme_id,
        t.specimen_id,
		sub.display_id$ AS submission_display_id,
        subsam.id AS submission_sample_id,
		subsam.name$ AS submission_sample_name,
        dna_sub_out.submission_platform AS sequencing_platform,
        ssid.sanger_sample_id,
        tube.name$ AS tube_id,
        sub.executed_on$ AS completion_date,
        tp.bt_id,
        'v1'::varchar AS source
    FROM submission_samples$raw AS subsam
    LEFT JOIN pooled_samples$raw AS dnap
        ON subsam.pooled_sample = dnap.id
    LEFT JOIN dna_extract$raw AS source_dna
        ON dnap.samples ->> 0 = source_dna.id
    LEFT JOIN tissue_prep$raw AS tp
        ON tp.id = source_dna.tissue_prep
    LEFT JOIN tissue$raw AS t
        ON t.id = tp.tissue
    LEFT JOIN project$raw AS proj
        ON tp.project_id$ = proj.id
    LEFT JOIN container_content$raw AS cc
        ON subsam.id = cc.entity_id
    LEFT JOIN container$raw AS c
        ON cc.container_id = c.id
    LEFT JOIN tube$raw AS tube
        ON c.name = tube.name$
    LEFT JOIN sanger_sample_id$raw AS ssid
        ON tube.id = ssid.sample_tube
    LEFT JOIN dna_extract_submission$raw AS sub
        ON tube.id = sub.sample_tube_id
    LEFT JOIN dna_extract_submission_output$raw AS dna_sub_out
        ON sub.sample_tube_id = dna_sub_out.sample_tube_id
    LEFT JOIN workflow_task_status$raw AS status
        ON sub.workflow_task_status_id$ = status.id
    WHERE sub.id IS NOT NULL
      AND sub.archived$ = 'FALSE'
      AND ssid.sanger_sample_id IS NOT NULL
      AND ssid.sanger_sample_id != ''
      AND status.status_type = 'COMPLETED'
      AND proj.name = 'ToL Core Lab'
	  AND dna_sub_out.submission_platform = 'WGS'
)

SELECT
    COALESCE(dna.sts_id, pooled_dna.sts_id, subsam.sts_id, psubsam.sts_id) AS sts_id,
    COALESCE(dna.taxon_id, pooled_dna.taxon_id, subsam.taxon_id, psubsam.taxon_id) AS taxon_id,
    COALESCE(dna.tissue_prep_id, pooled_dna.tissue_prep_id, subsam.tissue_prep_id, psubsam.tissue_prep_id) AS tissue_prep_id,
	COALESCE(dna.id, pooled_dna.id, subsam.original_dna_extract, psubsam.dna_id) AS extraction_id,
	COALESCE(dna.submission_sample_id, pooled_dna.submission_sample_id, subsam.submission_sample_id, psubsam.submission_sample_id) AS submission_sample_id,
	dna.bt_id,
    COALESCE(dna.programme_id, pooled_dna.programme_id, subsam.programme_id, psubsam.programme_id) AS programme_id,
    COALESCE(dna.specimen_id, pooled_dna.specimen_id, subsam.specimen_id, psubsam.specimen_id) AS specimen_id,
	COALESCE(dna.submission_sample_name, pooled_dna.submission_sample_name, subsam.submission_sample_name, psubsam.submission_sample_name) AS submission_sample_name,
    dna.sequencing_platform,
    dna.sanger_sample_id,
    dna.tube_id,
    dna.completion_date,
    dna.source
FROM dna_extr_submissions AS dna
LEFT JOIN pooled_dna_extr_submissions AS pooled_dna
    ON dna.submission_display_id = pooled_dna.submission_display_id
LEFT JOIN subsam_submissions AS subsam
    ON dna.submission_display_id = subsam.submission_display_id
LEFT JOIN subsam_from_pdna_submissions AS psubsam
	ON dna.submission_display_id = psubsam.submission_display_id;
