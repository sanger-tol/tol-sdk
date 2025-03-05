/* 
## SQL Query: WGS Submissions Benchling Warehouse (BWH)

Output: Table with cols:

1. sts_id: [integer] Tissue metadata. Origin: STS.
2. taxon_id: [character] Tissue metadata. Origin: STS.
3. tissue_prep_id: [character]  Foreign key to tissue prep entity in Benchling. Origin: BWH.
4. programme_id: [character] ToLID.
5. specimen_id: [character] Origin: STS.
6. submission_display_id: [character] ID of the sequencing submission. Origin: Benchling.
7. sequencing_platform: [character] Sequencing platform: WGS, ONT
8. sanger_sample_id: [character] Sanger Sample ID for the submission.
9. tube_id: [character] Identifier for the tube containing DNA extract. Origin: Benchling.
10. completion_date: [timestamp] Timestamp of submission execution. Origin: Benchling.
11. bt_id: [character] B&T ID (legacy)
12. source: [character] Data source: v1, legacy_bnt

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
      
)
SELECT
	COALESCE(dna.id, pooled_dna.id, subsam.original_dna_extract) AS extraction_id,
    COALESCE(dna.sts_id, pooled_dna.sts_id, subsam.sts_id) AS sts_id,
    COALESCE(dna.taxon_id, pooled_dna.taxon_id, subsam.taxon_id) AS taxon_id,
    COALESCE(dna.tissue_prep_id, pooled_dna.tissue_prep_id, subsam.tissue_prep_id) AS tissue_prep_id,
    COALESCE(dna.programme_id, pooled_dna.programme_id, subsam.programme_id) AS programme_id,
    COALESCE(dna.specimen_id, pooled_dna.specimen_id, subsam.specimen_id) AS specimen_id,
    dna.submission_display_id,
    dna.sequencing_platform,
    dna.sanger_sample_id,
    dna.tube_id,
    dna.completion_date,
    dna.bt_id,
    dna.source
FROM dna_extr_submissions AS dna
LEFT JOIN pooled_dna_extr_submissions AS pooled_dna
    ON dna.submission_display_id = pooled_dna.submission_display_id
LEFT JOIN subsam_submissions AS subsam
    ON dna.submission_display_id = subsam.submission_display_id;
