"""PixelLab V2 narrow REST contracts, researched 2026-09-21; no SDK assumptions."""
import base64
import binascii
import math
from .artifacts import decode_image, require_pillow
from .jobs import Artifact, Result
from .request import (IMAGE_LIMIT, ARTIFACT_LIMIT, fail, integer, object_fields,
                      read_file, sha256, string, task_id)

PRESETS = {
    'forest':'Forest background: layered trees, foliage and woodland depth.',
    'desert':'Desert background: sand dunes, rock formations and dry atmospheric depth.',
    'dungeon':'Dungeon background: stone corridors, ancient masonry and torchlit depth.',
    'city':'City background: architecture, streets and a layered urban skyline.',
    'space':'Space background: stars, distant planets and nebular depth.',
    'underwater':'Underwater background: aquatic plants, rocks and filtered light.'}
SYNC = {'create-image-pixen','create-image-pixflux','image-to-pixelart'}
ASYNC = {'create-image-pixflux-background','generate-ui-v2','inpaint-v3'}
EXPERIMENTAL = {'generate-ui-v2','inpaint-v3'}


def size(value,minimum,maximum):
    object_fields(value,('width','height'))
    return {k:integer(value[k],minimum,maximum) for k in ('width','height')}


def input_image(root,path):
    raw=read_file(root,path,IMAGE_LIMIT)
    return raw,decode_image(raw)


def wire_image(root,path):
    raw,info=input_image(root,path)
    return {'type':'base64','format':info['format'],'base64':base64.b64encode(raw).decode()}


def inline_image(value):
    if not isinstance(value,dict) or not isinstance(value.get('base64'),str) or value.get('type','base64')!='base64' or value.get('format','png') not in ('png','jpeg'):
        fail('unsupported_provider_result')
    encoded=value['base64']
    if encoded.startswith('data:'):
        prefixes={'data:image/png;base64,':'png','data:image/jpeg;base64,':'jpeg'}
        prefix=next((p for p in prefixes if encoded.startswith(p)),None)
        if prefix is None: fail('unsupported_provider_result')
        if 'format' in value and value['format']!=prefixes[prefix]: fail('unsupported_provider_result')
        encoded=encoded[len(prefix):]
    if len(encoded)>ARTIFACT_LIMIT*4//3+4: fail('artifact_byte_limit')
    try:
        raw=base64.b64decode(encoded,validate=True)
    except (ValueError,binascii.Error):
        fail('unsupported_provider_result')
    if not raw or len(raw)>ARTIFACT_LIMIT: fail('unsupported_provider_result')
    return raw


