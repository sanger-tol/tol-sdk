/* 
## SQL Query: Tissue preps produced during Sample Prep - Benchling Warehouse (BWH)

This query retrieves all the tissue preps produced during sample preparation in the ToL Core Lab. 
The ouput table gathers metadata and data relevant for all laboratory downstream processes. 

The table contains the eln_tisprep_id and eln_file_registry_id which uniquely idenfied each tissue prep entity in Benchling Warehouse (BWH). 

The eln_tisprep_id should be used as the foreign key to establish a relationship with its child entities (i.e. dna_extract and rna_sample). 

The eln_tissue_id is included as the foreign key to parent tissue entities.  

In Benchling warehouse the tissue prep schema gathers all these fields. Always use the .*$raw version of any schema in Benchling. 
These .*$raw tables contain all the data included the entities and fields that have been archived.
For more information: https://help.benchling.com/hc/en-us/articles/9684262336397-What-is-the-difference-between-tables-that-are-suffixed-with-raw-vs-not-

NOTE: As 2023-07-06 because of (1) the introduction of dynamic fields for metadata changes, and (2) a few fields in downstream entities not updating, 
it was decided that for the sake of data integrity all samples' metadata must be retrieved always from the tissue schema.

The queries must filter the data by the Benchling projects that are relevant to the ToL Core Lab: 'Core Lab Entities', 'R&D', and 'Routine Throughput'

Columns in output table: 

1) sts_id: [integer] Tissue metadata. Origin: STS
2) taxon_id: [character] Tissue metadata. Origin: STS
3) eln_tissue_id: [character] Benchling id for the tissue the tissue prep is derived from.
4) eln_tissue_prep_id: [character] Tissue prep primary key in Benchling.
5) eln_file_registry_id: [character] id in Benchling Registry.
6) programme_id: [character] ToLID. Origin: BWH
6) specimen_id: [character] Specimen ID. Origin: STS
7) eln_tissue_prep_name: [character]
8) sampleprep_date: [Date] date of sample preparation.
9) tissue_prep_fluidx_id: [character] fluidx id of the tissue prep container
10) tube_location: [character] location of the tissue prep container.
11) weight_mg: [double] weight in mg of the tissue prep.
12) downstream_protocol: [text] downstream process the tissue prep was prepped for.
13) disruption_method: [character] method used to disrupt the tissue.
14) tissue_prep_type: [character] tissue type for HiC SciOps submissions.
15) sciops_protocol_required: [character] protocol required for HiC SciOps submissions.
16) sts_labwork_category: [character] Reason for exporting tissue. Aid to interpret downstream protocol for legacy samples.
17) tissue_prep_bnt_id: [character] Batches and Tracking legacy id.
*/

WITH tissue_preps AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		t.id AS eln_tissue_id,
		tp.id AS eln_tissue_prep_id,
		t.programme_id,
		t.specimen_id,
		tp.name$ AS eln_tissue_prep_name,
		DATE(tp.created_at$) AS sampleprep_date,
		con.barcode AS tissue_prep_fluidx_id,
		loc.name AS tube_location,
		CASE
			WHEN con.archive_purpose$ IN ('Retired', 'Expended') THEN 0 -- Retired or expended tissue preps have a weight of 0
			WHEN loc.name = 'SciOps ToL Lab' THEN 0 -- Tissue preps sent to LRES have a weight of 0
			ELSE con.volume_si * 1000000
		END AS weight_mg,
		tube.tissue_prep_downstream_process AS downstream_protocol,
		tube.tissue_prep_disruption_method AS disruption_method,
		tube.tissue_prep_type,
		tube.sciops_protocol_required,
		t.lab_work_category AS labwork_category_sts,
		tp.bt_id AS tissue_prep_bnt_id
	FROM incoming_tissue_and_tissue_prep2$raw AS wrkf_tp
	LEFT JOIN tissue_prep$raw AS tp
		ON wrkf_tp.tissue_prep_id ->> 0 = tp.id
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	LEFT JOIN container$raw AS con 
		ON wrkf_tp.tissue_prep_tube_id = con.id
	LEFT JOIN tube$raw AS tube
		ON con.id = tube.id
	LEFT JOIN location$raw AS loc
		ON tube.location_id$ = loc.id
	LEFT JOIN project$raw AS proj
		ON tp.project_id$ = proj.id
	LEFT JOIN folder$raw AS f
		ON t.folder_id$ = f.id
	WHERE proj.name = 'ToL Core Lab'
		AND f.name IN ('Core Lab Entities', 'R&D', 'Routine Throughput', 'Benchling MS Project Move', 'ToL Core Restricted Entities')
		AND (tp.archive_purpose$ != ('Made in error') OR tp.archive_purpose$ IS NULL)
		AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)

),
legacy_tissue_preps AS (
	
	SELECT DISTINCT
		t.sts_id,
		t.taxon_id,
		t.id AS eln_tissue_id,
		tp.id AS eln_tissue_prep_id,
		t.programme_id,
		t.specimen_id,
		tp.name$ AS eln_tissue_prep_name,
		DATE(tp.created_at$) AS sampleprep_date,
		con.barcode AS tissue_prep_fluidx_id,
		loc.name AS tube_location,
		CASE
			WHEN con.archive_purpose$ IN ('Retired', 'Expended') THEN 0 -- Retired or expended tissue preps have a weight of 0
			WHEN loc.name = 'SciOps ToL Lab' THEN 0 -- Tissue preps sent to LRES have a weight of 0
			ELSE con.volume_si * 1000000 
		END AS weight_mg,
		tpr.downstream_protocol,
		NULL::varchar AS disruption_method,
		tube.tissue_prep_type,
		tube.sciops_protocol_required,
		t.lab_work_category AS labwork_category_sts,
		tp.bt_id AS tissue_prep_bnt_id
	FROM tissue_prep$raw AS tp
	LEFT JOIN tissue$raw AS t
		ON tp.tissue = t.id
	LEFT JOIN container_content$raw AS cc 
		ON tp.id = cc.entity_id
	LEFT JOIN sample_prep_weight_measurements$raw AS tpr
		ON tp.id = tpr.tissue_prep
	LEFT JOIN container$raw AS con
		ON cc.container_id = con.id
	LEFT JOIN tube$raw AS tube
		ON con.id = tube.id
	LEFT JOIN location$raw AS loc
		ON tube.location_id$ = loc.id
	LEFT JOIN project$raw AS proj
		ON tp.project_id$ = proj.id
	LEFT JOIN folder$raw AS f
		ON t.folder_id$ = f.id
	WHERE tp.bt_id IS NOT NULL
		AND proj.name = 'ToL Core Lab'
		AND f.name IN ('Core Lab Entities', 'Routine Throughput', 'Benchling MS Project Move', 'ToL Core Restricted Entities')
		AND (tp.archive_purpose$ != ('Made in error') OR tp.archive_purpose$ IS NULL)
		AND (con.archive_purpose$ != ('Made in error') OR con.archive_purpose$ IS NULL)
		
)
SELECT *
FROM tissue_preps
UNION
SELECT *
FROM legacy_tissue_preps;