"""Bounded read-only inspection of pointers recorded by the native exporter."""
from pathlib import Path
import ctypes as C,struct,json,sys
app=Path(__file__).resolve().parents[1]
work=app.parent
sys.path.insert(0,str(work/'dreams-debug-control'))
from debug_control import Client
root=Path((app/'cloud-capture/latest-compute-launch.txt').read_text().strip())
client=Client(root/'run.json');client.verify()
k=C.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[C.c_ulong,C.c_int,C.c_ulong];k.OpenProcess.restype=C.c_void_p
k.CloseHandle.argtypes=[C.c_void_p]
k.ReadProcessMemory.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
h=k.OpenProcess(0x1010,False,client.run['pid']);assert h
report=[]
try:
 for name in ['ceda85fb','f0a05240','da4c2318']:
  p=root/'compute-inputs'/name;ud=(p/'user-data.bin').read_bytes();flat=(p/'flat.bin').read_bytes()
  row={'shader':name,'pointers':[]}
  for n in range(0,24,8):
   address=struct.unpack_from('<Q',ud,n)[0]
   if not address:continue
   data=C.create_string_buffer(4096);got=C.c_size_t()
   if not k.ReadProcessMemory(h,address,data,4096,C.byref(got)):continue
   raw=data.raw[:got.value];(p/('srt-root'+str(n//8)+'.bin')).write_bytes(raw)
   matches=[]
   for off in range(16,len(flat)//4-3):
    needle=flat[off*4:off*4+16]
    if len(set(needle))<3:continue
    found=raw.find(needle)
    if found>=0:matches.append([off,found//4])
   row['pointers'].append({'user_pair':n//8,'address':hex(address),'matches':matches[:25]})
  report.append(row)
 client.verify()
finally:k.CloseHandle(h)
(root/'srt-mapping.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
