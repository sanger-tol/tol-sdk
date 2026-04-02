/* 
## SQL Query: ONT Submissions Benchling Warehouse (BWH)

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
10) sequencing_platform: [character] Sequencing platform: ONT
11) sanger_sample_id: [character] Sanger Sample ID or Sanger UUID of the ONT submission. 
12) tube_id: [character] Container barcode of submission tube. Origin: BWH
13) sheared: [character] Is the submission sample sheared. Origin: BWH
14) spried: [character] Is the submission sample spried. Origin: BWH
15) completion_date: [Date] Date of submission. Origin: BWH
16) source: [character] Data source: v1 - pre ONT template DNA extract submission workflows, v2
*/

WITH base AS (
    SELECT
        out.sample_tube_id,
        out.submission_platform,
        out.submitted_submission_date,
        con.barcode AS tube_id,
        cc.entity_id,
        ssid.sanger_sample_id
    FROM dna_extract_submission_output$raw out
    LEFT JOIN container$raw con
        ON out.sample_tube_id = con.id
    LEFT JOIN container_content$raw cc
        ON cc.container_id = con.id
    LEFT JOIN sanger_sample_id$raw ssid
        ON out.sample_tube_id = ssid.sample_tube
	LEFT JOIN workflow_task$raw AS wft
		ON out.workflow_task_id$ = wft.id
	LEFT JOIN workflow_task_status$raw AS wfts
		ON wft.workflow_task_status_id = wfts.id
    WHERE out.submission_platform = 'ONT'
		AND wfts.status_type = 'COMPLETED'
)

SELECT
    t.sts_id,
    t.taxon_id,
	tp.id AS tissue_prep_id,
	COALESCE(dna.id, source_dna.id, subsam_dna.id, subsubsam_dna.id) AS extraction_id,
    COALESCE(
        dna.id,
        pdna.id,
        subsam.id,
		subsubsam.id
    ) AS submission_sample_id,
    tp.bt_id,
    t.programme_id,
    t.specimen_id,
    COALESCE(
        dna.name$,
        pdna.name$,
        subsam.name$
    ) AS submission_sample_name,
    base.submission_platform AS sequencing_platform,
    base.sanger_sample_id,
    base.tube_id,
	CASE 
    	WHEN subsam.id IS NOT NULL THEN 'Yes'
    	ELSE 'No'
	END AS sheared,
	CASE
		WHEN subsam.id IS NOT NULL THEN 'Yes'
		ELSE 'No'
	END AS spried,
    base.submitted_submission_date AS completion_date,
    'v1'::varchar AS source

FROM base
-- direct DNA
LEFT JOIN dna_extract$raw AS dna
    ON dna.id = base.entity_id
-- pooled DNA
LEFT JOIN pooled_samples$raw AS pdna
    ON pdna.id = base.entity_id
LEFT JOIN dna_extract$raw source_dna
    ON pdna.samples ->> 0 = source_dna.id
-- subsampled DNA
LEFT JOIN submission_samples$raw AS subsam
    ON subsam.id = base.entity_id
LEFT JOIN dna_extract$raw subsam_dna
    ON subsam.original_dna_extract = subsam_dna.id
-- subsampled subsample
LEFT JOIN submission_samples$raw AS subsubsam
	ON subsam.submission_sample = subsubsam.id
LEFT JOIN dna_extract$raw AS subsubsam_dna
	ON subsubsam.original_dna_extract = subsubsam_dna.id
-- resolve which dna to use
LEFT JOIN tissue_prep$raw tp
    ON tp.id = COALESCE(
        dna.tissue_prep,
        source_dna.tissue_prep,
        subsam_dna.tissue_prep,
		subsubsam_dna.tissue_prep
    )
LEFT JOIN tissue$raw t
    ON t.id = tp.tissue
	
UNION ALL

SELECT
	t.sts_id,
	t.taxon_id,
	tp.id AS tissue_prep_id,
    dna.id AS extraction_id,
	subsam.id AS submission_sample_id,
	tp.bt_id,
	t.programme_id,
	t.specimen_id,
	subsam.name$ AS submission_sample_name,
	'ONT'::varchar AS sequencing_platform,
	ssid.sanger_sample_id,
	c.barcode AS tube_id,
	ss.shearing_required AS sheared,
	ss.spri_required AS spried,
	out.submission_date AS completion_date,
	'v2'::varchar AS source
FROM ont_submissions_output$raw AS out
LEFT JOIN container$raw AS c
	ON c.id = out.sample_tube_id
LEFT JOIN container_content$raw AS cc
	ON cc.container_id = c.id
LEFT JOIN submission_samples$raw AS subsam
	ON cc.entity_id = subsam.id
LEFT JOIN dna_extract$raw AS dna
	ON dna.id = subsam.original_dna_extract
LEFT JOIN tissue_prep$raw AS tp
	ON tp.id = dna.tissue_prep
LEFT JOIN tissue$raw AS t
	ON t.id = tp.tissue
LEFT JOIN sanger_sample_id$raw AS ssid
	ON ssid.sample_tube = c.id
LEFT JOIN ont_shear_spri_decision$raw AS ss
	ON ss.submission_sample = subsam.id
LEFT JOIN workflow_task$raw AS wft
	ON out.workflow_task_id$ = wft.id
LEFT JOIN workflow_task_status$raw AS wfts
	ON wft.workflow_task_status_id = wfts.id
WHERE wfts.status_type = 'COMPLETED'
ORDER BY completion_date DESC
