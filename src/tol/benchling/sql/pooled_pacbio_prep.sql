/* 
## SQL Query: PacBio prep data Benchling Warehouse (BWH)

This SQL query retrieves all the information of PacBio preparations from pooled dna samples performed by the ToL Core Laboratory. 

The table produced also contains the eln_submission_sample_id and eln_file_registry_id 
which uniquely idenfied each dna extract entity in Benchling Warehouse (BWH). 

The eln_dna_extract_id can be used as the foreign key to the DNA extract entity the
submission is derived from.

Output: Table with cols: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the extractions is derived from.
4) eln_tissue_prep_id: [character] Benchling id for the tissue prep the extractions is derived from.
5) eln_dna_extract_id: [character] id of the first dna extract that was pooled. Used as a connection to the tissue metadata. 
6) eln_pooled_sample_id: [character] Key to original pooled dna extract.
7) eln_file_registry_id: [character] id in Benchling Registry.
8) eln_submission_sample_id: [character] primary key.
9) submission_sample_container: [character] container barcode of the submission sample. This contains the Sanger Sample ID.
10) pbprep_bnt_id: [character] Batches and Tracking legacy id.

NOTES: 

1) DISTINCT ON and ORDER BY are applied together to delete duplicated rows present in BWH.

*/

SELECT DISTINCT ON (subsam.name$, con.barcode)
	t.sts_id,
	t.taxon_id,
	t.id AS eln_tissue_id,
	tp.id AS eln_tissue_prep_id,
	dna.id AS eln_dna_extract_id,
	pdna.id AS eln_pooled_sample_id,
	subsam.file_registry_id$ AS eln_file_registry_id,
	subsam.id AS eln_submission_sample_id,
	t.tolid,
	COALESCE(DATE(subsam.created_on), DATE(subsam.created_at$)) AS preparation_date,
	subsam.name$ AS eln_submission_sample_name,
	con.barcode AS submission_sample_container,
	subsam.bt_id AS pbprep_bnt_id
FROM submission_samples$raw AS subsam
LEFT JOIN pooled_samples$raw AS pdna
	ON subsam.pooled_sample = pdna.id
LEFT JOIN dna_extract$raw AS dna -- Chunk for for metada
	ON pdna.samples ->> 0 = dna.id
LEFT JOIN tissue_prep$raw AS tp 
	ON dna.tissue_prep = tp.id
LEFT JOIN tissue$raw AS t 
	ON tp.tissue = t.id -- End of Chunk for for metada
LEFT JOIN container_content$raw AS cc -- Chunk for Container info
	ON cc.entity_id = subsam.id
LEFT JOIN container$raw AS con 
	ON con.id = cc.container_id -- End of Chunk for Container info
LEFT JOIN pacbio_decision_making_v2$raw AS pbdc -- Chunk for results
	ON subsam.id = pbdc.sample_id
LEFT JOIN nanodrop_measurements_v2$raw AS nanod 
	ON subsam.id = nanod.sample_id
LEFT JOIN qubit_measurements_v2$raw AS qbit 
	ON subsam.id = qbit.sample_id
LEFT JOIN shearing_step$raw AS shear_v1 -- Chunk for uniting Shear_Step from Data Models 1 and 2
		ON con.id = shear_v1.sample_submission_tube
	LEFT JOIN shearing_step_v2$raw AS shear_v2 
		ON subsam.id = shear_v2.sample_id -- End Chunk for uniting Shear_Step from Data Models 1 and 2
LEFT JOIN sanger_tol.femto_pacbio_prep_v2$raw AS femtopb 
	ON subsam.id = femtopb.sample_id
LEFT JOIN spri_info_v2$raw AS spri 
	ON subsam.id = spri.sample_id
LEFT JOIN pacbio_yield_v2$raw AS pbyield 
	ON subsam.id = pbyield.sample_id -- End of chunk for results
LEFT JOIN pacbio_preparation_from_gdna$raw AS pbgdna -- Just for the category field
	ON dna.id = pbgdna.dna_extract ->> 0
LEFT JOIN folder$raw AS f 
	ON subsam.folder_id$ = f.id
WHERE (f.name IN ('Routine Throughput', 'PacBio prep', 'Core Lab Entities', 'Benchling MS Project Move') OR f.name IS NULL)
	AND (subsam.archive_purpose$ != ('Made in error') OR subsam.archive_purpose$ IS NULL)
	AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL) --not necessary anymore
	AND subsam.pooled_sample IS NOT NULL -- Exluding non pooled samples
	AND con.barcode IS NOT NULL -- Excluding submission samples without containers.
ORDER BY 
	eln_submission_sample_name DESC, -- To enable DISTINCT On and select only the most recent result
	submission_sample_container DESC,
	subsam.modified_at$ DESC,
	shear_v2.modified_at$ DESC,
	spri.modified_at$ DESC,
	qbit.modified_at$ DESC, 
	nanod.modified_at$ DESC, 
	femtopb.modified_at$ DESC,
	pbyield.modified_at$ DESC,
	pbdc.modified_at$ DESC;
