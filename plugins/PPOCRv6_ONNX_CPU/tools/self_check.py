"""Exercise the real worker path; no empty-sample false PASS."""
import argparse
import base64
import importlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image',default='',help='Image path; drag an image onto the window when prompted')
    parser.add_argument('--mode',default='small',choices=['tiny','small','medium'])
    parser.add_argument('--expected',default='',help='Optional exact text for a labelled sample')
    parser.add_argument('--all-modes',action='store_true')
    args=parser.parse_args()
    name=ROOT.name
    module={'PPOCRv6_ONNX_CPU':'ppocr_api','HyperLPR3_Plate_CPU':'lpr_api','DDDDOCR_Captcha_Umi':'ddddocr_api'}[name]
    print('Python:',sys.version)
    print('OS:',platform.platform(),'Plugin:',ROOT)
    if not args.image and sys.stdin.isatty():
        args.image=input('Drag a test image here (or paste its path), then press Enter: ').strip().strip('"')
    if not args.image:
        print('[INCOMPLETE] No test image. Real inference was NOT tested.')
        return 2
    image=Path(args.image)
    if not image.is_file():
        print('[FAIL] Image does not exist:',image)
        return 1
    data=image.read_bytes()
    local={}
    if module=='ppocr_api':
        cases=[{'mode':x,'use_cls':False} for x in (['tiny','small','medium'] if args.all_modes else [args.mode])]
    elif module=='lpr_api':
        cases=[{'detect_level':x,'use_cls':True} for x in (['low','high'] if args.all_modes else ['low'])]
    else:
        cases=[{'mode':x,'charset':'alnum','strict_length':False,'decoder':'greedy'} for x in ['beta','classic','dual','race']]
    api=importlib.import_module(module).Api({})
    incomplete=False
    try:
        for local in cases:
            error=api.start(local)
            if error:
                print('[FAIL]',error)
                return 1
            results=[]
            for method,arg in [('runPath',str(image.resolve())),('runBytes',data),('runBase64',base64.b64encode(data).decode('ascii'))]:
                t=time.monotonic();result=getattr(api,method)(arg)
                print(local,method,round(time.monotonic()-t,3),'s',json.dumps(result,ensure_ascii=False))
                if result.get('code') not in (100,101):
                    return 1
                results.append(result)
            if any(r!=results[0] for r in results[1:]):
                print('[FAIL] Path/bytes/base64 results differ')
                return 1
            if results[0]['code']==101:
                incomplete=True
                print('[INCOMPLETE] Inference ran but returned no text. Try a suitable test image.')
            if args.expected:
                text=''.join(x['text'] for x in results[0].get('data',[]) or [])
                if text!=args.expected:
                    print('[FAIL] Expected text mismatch')
                    return 1
        if any(n in sys.modules for n in ['numpy','cv2','onnxruntime','ddddocr','PIL']):
            print('[FAIL] Native dependency leaked into parent process')
            return 1
    finally:
        api.stop()
    if incomplete:
        return 2
    print('[PASS] Models loaded; three input methods agreed; worker closed. Check printed text yourself. This is not an accuracy benchmark.')
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('[FAIL]',str(exc))
        sys.exit(1)
