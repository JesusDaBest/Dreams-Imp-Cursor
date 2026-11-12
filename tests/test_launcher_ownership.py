"""Exercise the real launcher against disposable processes, never the live cursor."""
import ctypes as C
import json,os,subprocess,time,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
kernel=C.WinDLL('kernel32')
kernel.OpenEventW.argtypes=(C.c_ulong,C.c_int,C.c_wchar_p);kernel.OpenEventW.restype=C.c_void_p
kernel.CloseHandle.argtypes=(C.c_void_p,)
existing=kernel.OpenEventW(0x100000,False,'Local\\DreamsImp.Exit')
if existing:
    kernel.CloseHandle(existing)
    raise RuntimeError('Close Dreams Imp before running the isolated launcher tests; the live app will not be changed.')
TEST=ROOT.parent/'imp-selection-lifecycle-20261111'
TEST.mkdir(exist_ok=True)
(TEST/'runtime').mkdir(exist_ok=True)
python=TEST/'runtime/python'
if not python.exists():
    subprocess.run(['cmd','/c','mklink','/J',str(python),str(ROOT/'runtime/python')],check=True,capture_output=True)
shutil.copy2(ROOT/'build-output/Dreams Imp.exe',TEST/'Dreams Imp.exe')
shutil.copy2(ROOT/'runtime/app_lifecycle.py',TEST/'runtime/app_lifecycle.py')
(TEST/'runtime/app.py').write_text('''import os,sys,json,subprocess,time,ctypes as C
from pathlib import Path
import app_lifecycle as life
root=Path(__file__).resolve().parent
mode=os.environ['IMP_TEST_MODE']
if mode=='empty':life.picker_closed();sys.exit(0)
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],creationflags=subprocess.CREATE_NO_WINDOW)
if mode in ('keep','watchkill'):
 subprocess.Popen([sys.executable,str(root/'watch.py'),str(os.getpid())],creationflags=subprocess.CREATE_NO_WINDOW|0x01000000)
(root/'pids.json').write_text(json.dumps({'picker':os.getpid(),'child':child.pid}))
if mode=='keep':life.picker_closed();sys.exit(0)
if mode=='unexpected':sys.exit(0)
while not life.exit_requested():time.sleep(.02)
child.terminate();child.wait()
life.picker_closed()
''')
(TEST/'runtime/watch.py').write_text('''import ctypes as C,sys,time
from pathlib import Path
k=C.WinDLL('kernel32');k.OpenProcess.argtypes=(C.c_ulong,C.c_int,C.c_ulong);k.OpenProcess.restype=C.c_void_p
k.WaitForSingleObject.argtypes=(C.c_void_p,C.c_ulong);k.CloseHandle.argtypes=(C.c_void_p,)
h=k.OpenProcess(0x100000,False,int(sys.argv[1]))
if h:
 (Path(__file__).parent/'watch-ready').write_text('ready')
 k.WaitForSingleObject(h,0xffffffff);k.CloseHandle(h)
(Path(__file__).parent/'watch-done').write_text('done')
''')
k=C.WinDLL('kernel32')
k.OpenProcess.argtypes=(C.c_ulong,C.c_int,C.c_ulong);k.OpenProcess.restype=C.c_void_p
k.WaitForSingleObject.argtypes=(C.c_void_p,C.c_ulong);k.CloseHandle.argtypes=(C.c_void_p,)
k.TerminateProcess.argtypes=(C.c_void_p,C.c_uint)
def dead(pid):
    h=k.OpenProcess(0x100000,False,pid)
    if not h:return True
    try:return k.WaitForSingleObject(h,0)==0
    finally:k.CloseHandle(h)
def until(predicate):
    end=time.monotonic()+8
    while time.monotonic()<end:
        if predicate():return
        time.sleep(.03)
    raise AssertionError('test condition timed out')
def launch(mode):
    (TEST/'runtime/pids.json').unlink(missing_ok=True)
    (TEST/'runtime/watch-done').unlink(missing_ok=True)
    (TEST/'runtime/watch-ready').unlink(missing_ok=True)
    p=subprocess.Popen([str(TEST/'Dreams Imp.exe')],env={**os.environ,'IMP_TEST_MODE':mode})
    if mode=='empty':return p,None
    until(lambda:(TEST/'runtime/pids.json').exists())
    ids=json.loads((TEST/'runtime/pids.json').read_text())
    return p,ids

p,_=launch('empty');assert p.wait(8)==0;print('PASS empty picker closes launcher',flush=True)
p,ids=launch('keep');until(lambda:dead(ids['picker']));assert p.poll() is None and not dead(ids['child'])
until(lambda:(TEST/'runtime/watch-done').exists())
p.terminate();p.wait(8);until(lambda:dead(ids['child']));print('PASS close preserves cursor worker; End Task kills worker; recovery watcher escapes and exits',flush=True)
p,ids=launch('watchkill');until(lambda:(TEST/'runtime/watch-ready').exists())
p.terminate();p.wait(8);until(lambda:dead(ids['child']))
until(lambda:(TEST/'runtime/watch-done').exists());print('PASS recovery watcher survives forced job termination and finishes',flush=True)
p,ids=launch('unexpected');p.wait(8);until(lambda:dead(ids['child']));print('PASS unexpected picker death stops children',flush=True)
p,ids=launch('running')
h=k.OpenProcess(1,False,ids['picker']);assert h;k.TerminateProcess(h,1);k.CloseHandle(h)
p.wait(8);until(lambda:dead(ids['child']));print('PASS End Task on picker stops launcher and worker',flush=True)
p,ids=launch('running')
import sys
sys.path.insert(0,str(ROOT/'runtime'))
import app_lifecycle
assert app_lifecycle.request_exit();assert p.wait(8)==0
until(lambda:dead(ids['child']));print('PASS tray Exit request closes entire session',flush=True)
