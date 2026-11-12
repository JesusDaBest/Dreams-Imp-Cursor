"""Lower only AMD min/max instructions; preserve the captured shader's other words."""
from pathlib import Path
import struct,json,subprocess
ROOT=Path(__file__).resolve().parent

def string(words):return struct.pack('<'+'I'*len(words),*words).split(b'\0',1)[0].decode()
def lower(src,dst,*,lower_minmax=True):
    words=list(struct.unpack('<'+'I'*(len(src.read_bytes())//4),src.read_bytes()));header=words[:5];ins=[];off=5;amd=None;glsl=None;nextid=header[3]
    while off<len(words):
        count=words[off]>>16;op=words[off]&65535;w=words[off:off+count];assert count>0;off+=count
        if op==10 and string(w[1:]) in ('SPV_AMD_shader_explicit_vertex_parameter','SPV_AMD_shader_image_load_store_lod'):continue
        if op==17 and w[1]==5015:continue
        # AMD image LOD capability is unused in these captures; reject an actual LOD operand.
        if op==98:assert len(w)==5 or w[5]==0,'Image-read LOD needs lowering'
        if op==99:assert len(w)==4 or w[4]==0,'Image-write LOD needs lowering'
        if op==11:
            name=string(w[2:])
            if name=='SPV_AMD_shader_trinary_minmax' and lower_minmax:amd=w[1];continue
            if name=='GLSL.std.450':glsl=w[1]
        ins.append(w)
    assert amd is None or glsl is not None;out=[];changed=0
    def ext(typ,result,op,*args):return [((5+len(args))<<16)|12,typ,result,glsl,op,*args]
    def fresh():
        nonlocal nextid
        result=nextid;nextid+=1;return result
    for w in ins:
        if w[0]&65535==12 and w[3]==amd:
            typ,result,_,kind,a,b,c=w[1:];changed+=1
            if kind in (1,4):
                tmp=fresh();op=37 if kind==1 else 40;out+=[ext(typ,tmp,op,a,b),ext(typ,result,op,tmp,c)]
            elif kind==7:
                lo=fresh();hi=fresh();mid=fresh();out+=[ext(typ,lo,37,a,b),ext(typ,hi,40,a,b),ext(typ,mid,37,hi,c),ext(typ,result,40,lo,mid)]
            else:raise ValueError('Unsupported AMD trinary opcode '+str(kind))
        else:out.append(w)
    header[3]=nextid;flat=header+[v for w in out for v in w];dst.write_bytes(struct.pack('<'+'I'*len(flat),*flat));return changed
if __name__=='__main__':
    n=lower(ROOT/'buttons-b4e-now/fs.spv',ROOT/'ui-portable-fs.spv');print('Lowered native AMD min/max sites:',n);lower(ROOT/'buttons-b4e-now/vs.spv',ROOT/'ui-portable-vs.spv')
    subprocess.run(['C:/VulkanSDK/1.4.350.0/Bin/spirv-val.exe','--target-env','vulkan1.3',str(ROOT/'ui-portable-fs.spv')],check=True)
