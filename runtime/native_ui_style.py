"""Execute Dreams' original 0x76b77a0 UI material interpolation, unchanged."""
from pathlib import Path
import ctypes as C, struct, runpy, hashlib, json, math
RUNTIME=Path(__file__).resolve().parent
ROOT=RUNTIME/'reference-state/native-ui'
base=runpy.run_path(str(RUNTIME/'verify-native-imp-animation.py'))
class NativeUIStyle(base['NativeEvaluator']):
    def __init__(self):
        text=base['verified_bytes'](RUNTIME/'native-code/guest-text.bin',base['EXPECTED_TEXT'])
        super().__init__(text,last_page=0xfa00000)
        for lo,hi in [(0x76b7000,0x76ba000),(0x7867000,0x7868000),(0x77a7000,0x77a8000),(0xf929000,0xf92e000)]:
            self.pages(lo,hi)
            if hi-base['BASE']<=len(text):self.put(lo,text[lo-base['BASE']:hi-base['BASE']])
        presets=(ROOT/'ui-presets.bin').read_bytes()
        assert hashlib.sha256(presets).hexdigest()=='5282534d63beeac494e67bb1fa872b2b8dc1f375c38b8cc0426497a578b4adb5'
        self.put(0xf929460,presets)
        # Preserve Windows nonvolatile registers; pass two host args to SysV RDI/RSI.
        wrapper=base['to_guest'](self.addr(0x76b77a0))
        wrapper=wrapper.replace(bytes.fromhex('48 89 cf 48 b8'),bytes.fromhex('48 89 cf 48 89 d6 48 b8'),1)
        self.put(0x76b9e00,wrapper)
        self.protect(0x76b7000,0x76ba000,0x20);self.protect(0x7867000,0x7868000,0x02)
        self.fn=C.CFUNCTYPE(None,C.c_void_p,C.c_void_p)(self.addr(0x76b9e00))
    def sample(self,primitive,hover):
        assert len(primitive)==432 and 0<=hover<=1
        src=C.create_string_buffer(primitive);out=C.create_string_buffer(212)
        struct.pack_into('<f',src,0xbc,hover)
        self.fn(C.addressof(out),C.addressof(src))
        return out.raw
if __name__=='__main__':
    vm=NativeUIStyle();rows=[]
    try:
        for p in sorted((ROOT/'entry-inputs').glob('*.bin')):
            raw=p.read_bytes();samples=[vm.sample(raw,i/60) for i in range(61)]
            assert all(all(math.isfinite(x) for x in struct.unpack('<53f',b)) for b in samples)
            again=[vm.sample(raw,i/60) for i in range(61)];assert again==samples
            (ROOT/(p.stem+'-materials.bin')).write_bytes(b''.join(samples))
            rows.append({'widget':p.stem,'samples':len(samples),'changing_fields':[i for i in range(53) if samples[0][i*4:i*4+4]!=samples[-1][i*4:i*4+4]],'sha256':hashlib.sha256(b''.join(samples)).hexdigest()})
        (ROOT/'native-style-results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
    finally:vm.close()