class PixelLab:
    credential_env='PIXELLAB_SECRET'

    def dependency_ids(self,parameters):
        return []

    def validate_dependencies(self,plan,dependencies,transport,*,credential,deadline):
        return {}  # PixelLab's supported operations have no remote task prerequisites.

    def prepare(self,root,operation,parameters):
        if operation not in SYNC|ASYNC:
            fail('unsupported_pixellab_operation')
        require_pillow()  # All six operations declare an image, even text-only input.
        required={'description','image_size'}
        optional={'no_background','seed','background_preset'}
        if operation in ('create-image-pixflux','create-image-pixflux-background'):
            optional|={'init_image','init_image_strength'}
        elif operation=='generate-ui-v2':
            optional|={'color_palette'}
            optional-={'background_preset'}
        elif operation=='image-to-pixelart':
            required={'image','image_size','output_size'}
            optional={'seed','fixer','init_image_strength'}
        elif operation=='inpaint-v3':
            required={'description','inpainting_image','mask_image'}
            optional={'seed','no_background','crop_to_mask'}
        object_fields(parameters,required,optional)
        result=dict(parameters)
        if 'description' in result: string(result['description'],2000)
        for key in ('no_background','fixer','crop_to_mask'):
            if key in result and type(result[key]) is not bool: fail('parameter_must_be_boolean')
        if 'seed' in result:
            integer(result['seed'], -2**63 if operation.startswith('create-image') else 0)
        if 'background_preset' in result:
            preset=result['background_preset']
            if not isinstance(preset,str) or preset not in PRESETS: fail('unsupported_background_preset')
            suffix='\n'+PRESETS[preset]
            if not result['description'].endswith(suffix): result['description']+=suffix
            string(result['description'],2000)
        paths=[]
        if operation=='create-image-pixen':
            dimensions=size(result['image_size'],16,768)
            w,h=dimensions['width'],dimensions['height']
            if w%4 or h%4 or w*h>512*512 or (min(w,h)<32 and w!=h): fail('pixen_size_constraints')
        elif operation in ('create-image-pixflux','create-image-pixflux-background'):
            dimensions=size(result['image_size'],16,400)
            if dimensions['width']*dimensions['height']<32*32: fail('pixflux_minimum_area')
            if 'init_image_strength' in result:
                integer(result['init_image_strength'],1,999)
                if 'init_image' not in result: fail('init_image_required_for_strength')
            if 'init_image' in result:
                paths.append(result['init_image'])
                _,info=input_image(root,result['init_image'])
                if any(info[k]!=dimensions[k] for k in dimensions): fail('init_image_dimensions_mismatch')
        elif operation=='generate-ui-v2':
            dimensions=size(result['image_size'],16,512)
            if dimensions['width']!=dimensions['height']: fail('ui_supported_subset_requires_square')
            if 'color_palette' in result: string(result['color_palette'],200,0)
        elif operation=='image-to-pixelart':
            source_size=size(result['image_size'],16,2048)
            dimensions=size(result['output_size'],16,512)
            paths.append(result['image'])
            _,info=input_image(root,result['image'])
            if any(info[k]!=source_size[k] for k in source_size): fail('source_image_dimensions_mismatch')
            if 'init_image_strength' in result: integer(result['init_image_strength'],0,999)
        else:
            if result.get('crop_to_mask',False): fail('inpaint_crop_to_mask_not_supported')
            result['crop_to_mask']=False  # Vendor defaults true; explicitly override in supported subset.
            paths.extend([result['inpainting_image'],result['mask_image']])
            _,source=input_image(root,result['inpainting_image'])
            _,mask=input_image(root,result['mask_image'])
            dimensions=size({'width':source['width'],'height':source['height']},32,512)
            if any(source[k]!=mask[k] for k in dimensions): fail('mask_dimensions_mismatch')
        return result,paths,{'image':dict(dimensions,formats=['png','jpeg'])}

    def payload(self,root,plan):
        operation = plan['request']['operation']
        body = dict(plan['request']['parameters'])
        body.pop('background_preset', None)
        pins = {item['path']: item for item in plan.get('inputs', [])}

        def pinned_image(path):
            raw, info = input_image(root, path)
            pin = pins.get(path)
            if pin is None or sha256(raw) != pin['sha256'] or len(raw) != pin['size']:
                fail('source_changed_since_plan')
            return {'type': 'base64', 'format': info['format'],
                    'base64': base64.b64encode(raw).decode()}, info

        for key in ('init_image', 'image'):
            if key in body:
                body[key], info = pinned_image(body[key])
                if any(info[dim] != body['image_size'][dim] for dim in ('width', 'height')):
                    fail('source_image_dimensions_mismatch')
        if operation == 'inpaint-v3':
            sizes = []
            for key in ('inpainting_image', 'mask_image'):
                image, info = pinned_image(body[key])
                dimensions = size({'width': info['width'], 'height': info['height']}, 32, 512)
                sizes.append(dimensions)
                body[key] = {'image': image, 'size': dimensions}
            if sizes[0] != sizes[1]:
                fail('mask_dimensions_mismatch')
        return body

    def _completed(self,operation,value,job=None,evidence=None):
        try:
            if not isinstance(value,dict): fail('unsupported_provider_result')
            if 'image' in value and 'images' not in value:
                raw=inline_image(value['image'])
            elif operation in EXPERIMENTAL and 'image' not in value and isinstance(value.get('images'),list) and len(value['images'])==1:
                raw=inline_image(value['images'][0])
            else:
                fail('unsupported_provider_result')
            return Result('generated',job,data_type='pixellab.image',
                          data={'decoder':'experimental-single-image-v1' if operation in EXPERIMENTAL else 'documented-image-v1'},
                          artifacts={'image':Artifact(inline=raw)})
        except ValueError:
            return Result('unsupported_provider_result',job,evidence=evidence or value if isinstance(value,dict) else {'result':value})

    def submit(self,root,plan,dependencies,transport,*,credential,deadline):
        operation=plan['request']['operation']
        value=transport.json('pixellab','POST','/v2/'+operation,body=self.payload(root,plan),credential=credential,deadline=deadline)
        if operation in SYNC:
            return self._completed(operation,value)
        if not isinstance(value,dict) or 'background_job_id' not in value:
            return Result('unsupported_provider_result',evidence={'response':value})
        job=task_id(value['background_job_id'])
        return Result('pending',job,evidence=value)

    def poll(self,plan,job,transport,*,credential,deadline):
        task_id(job)
        value=transport.json('pixellab','GET','/v2/background-jobs/'+job,credential=credential,deadline=deadline)
        if not isinstance(value,dict) or value.get('id')!=job or not isinstance(value.get('created_at'),str):
            return Result('unsupported_provider_result',job,evidence={'response':value})
        state=value.get('status')
        if state=='processing': return Result('pending',job)
        if state=='failed': return Result('failed',job)
        if state=='completed': return self._completed(plan['request']['operation'],value.get('last_response'),job,value)
        return Result('unsupported_provider_result',job,evidence=value)

    def validate_json(self,operation,value):
        fail('pixellab_has_no_collectable_json_operation')

    def validate_data(self,operation,data_type,data):
        if data_type is None and data=={}: return
        if data_type!='pixellab.image' or data not in ({'decoder':'documented-image-v1'},{'decoder':'experimental-single-image-v1'}):
            fail('invalid_pixellab_result_data')

    def balance(self,transport,*,credential):
        value=transport.json('pixellab','GET','/v2/balance',credential=credential)
        if not isinstance(value,dict) or not isinstance(value.get('credits'),dict) or not isinstance(value.get('subscription'),dict): fail('unsupported_balance_result')
        credit,subscription=value['credits'],value['subscription']
        for obj,key in ((credit,'usd'),(subscription,'generations'),(subscription,'total')):
            if type(obj.get(key)) not in (int,float) or not math.isfinite(obj[key]): fail('unsupported_balance_result')
        if not isinstance(subscription.get('status'),str) or len(subscription['status'])>100: fail('unsupported_balance_result')
        if credit.get('type','usd')!='usd' or subscription.get('type','generations')!='generations': fail('unsupported_balance_result')
        # Return only known scalar fields; arbitrary provider fields are never echoed.
        return {'credits':{'usd':credit['usd']},'subscription':{k:subscription[k] for k in ('status','generations','total')}}
