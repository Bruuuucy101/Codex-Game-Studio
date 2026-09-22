"""Command line boundary; no configurable hosts, executables or persisted credentials."""
import argparse
import json
from .request import check_root, get_adapter, prepare_request, redact


def main(root,argv=None,*,transport=None,adapters=None):
    """Library-injected transport is available to tests; CLI has no endpoint override."""
    parser=argparse.ArgumentParser(prog='ccgs assets',description='Optional explicit asset production; preview by default.')
    commands=parser.add_subparsers(dest='command',required=True)
    plan=commands.add_parser('plan'); plan.add_argument('--request',required=True)
    submit_parser=commands.add_parser('submit')
    submit_parser.add_argument('--request',required=True); submit_parser.add_argument('--id',required=True)
    submit_parser.add_argument('--write',action='store_true')
    for command in ('status','resume','collect'):
        child=commands.add_parser(command); child.add_argument('--id',required=True)
        if command!='status': child.add_argument('--write',action='store_true')
        if command=='resume': child.add_argument('--wait-seconds',type=float,default=120)
    ingest_parser=commands.add_parser('ingest')
    for name in ('source','output','asset-id'): ingest_parser.add_argument('--'+name,required=True)
    ingest_parser.add_argument('--write',action='store_true')
    balance=commands.add_parser('balance'); balance.add_argument('--provider',choices=['pixellab'],required=True)
    args=parser.parse_args(argv)
    try:
        from . import artifacts,jobs
        from .http import Transport
        root=check_root(root); state_dir=root/'.ccgs-assets'
        common={'transport':transport,'adapters':adapters}
        if args.command=='plan':
            result=prepare_request(root,state_dir,args.request,adapters=adapters)
            artifacts.preflight(root,result['request']['outputs'])
        elif args.command=='submit':
            result=jobs.submit(root,state_dir,args.request,args.id,write=args.write,**common)
        elif args.command=='status':
            result=jobs.status(root,state_dir,args.id,**common)
        elif args.command=='resume':
            result=jobs.resume(root,state_dir,args.id,write=args.write,wait_seconds=args.wait_seconds,**common)
        elif args.command=='collect':
            result=jobs.collect(root,state_dir,args.id,write=args.write,**common)
        elif args.command=='ingest':
            result=jobs.ingest(root,state_dir,args.source,args.output,args.asset_id,write=args.write)
        else:
            adapter=get_adapter(args.provider,adapters)
            result=adapter.balance(transport or Transport(),credential=jobs._credential(adapter))
        print(json.dumps(redact(result),ensure_ascii=False,indent=2,allow_nan=False))
        return 0
    except ValueError as error:
        print(json.dumps({'status':'FAIL','error':str(error)}))
        return 1
    except (OSError,KeyError,TypeError,RecursionError):
        print(json.dumps({'status':'FAIL','error':'invalid_or_unavailable_local_state'}))
        return 1
