SELECT c.barcode as sample_ref,
t.tolid as tolid,
t.scientific_name,
t.tubewell_id as tube_or_well_id,
pbsum.submission_date,
'pacbio' as sequencing_platform
FROM pacbio_sequencing_submission2$raw AS pbsum
LEFT JOIN container$raw AS c ON pbsum.sample_tube_id = c.id
LEFT JOIN container_content$raw AS cc ON pbsum.sample_tube_id = cc.container_id
LEFT JOIN submission_samples$raw AS subsam ON cc.entity_id = subsam.id
LEFT JOIN dna_extract$raw AS dna ON subsam.original_dna_extract = dna.id
LEFT JOIN tissue_prep$raw AS tp ON dna.tissue_prep = tp.id
LEFT JOIN tissue$raw AS t ON tp.tissue = t.id
WHERE c.archived$ = 'FALSE'
AND pbsum.archived$ = 'FALSE'
AND subsam.archived$ = 'FALSE'
AND dna.archived$ = 'FALSE'