# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sciops.messages import CreateLabwareMessage, LabwareMessage, UpdateLabwareMessage


class MessageBuilder:
    """ Build up various message types for sending to MQ """

    def __init__(self):
        pass

    @classmethod
    def build_labware_message(cls, message: LabwareMessage):
        if isinstance(message, CreateLabwareMessage):
            return cls._build_create_labware_message(message)
        elif isinstance(message, UpdateLabwareMessage):
            return cls._build_update_labware_message(message)
        else:
            raise TypeError('Unknown message type provided')

    @staticmethod
    def _build_create_labware_message(message: CreateLabwareMessage) -> dict:
        """ Build a create_labware message """
        output = {}
        labware_dict = {}
        samples = []
        for sample in message.samples:
            sample_dict = {}
            sample_dict.update(
                {} if sample.sample_uuid is None else {'sampleUuid': sample.sample_uuid.encode()})
            sample_dict.update(
                {} if sample.study_uuid is None else {'studyUuid': sample.study_uuid.encode()})
            sample_dict.update(
                {} if sample.sanger_sample_id is None else {
                    'sangerSampleId': sample.sanger_sample_id})
            sample_dict.update(
                {} if sample.location is None else {'location': sample.location})
            sample_dict.update(
                {} if sample.supplier_sample_name is None else {
                    'supplierSampleName': sample.supplier_sample_name})
            sample_dict.update({} if sample.volume is None else {'volume': sample.volume})
            sample_dict.update(
                {} if sample.concentration is None else {'concentration': sample.concentration})
            sample_dict.update(
                {} if sample.public_name is None else {'publicName': sample.public_name})
            sample_dict.update({} if sample.taxon_id is None else {'taxonId': sample.taxon_id})
            sample_dict.update(
                {} if sample.common_name is None else {'commonName': sample.common_name})
            sample_dict.update(
                {} if sample.donor_id is None else {'donorId': sample.donor_id})
            sample_dict.update(
                {} if sample.library_type is None else {'libraryType': sample.library_type})
            sample_dict.update(
                {} if sample.country_of_origin is None else {
                    'countryOfOrigin': sample.country_of_origin})
            sample_dict.update({} if sample.sample_collection_date_utc is None else {
                'sampleCollectionDateUtc': sample.sample_collection_date_utc.timestamp() * 1000})
            sample_dict.update(
                {} if sample.cost_code is None else {'costCode': sample.cost_code})
            sample_dict.update(
                {} if sample.genome_size is None else {'genomeSize': sample.genome_size})
            sample_dict.update(
                {} if sample.accession_number is None else {
                    'accessionNumber': sample.accession_number})
            sample_dict.update(
                {} if sample.sheared_femto_fragment_size is None else {
                    'shearedFemtoFragmentSize': sample.sheared_femto_fragment_size})
            sample_dict.update(
                {} if sample.post_spri_concentration is None else {
                    'postSPRIConcentration': sample.post_spri_concentration})
            sample_dict.update(
                {} if sample.post_spri_volume is None else {
                    'postSPRIVolume': sample.post_spri_volume})
            sample_dict.update(
                {} if sample.final_nano_drop_280 is None else {
                    'finalNanoDrop280': sample.final_nano_drop_280})
            sample_dict.update(
                {} if sample.final_nano_drop_230 is None else {
                    'finalNanoDrop230': sample.final_nano_drop_230})
            sample_dict.update(
                {} if sample.final_nano_drop is None else {
                    'finalNanoDrop': sample.final_nano_drop})
            sample_dict.update(
                {} if sample.shearing_and_qc_comments is None else {
                    'shearingAndQCComments': sample.shearing_and_qc_comments})
            sample_dict.update(
                {} if sample.date_submitted_utc is None else {
                    'dateSubmittedUTC': sample.date_submitted_utc.timestamp() * 1000})
            sample_dict.update(
                {} if sample.priority_level is None else {
                    'priorityLevel': sample.priority_level})
            sample_dict.update(
                {} if sample.date_required_by is None else {
                    'dateRequiredBy': sample.date_required_by})
            sample_dict.update(
                {} if sample.reason_for_priority is None else {
                    'reasonForPriority': sample.reason_for_priority})
            samples.append(sample_dict)
        labware_dict.update(
            {} if message.labware_type is None else {'labwareType': message.labware_type})
        labware_dict.update(
            {} if message.labware_uuid is None else {'labwareUuid': message.labware_uuid.encode()})
        labware_dict.update({} if message.barcode is None else {'barcode': message.barcode})
        labware_dict['samples'] = samples
        output.update(
            {} if message.message_uuid is None else {'messageUuid': message.message_uuid.encode()})
        output.update({} if message.message_create_date_utc is None else {
            'messageCreateDateUtc': message.message_create_date_utc.timestamp() * 1000})
        output['labware'] = labware_dict
        return output

    @staticmethod
    def _build_update_labware_message(message: UpdateLabwareMessage) -> dict:
        """ Build a update_labware message """
        output = {}
        labware_updates = []
        sample_updates = []
        for upd in message.labware_updates:
            labware_updates_dict = {}
            labware_updates_dict.update(
                {} if upd.uuid is None else {'labwareUuid': upd.uuid.encode()})
            labware_updates_dict.update({} if upd.name is None else {'name': upd.name})
            labware_updates_dict.update({} if upd.value is None else {'value': upd.value})
            labware_updates.append(labware_updates_dict)
        for upd in message.sample_updates:
            sample_updates_dict = {}
            sample_updates_dict.update(
                {} if upd.uuid is None else {'sampleUuid': upd.uuid.encode()})
            sample_updates_dict.update({} if upd.name is None else {'name': upd.name})
            sample_updates_dict.update({} if upd.value is None else {'value': upd.value})
            sample_updates.append(sample_updates_dict)
        output.update(
            {} if message.message_uuid is None else {'messageUuid': message.message_uuid.encode()})
        output.update({} if message.message_create_date_utc is None else {
            'messageCreateDateUtc': message.message_create_date_utc.timestamp() * 1000})
        output['labwareUpdates'] = labware_updates
        output['sampleUpdates'] = sample_updates
        return output
