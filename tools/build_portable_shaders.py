"""Build the cursor shaders and lower vendor instructions before packaging."""
from pathlib import Path
import argparse,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]

def build(sdk):
 tools=Path(sdk)/'Bin'
 for source,dest in [('khr-fragment.spvasm','PrimImpOverBokehPS-desktop-draw.spv'),('wave32-resolve.spvasm','PrimImpTAAUpdate-desktop-resolve.spv')]:
  target=ROOT/'runtime/shader-inputs'/dest
  with tempfile.TemporaryDirectory(prefix='dreams-imp-shader-') as d:
   raw=Path(d)/'assembled.spv';portable=Path(d)/'portable.spv'
   subprocess.run([str(tools/'spirv-as.exe'),'--target-env','spv1.6',str(ROOT/'native/shaders'/source),'-o',str(raw)],check=True)
   subprocess.run([str(tools/'spirv-opt.exe'),'--amd-ext-to-khr',str(raw),'-o',str(portable)],check=True)
   subprocess.run([str(tools/'spirv-val.exe'),'--target-env','vulkan1.3',str(portable)],check=True)
   target.write_bytes(portable.read_bytes())
  print(target.name,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sdk',default=os.environ.get('VULKAN_SDK'));a=p.parse_args()
 if not a.sdk:p.error('Set VULKAN_SDK or pass --sdk.')
 build(a.sdk)
