"""Durable operation orchestration; adapters own only vendor contracts."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Artifact:
    """Exactly one inline byte result or private HTTPS URL, keyed by declared output."""
    inline: Optional[bytes] = None
    url: Optional[str] = None


@dataclass
class Result:
    """Adapter result. data is private typed JSON; raw evidence is never public."""
    status: str
    task_id: Optional[str] = None
    data_type: Optional[str] = None
    data: dict = field(default_factory=dict)
    artifacts: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)

from contextlib import contextmanager
import math
import os
from pathlib import Path
import secrets
import stat
import time
from . import artifacts as media
from .http import Transport, TransportError
from .request import (ARTIFACT_LIMIT, JSON_LIMIT, HASH,
                      canonical, check_root, fail, get_adapter, identifier, integer,
                      object_fields, parent_fd, prepare_request, prepare_value,
                      read_file, redact, relative_path, sha256, state_path,
                      strict_json, task_id, verify_fresh)

STATES = {'prepared','submitting','submission_unknown','pending','generated','completed',
          'collected','failed','cancelled','expired','banned','unsupported_provider_result'}
RESULT_STATES = STATES - {'prepared','submitting','submission_unknown','collected'}
REVIEW = {'creative_approval':'pending','engine_import':'pending','asset_audit':'pending'}


def _relative(id,name):
    identifier(id)
    return '.ccgs-assets/jobs/'+id+'/'+name


def write_private_bytes(root,path,raw,*,exclusive=False):
    """0600 file + fsync + atomic replacement; use no-follow dirfd paths throughout."""
    if not isinstance(path, str) or not path.startswith(".ccgs-assets/"):
        fail("private_write_must_be_under_ccgs_assets")
    with parent_fd(root,path,create=True,mode=0o700,private=True) as (fd,name):
        if exclusive:
            try:
                file_fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
            except FileExistsError:
                if read_file(root,path,len(raw),private=True)!=raw: fail('private_file_collision')
                return
            with os.fdopen(file_fd,'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.fsync(fd)
            return
        try:
            existing=os.stat(name,dir_fd=fd,follow_symlinks=False)
            if not stat.S_ISREG(existing.st_mode) or stat.S_IMODE(existing.st_mode)&0o077:
                fail('unsafe_private_file')
        except FileNotFoundError:
            pass
        temporary='atomic-'+secrets.token_hex(16)
        file_fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        try:
            with os.fdopen(file_fd,'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary,name,src_dir_fd=fd,dst_dir_fd=fd)
            os.fsync(fd)
        finally:
            try: os.unlink(temporary,dir_fd=fd)
            except FileNotFoundError: pass


def write_private_json(root,path,value,*,exclusive=False):
    raw=canonical(value)
    if len(raw)>JSON_LIMIT: fail('private_json_size_limit')
    write_private_bytes(root,path,raw,exclusive=exclusive)


# Compatibility aliases for existing asset orchestration internals.
_private_bytes = write_private_bytes
_private_json = write_private_json


@contextmanager
def private_lock(root,state_dir,path):
    """Own one project-private lock path; stale locks require explicit inspection."""
    root=check_root(root); state_path(root,state_dir)
    if not isinstance(path,str) or not path.startswith('.ccgs-assets/') or not path.endswith('/lock'):
        fail('invalid_private_lock_path')
    token=secrets.token_hex(32)
    with parent_fd(root,path,create=True,mode=0o700,private=True) as (fd,name):
        try:
            lock_fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        except FileExistsError:
            fail('operation_locked: inspect the owner and any stale lock explicitly')
        with os.fdopen(lock_fd,'wb') as stream:
            stream.write(token.encode()); stream.flush(); os.fsync(stream.fileno())
        owned=os.stat(name,dir_fd=fd,follow_symlinks=False)
        os.fsync(fd)
        try:
            yield
        finally:
            try:
                current=os.stat(name,dir_fd=fd,follow_symlinks=False)
                if os.path.samestat(owned,current) and read_file(root,path,128,private=True)==token.encode():
                    os.unlink(name,dir_fd=fd); os.fsync(fd)
            except (FileNotFoundError,ValueError):
                pass


@contextmanager
def operation_lock(root,state_dir,id):
    """Backward-compatible asset job lock using the shared private lock primitive."""
    identifier(id)
    with private_lock(root,state_dir,_relative(id,'lock')):
        yield


def save_receipt(root,state_dir,id,receipt):
    state_path(root,state_dir)
    _private_json(root,_relative(id,'receipt.json'),receipt)


def _summary(receipt,**extra):
    fields=('schema_version','id','provider','operation','asset_id','standalone','request_sha256',
            'status','task_id','data_type','diagnostic','published','review')
    result={key:receipt[key] for key in fields}
    if receipt['status'] in ('submitting','submission_unknown'):
        result['status']='submission_unknown'
        result['next']='Inspect provider history/support; automatic resubmission is blocked.'
    if receipt['status']=='unsupported_provider_result':
        result['next']='Private provider evidence retained; inspect result compatibility and resume the same task if available.'
    result.update(extra)
    return redact(result)


def _new_receipt(id,plan):
    value=plan['request']
    return {'schema_version':1,'id':id,'provider':value['provider'],'operation':value['operation'],
            'asset_id':value['asset_id'],'standalone':value['standalone'],
            'request_sha256':plan['request_sha256'],'plan_sha256':sha256(canonical(plan)),
            'status':'prepared','task_id':None,'data_type':None,'result_sha256':None,
            'staged':{},'published':{},'diagnostic':None,'review':dict(REVIEW)}


def _receipt_exists(root,id):
    path=Path(root)/_relative(id,'receipt.json')
    return path.exists() or path.is_symlink()


def _validate_receipt(receipt,id,plan):
    object_fields(receipt,tuple(_new_receipt(id,plan)))
    expected=_new_receipt(id,plan)
    for key in ('schema_version','id','provider','operation','asset_id','standalone','request_sha256','plan_sha256','review'):
        if receipt[key]!=expected[key] or type(receipt[key]) is not type(expected[key]): fail('receipt_identity_or_plan_corrupt')
    if receipt['status'] not in STATES: fail('receipt_status_corrupt')
    diagnostic = receipt['diagnostic']
    if diagnostic is not None:
        if diagnostic == {'category': 'submission_response_unavailable'}:
            pass
        elif isinstance(diagnostic, dict) and set(diagnostic) == {'category', 'http_status'} and diagnostic['category'] == 'provider_http_error':
            integer(diagnostic['http_status'], 300, 599)
        else:
            fail('receipt_diagnostic_corrupt')
    if receipt['task_id'] is not None: task_id(receipt['task_id'])
    if receipt['result_sha256'] is not None and (not isinstance(receipt['result_sha256'],str) or not HASH.fullmatch(receipt['result_sha256'])): fail('receipt_result_hash_corrupt')
    outputs={out['key']:out for out in plan['request']['outputs']}
    for key in ('staged','published'):
        if not isinstance(receipt[key],dict) or set(receipt[key])-outputs.keys(): fail('receipt_outputs_corrupt')
    for key,item in receipt['staged'].items():
        object_fields(item,('file','sha256','size','format'),('width','height','version'))
        if not isinstance(item['sha256'],str) or not HASH.fullmatch(item['sha256']): fail('receipt_artifact_hash_corrupt')
        if item['file']!='stage-'+key+'-'+item['sha256']+'.bin': fail('receipt_staging_path_corrupt')
        integer(item['size'],1,ARTIFACT_LIMIT)
        if item['format']!=outputs[key]['format']: fail('receipt_artifact_format_corrupt')
        for dim in ('width','height'):
            if dim in outputs[key] and item.get(dim)!=outputs[key][dim]: fail('receipt_artifact_dimensions_corrupt')
    for key,item in receipt['published'].items():
        object_fields(item,('path','sha256','size'))
        if key not in receipt['staged'] or item!={k:(outputs[key]['path'] if k=='path' else receipt['staged'][key][k]) for k in ('path','sha256','size')}: fail('receipt_publication_corrupt')
    if receipt['status']=='collected' and set(receipt['published'])!=set(outputs): fail('receipt_incomplete_collection')


def _serialize_result(root,id,plan,result,previous):
    if not isinstance(result,Result) or result.status not in RESULT_STATES: fail('invalid_adapter_result')
    if result.task_id is not None: task_id(result.task_id)
    adapter=get_adapter(plan['request']['provider']) if plan['request']['provider']=='pixellab' else None
    if adapter: adapter.validate_data(plan['request']['operation'],result.data_type,result.data)
    entries={}
    expected={out['key'] for out in plan['request']['outputs']}
    if result.status=='generated' and set(result.artifacts)!=expected: fail('adapter_output_keys_mismatch')
    if result.status=='completed' and result.artifacts: fail('nonmedia_result_has_artifacts')
    for key,value in result.artifacts.items():
        if key not in expected or not isinstance(value,Artifact) or (value.inline is None)==(value.url is None): fail('invalid_adapter_artifact')
        identifier(key)
        if value.inline is not None:
            if not isinstance(value.inline,bytes) or not 0<len(value.inline)<=ARTIFACT_LIMIT: fail('artifact_byte_limit')
            digest=sha256(value.inline); filename='inline-'+key+'-'+digest+'.bin'
            _private_bytes(root,_relative(id,filename),value.inline,exclusive=True)
            entries[key]={'kind':'inline','file':filename,'sha256':digest,'size':len(value.inline)}
        else:
            Transport()._validate_url(value.url)
            entries[key]={'kind':'url','url':value.url}
    value={'schema_version':1,'request_sha256':plan['request_sha256'],'previous_sha256':previous,
           'status':result.status,'task_id':result.task_id,'data_type':result.data_type,
           'data':result.data,'artifacts':entries,'evidence':result.evidence}
    return value


def _load_result(root,id,plan,receipt,adapter):
    path=Path(root)/_relative(id,'result.json')
    if not path.exists() and not path.is_symlink():
        if receipt['result_sha256'] is not None: fail('receipt_result_missing')
        return None
    raw=read_file(root,_relative(id,'result.json'),JSON_LIMIT,private=True)
    value=strict_json(raw,JSON_LIMIT)
    object_fields(value,('schema_version','request_sha256','previous_sha256','status','task_id','data_type','data','artifacts','evidence'))
    digest=sha256(raw)
    if type(value['schema_version']) is not int or value['schema_version']!=1 or value['request_sha256']!=plan['request_sha256'] or value['status'] not in RESULT_STATES:
        fail('private_result_corrupt')
    if digest!=receipt['result_sha256'] and value['previous_sha256']!=receipt['result_sha256']:
        fail('private_result_chain_corrupt')
    if value['task_id'] is not None: task_id(value['task_id'])
    if receipt['task_id'] is not None and value['task_id']!=receipt['task_id']: fail('provider_task_changed')
    adapter.validate_data(plan['request']['operation'],value['data_type'],value['data'])
    outputs={out['key'] for out in plan['request']['outputs']}
    if not isinstance(value['artifacts'],dict) or set(value['artifacts'])-outputs: fail('private_result_artifacts_corrupt')
    if value['status']=='generated' and set(value['artifacts'])!=outputs: fail('private_result_artifact_missing')
    for key,item in value['artifacts'].items():
        if not isinstance(item,dict): fail('private_result_artifacts_corrupt')
        if item.get('kind')=='inline':
            object_fields(item,('kind','file','sha256','size'))
            if not isinstance(item['sha256'],str) or not HASH.fullmatch(item['sha256']) or item['file']!='inline-'+key+'-'+item['sha256']+'.bin': fail('private_inline_path_corrupt')
            integer(item['size'],1,ARTIFACT_LIMIT)
            data=read_file(root,_relative(id,item['file']),ARTIFACT_LIMIT,private=True)
            if len(data)!=item['size'] or sha256(data)!=item['sha256']: fail('private_inline_corrupt')
        elif item.get('kind')=='url':
            object_fields(item,('kind','url')); Transport()._validate_url(item['url'])
        else: fail('private_artifact_kind_corrupt')
    # A complete atomic result may precede its receipt pointer by one crash interval.
    if digest!=receipt['result_sha256']:
        if receipt['status']=='collected': fail('unexpected_result_after_collection')
        receipt.update(status=value['status'],task_id=value['task_id'],data_type=value['data_type'],result_sha256=digest)
    return value


def load_operation(root,state_dir,id,*,adapters=None):
    """Validate private receipt, full plan/source hash association and durable result; read-only."""
    root=check_root(root); state_path(root,state_dir); identifier(id)
    plan=strict_json(read_file(root,_relative(id,'plan.json'),JSON_LIMIT,private=True),JSON_LIMIT)
    object_fields(plan,('schema_version','request','inputs','dependencies','request_sha256'))
    local = isinstance(plan['request'], dict) and plan['request'].get('provider') == 'local'
    if local:
        value = plan['request']
        if value.get('operation') != 'ingest' or not isinstance(value.get('source_files'), list) or len(value['source_files']) != 1 or not isinstance(value.get('outputs'), list) or len(value['outputs']) != 1:
            fail('invalid_ingestion_plan')
        fresh, _, _ = _ingestion_plan(root, value['source_files'][0], value['outputs'][0]['path'], value['asset_id'])
    else:
        fresh=prepare_value(root,state_dir,plan['request'],adapters=adapters)
    if fresh!=plan: fail('source_or_dependency_changed_since_submission')
    receipt=strict_json(read_file(root,_relative(id,'receipt.json'),JSON_LIMIT,private=True),JSON_LIMIT)
    _validate_receipt(receipt,id,plan)
    adapter=_IngestAdapter() if local else get_adapter(plan['request']['provider'],adapters)
    result=_load_result(root,id,plan,receipt,adapter)
    if receipt['status']=='submitting' and result is None: receipt['status']='submission_unknown'
    return {'plan':plan,'receipt':receipt,'result':result}


def load_dependency(root,state_dir,id,*,adapters=None):
    operation=load_operation(root,state_dir,identifier(id),adapters=adapters)
    receipt=operation['receipt']
    if receipt['status'] not in ('completed','generated','collected') or operation['result'] is None:
        fail('dependency_not_successful')
    pin={key:receipt[key] for key in ('id','provider','operation','request_sha256','result_sha256','task_id','data_type')}
    return dict(operation,pin=pin)


def _dependencies(root,state_dir,plan,adapters):
    result={}
    for pin in plan['dependencies']:
        loaded=load_dependency(root,state_dir,pin['id'],adapters=adapters)
        if loaded['pin']!=pin: fail('dependency_changed_since_plan')
        result[pin['id']]=loaded
    return result


def _credential(adapter):
    value=os.environ.get(adapter.credential_env)
    if not value: fail('provider_credential_unavailable: set '+adapter.credential_env)
    return value


def _scrub_evidence(value, credential):
    """Preserve private result evidence while discarding echoed API authorization."""
    if isinstance(value, dict):
        secret_keys = {'authorization', 'api_key', 'apikey', 'secret', 'access_token'}
        return {key: ('[redacted]' if key.lower() in secret_keys else _scrub_evidence(item, credential))
                for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub_evidence(item, credential) for item in value]
    if isinstance(value, str) and credential:
        return value.replace(credential, '[redacted]')
    return value


def _persist_result(root,state_dir,id,plan,receipt,result,adapter):
    adapter.validate_data(plan['request']['operation'],result.data_type,result.data)
    result.evidence = _scrub_evidence(result.evidence, os.environ.get(adapter.credential_env))
    value=_serialize_result(root,id,plan,result,receipt['result_sha256'])
    _private_json(root,_relative(id,'result.json'),value)
    receipt.update(status=result.status,task_id=result.task_id,data_type=result.data_type,result_sha256=sha256(canonical(value)))
    save_receipt(root,state_dir,id,receipt)


def submit(root,state_dir,request_path,id,*,write=False,transport=None,adapters=None):
    """Submit one journaled operation only with write=True. Identical IDs never POST twice."""
    identifier(id)
    plan=prepare_request(root,state_dir,request_path,adapters=adapters)
    if _receipt_exists(root,id):
        existing=load_operation(root,state_dir,id,adapters=adapters)
        if existing['plan']['request_sha256']!=plan['request_sha256']: fail('operation_request_hash_conflict')
        return _summary(existing['receipt'])
    media.preflight(root,plan['request']['outputs'])
    if not write: return redact(dict(plan,effect='preview_only; one explicit provider submission on --write'))
    adapter=get_adapter(plan['request']['provider'],adapters)
    credential=_credential(adapter); transport=transport or Transport()
    with operation_lock(root,state_dir,id):
        if _receipt_exists(root,id):
            existing=load_operation(root,state_dir,id,adapters=adapters)
            if existing['plan']['request_sha256']!=plan['request_sha256']: fail('operation_request_hash_conflict')
            return _summary(existing['receipt'])
        verify_fresh(root,plan)
        media.preflight(root,plan['request']['outputs'])
        media.link_capability(root,state_dir,plan['request']['outputs'])
        dependencies=_dependencies(root,state_dir,plan,adapters)
        end=time.monotonic()+120
        adapter.validate_dependencies(plan,dependencies,transport,credential=credential,deadline=end)
        verify_fresh(root,plan)
        _private_json(root,_relative(id,'plan.json'),plan,exclusive=True)
        receipt=_new_receipt(id,plan)
        save_receipt(root,state_dir,id,receipt)
        receipt['status']='submitting'
        save_receipt(root,state_dir,id,receipt)  # Intent precedes every possibly billable byte.
        try:
            result=adapter.submit(root,plan,dependencies,transport,credential=credential,deadline=end)
        except (ValueError,OSError) as error:
            receipt['diagnostic'] = ({'category': 'provider_http_error', 'http_status': error.status}
                                     if isinstance(error, TransportError) and error.status is not None
                                     else {'category': 'submission_response_unavailable'})
            # HTTP errors or incomplete parsing do not prove the provider did no work.
            receipt['status']='submission_unknown'
            save_receipt(root,state_dir,id,receipt)
            return _summary(receipt)
        # Persistence failures must not replace an already durable result with unknown.
        _persist_result(root,state_dir,id,plan,receipt,result,adapter)
        return _summary(receipt)


def status(root,state_dir,id,*,transport=None,adapters=None):
    """Inspect local/remote state without a lock or any state write."""
    op=load_operation(root,state_dir,id,adapters=adapters)
    receipt=op['receipt']
    if receipt['task_id'] and receipt['status'] in ('pending','unsupported_provider_result'):
        adapter=get_adapter(receipt['provider'],adapters)
        try:
            remote=adapter.poll(op['plan'],receipt['task_id'],transport or Transport(),credential=_credential(adapter),deadline=time.monotonic()+30)
            return _summary(receipt,remote_status=remote.status)
        except ValueError:
            return _summary(receipt,remote_inspection='unavailable: credential, network or provider contract')
    return _summary(receipt)


def resume(root,state_dir,id,*,write=False,wait_seconds=120,transport=None,adapters=None):
    """Poll a known remote task. Zero means one check; no path can submit."""
    if type(wait_seconds) not in (int,float) or not math.isfinite(wait_seconds) or not 0<=wait_seconds<=600:
        fail('invalid_wait_seconds')
    op=load_operation(root,state_dir,id,adapters=adapters)
    if not write: return _summary(op['receipt'],effect='preview_only; poll known task on --write')
    with operation_lock(root,state_dir,id):
        op=load_operation(root,state_dir,id,adapters=adapters)
        receipt=op['receipt']; plan=op['plan']
        refresh_urls = (receipt['status'] == 'generated' and op['result'] is not None
                        and any(item['kind'] == 'url' for item in op['result']['artifacts'].values()))
        if (receipt['status'] not in ('pending','unsupported_provider_result') and not refresh_urls) or not receipt['task_id']:
            save_receipt(root,state_dir,id,receipt)
            return _summary(receipt)
        adapter=get_adapter(receipt['provider'],adapters); credential=_credential(adapter)
        end=time.monotonic()+(wait_seconds if wait_seconds else 30)
        while True:
            verify_fresh(root,plan)
            try:
                result=adapter.poll(plan,receipt['task_id'],transport or Transport(),credential=credential,deadline=end)
            except TransportError as error:
                return _summary(receipt,local_wait='deadline_exhausted' if error.category=='deadline_exhausted' else error.category)
            if result.task_id!=receipt['task_id']: fail('provider_task_changed')
            _persist_result(root,state_dir,id,plan,receipt,result,adapter)
            if receipt['status']!='pending' or not wait_seconds: return _summary(receipt)
            remaining=end-time.monotonic()
            if remaining<=0: return _summary(receipt,local_wait='deadline_exhausted')
            time.sleep(min(5,remaining))
            if time.monotonic()>=end: return _summary(receipt,local_wait='deadline_exhausted')


def _stage_path(root,id,item):
    return Path(root)/_relative(id,item['file'])


def _collect(root,state_dir,id,plan,receipt,result,adapter,transport):
    outputs=plan['request']['outputs']
    def owned(out):
        item=receipt['staged'].get(out['key'])
        return bool(item and media.prove_owned(root,out['path'],_stage_path(root,id,item),item['sha256']))
    media.preflight(root,outputs,allow_owned=owned)
    if receipt['status']=='collected':
        if not all(owned(out) for out in outputs):
            fail('collected_output_missing_or_changed')
        return _summary(receipt)
    if receipt['status'] not in ('generated','completed'): fail('operation_has_no_collectable_result')
    if not outputs: return _summary(receipt)
    media.link_capability(root,state_dir,outputs)
    for out in outputs:
        key=out['key']
        if key in receipt['staged']:
            item=receipt['staged'][key]
            raw=read_file(root,_relative(id,item['file']),ARTIFACT_LIMIT,private=True)
            if sha256(raw)!=item['sha256']: fail('staged_artifact_changed')
        else:
            entry=result['artifacts'].get(key)
            if entry is None:
                if out['format']!='json': fail('missing_provider_artifact')
                raw=canonical(result['data'])
            elif entry['kind']=='inline':
                raw=read_file(root,_relative(id,entry['file']),ARTIFACT_LIMIT,private=True)
            else:
                raw=transport.download(entry['url'],deadline=time.monotonic()+30)
            metadata=media.validate_content(raw,out,json_validator=lambda data:adapter.validate_json(plan['request']['operation'],data))
            filename='stage-'+key+'-'+metadata['sha256']+'.bin'
            _private_bytes(root,_relative(id,filename),raw,exclusive=True)
            receipt['staged'][key]=dict(metadata,file=filename)
            save_receipt(root,state_dir,id,receipt)  # Retain inode and hash before any public link.
        media.validate_content(raw,out,json_validator=lambda data:adapter.validate_json(plan['request']['operation'],data))
    verify_fresh(root,plan)
    media.preflight(root,outputs,allow_owned=owned)
    collection_status = receipt['status']
    try:
        for out in outputs:
            key=out['key']; item=receipt['staged'][key]
            media.publish(root,out['path'],_stage_path(root,id,item),item['sha256'])
            receipt['published'][key]={'path':out['path'],'sha256':item['sha256'],'size':item['size']}
            save_receipt(root,state_dir,id,receipt)
        verify_fresh(root,plan)
        for out in outputs:
            if not owned(out): fail('published_artifact_changed')
        receipt['status']='collected'; save_receipt(root,state_dir,id,receipt)
    except (ValueError,OSError):
        # Retain every public target: proof followed by unlink cannot exclude edits.
        # Keep committed publication entries and all staging, including the
        # link-before-receipt interval that the next collection can reconcile.
        receipt['status'] = collection_status
        save_receipt(root,state_dir,id,receipt)
        raise
    return _summary(receipt)


def collect(root,state_dir,id,*,write=False,transport=None,adapters=None):
    """Validate all declared artifacts, then publish each via an owned create-only hard link."""
    op=load_operation(root,state_dir,id,adapters=adapters)
    if not write: return _summary(op['receipt'],effect='preview_only; validate and publish declared outputs on --write')
    with operation_lock(root,state_dir,id):
        op=load_operation(root,state_dir,id,adapters=adapters)
        return _collect(root,state_dir,id,op['plan'],op['receipt'],op['result'],
                        _IngestAdapter() if op['receipt']['provider']=='local' else get_adapter(op['receipt']['provider'],adapters),transport or Transport())


class _IngestAdapter:
    def validate_data(self,operation,data_type,data):
        fail('ingestion_has_no_remote_result')
    def validate_json(self,operation,data): fail('untyped_json_ingestion_unsupported')


def _ingestion_plan(root,source,output,asset_id):
    identifier(asset_id)
    raw=read_file(root,source,ARTIFACT_LIMIT)
    extension=Path(source).suffix.lower()
    format_name={'.png':'png','.jpg':'jpeg','.jpeg':'jpeg','.glb':'glb'}.get(extension)
    if format_name is None: fail('unsupported_ingestion_format')
    relative_path(output,output=True)
    if Path(output).suffix.lower() not in ({'jpeg':['.jpg','.jpeg']}.get(format_name,['.'+format_name])): fail('output_suffix_mismatch')
    metadata=media.validate_content(raw,{'format':format_name})
    out={'key':'artifact','path':output,'format':format_name}
    for key in ('width','height'):
        if key in metadata: out[key]=metadata[key]
    value={'schema_version':1,'provider':'local','operation':'ingest','asset_id':asset_id,
           'standalone':True,'source_files':[source],'parameters':{},'outputs':[out]}
    plan={'schema_version':1,'request':value,'inputs':[{'path':source,'kind':'artifact','sha256':sha256(raw),'size':len(raw)}],'dependencies':[]}
    plan['request_sha256']=sha256(canonical(plan))
    return plan, metadata, raw


def ingest(root,state_dir,source,output,asset_id,*,write=False):
    """Stage a decoded native/manual artifact with an owned ingestion receipt; no engine import."""
    root=check_root(root); state_path(root,state_dir)
    plan,metadata,raw=_ingestion_plan(root,source,output,asset_id)
    out=plan['request']['outputs'][0]
    id='ingest-'+plan['request_sha256'][:32]
    receipt=_new_receipt(id,plan)
    if _receipt_exists(root,id):
        old_plan=strict_json(read_file(root,_relative(id,'plan.json'),JSON_LIMIT,private=True),JSON_LIMIT)
        if old_plan!=plan: fail('ingestion_source_changed')
        receipt=strict_json(read_file(root,_relative(id,'receipt.json'),JSON_LIMIT,private=True),JSON_LIMIT)
        _validate_receipt(receipt,id,plan)
    def owned(out):
        item=receipt['staged'].get('artifact')
        return bool(item and media.prove_owned(root,output,_stage_path(root,id,item),item['sha256']))
    media.preflight(root,[out],allow_owned=owned)
    if not write: return _summary(receipt,effect='preview_only; copy verified local artifact on --write')
    with operation_lock(root,state_dir,id):
        media.preflight(root,[out],allow_owned=owned)
        media.link_capability(root,state_dir,[out])
        _private_json(root,_relative(id,'plan.json'),plan,exclusive=True)
        filename='stage-artifact-'+metadata['sha256']+'.bin'
        _private_bytes(root,_relative(id,filename),raw,exclusive=True)
        receipt['staged']={'artifact':dict(metadata,file=filename)}
        if receipt['status']!='collected': receipt['status']='generated'
        save_receipt(root,state_dir,id,receipt)
        # All bytes already decoded/staged; native ingestion does not synthesize a remote result.
        return _collect(root,state_dir,id,plan,receipt,{'artifacts':{}},_IngestAdapter(),Transport())
