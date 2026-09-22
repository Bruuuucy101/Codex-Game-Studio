"""Real process-death fixture. Never imported or exposed by production CLI."""
import os
from pathlib import Path
import sys
from fixtures import REPO
from ccgs.assets import jobs,artifacts
from ccgs.assets.http import Transport

root=Path(sys.argv[1]); phase=sys.argv[2]; origin=sys.argv[3]
transport=Transport(origin_map={'https://api.pixellab.ai':origin})
if phase in ('before-post','after-result'):
    original=jobs.save_receipt
    def dying_save(root,state,id,receipt):
        if phase=='after-result' and receipt['status']=='generated':os._exit(73)
        original(root,state,id,receipt)
        if phase=='before-post' and receipt['status']=='submitting':os._exit(73)
    jobs.save_receipt=dying_save
    jobs.submit(root,root/'.ccgs-assets','request.json','one',write=True,transport=transport)
elif phase=='after-link':
    original=artifacts.publish
    def dying_publish(*args,**kwargs):
        original(*args,**kwargs)
        os._exit(73)
    artifacts.publish=dying_publish
    jobs.collect(root,root/'.ccgs-assets','one',write=True,transport=transport)
else:
    raise ValueError('unknown fixture crash phase')
