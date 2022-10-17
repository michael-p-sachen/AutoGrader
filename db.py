import dataclasses
import houston_client
import sgqlc.operation

from typing import Optional
from .. import operations


@dataclasses.dataclass
class PantSimilarityProperties:
    fabric_uuid: str
    style_uuid: str
    softness: str
    body_shape: str


def _tag_name_by_tag_group(tags, group_name):
    for tag_dict in tags:
        tag = tag_dict.get('tag', {})
        if tag.get('taggroup', {}).get('name') == group_name:
            return tag.get('name')

    return None


def _query_result_to_similarity_properties(result: dict) -> PantSimilarityProperties:
    scan_tags = result.get('scan', {}).get('scantags', [])
    return PantSimilarityProperties(
        style_uuid=result.get('style_uuid'),
        fabric_uuid=result.get('wash', {}).get('fabric_uuid'),
        softness=_tag_name_by_tag_group(scan_tags, 'softness'),
        body_shape=_tag_name_by_tag_group(scan_tags, 'body shape')
    )


def _query_result_to_browzwear_file_contents(result: dict) -> Optional[str]:
    try:
        # BW file
        pants_files = result.get('pant', {}).get('pants_files', [])[0]
        bw_file_uuid = pants_files[0]['file']['uuid']
    except (IndexError, KeyError):
        return None
    else:
        response = operations.juno_client.files.get(bw_file_uuid) or {}
        return response.get('data', {}).get('data')


def get_similarity_properties(pant_serial) -> Optional[PantSimilarityProperties]:
    op = sgqlc.operation.Operation(houston_client.client_schema.query_root)
    pantsruns = op.pants(where={'serial': {'_eq': pant_serial}}).pantsruns
    pantsruns.__fields__('style_uuid')
    pantsruns.wash.__fields__('fabric_uuid')
    pantsruns.scan.scan_tags.tag.__fields__('name')
    pantsruns.scan.scan_tags.tag.taggroup.__fields__('name')
    query_results = operations.houston_endpoint(op)

    pantsrun_dicts = query_results.get('data', {}).get('pants', {}).get('pantsruns', [])
    for pantsrun_dict in pantsrun_dicts:
        if pantsrun_dict.get('active'):
            return _query_result_to_similarity_properties(pantsrun_dict)

    return None


def get_healed_mesh(pant_serial) -> Optional[str]:
    op = sgqlc.operation.Operation(houston_client.client_schema.query_root)
    pantsruns = op.pants(where={'serial': {'_eq': pant_serial}}).pantsruns
    pantsruns.scan.__fields__('healed_file_uuid')
    query_result = operations.houston_endpoint(op)
    pantsruns = query_result.get('data', {}).get('pantsruns', [])
    if not pantsruns:
        return None

    file_uuid = pantsruns[0].get('scan', {}).get('healed_file_uuid')
    if not file_uuid:
        return None

    file_response = operations.juno_client.files.get(file_uuid)
    return file_response.get('data')


def find_similar_pants(similarity_properties: PantSimilarityProperties) -> Optional[str]:
    op = sgqlc.operation.Operation(houston_client.client_schema.query_root)
    query = {
        'active': {'_eq': True},
        'wash': {'fabric': {'uuid': {'_eq': similarity_properties.fabric_uuid}}},
        'style': {'uuid': {'_eq': similarity_properties.style_uuid}},
        'scan': {'tags': {'tag': {'name': {'_eq': similarity_properties.softness}}}}
    }
    pantsruns = op.pantsrun(where=query)
    pantsruns.pant.pants_files(
        where={'category': {'_eq': 'bw save'}}
    ).file.__fields__('uuid', 'blob', 'bucket')
    pantsruns.scan.scan_tags.tag.__fields__('name')
    pantsruns.scan.scan_tags.tag.taggroup.__fields__('name')
    query_results = operations.houston_endpoint(op)

    # Filter query results to those with the requested body shape.
    pantsruns_with_right_shape = []
    pantsrun_dicts = query_results.get('data', {}).get('pantsruns', [])
    for pantsrun_dict in pantsrun_dicts:
        scan_tags = pantsrun_dict.get('scan', {}).get('scantags', [])
        body_shape = _tag_name_by_tag_group(scan_tags, 'body shape')
        if body_shape == similarity_properties.body_shape:
            pantsruns_with_right_shape.append(pantsrun_dict)

    # Return the first pair of similar pants we can find
    # that has a healed scan and browzwear file associated with it.
    for pantsrun in pantsruns_with_right_shape:
        browzwear_file_contents = _query_result_to_browzwear_file_contents(pantsrun)
        if browzwear_file_contents:
            return browzwear_file_contents

    return None
