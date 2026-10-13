import importlib.util,sys,ctypes,inspect,json
from pathlib import Path
p=Path(__file__).with_name('owned-sandbox-stop-proof.py')
s=importlib.util.spec_from_file_location('stopproof',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
original=m.process_identity
def observed(pid):
    try: return original(pid)
    except RuntimeError as error:
        print(json.dumps({'operation':'read_only_process_identity_diagnostic','pid':pid,'code':str(error),'win32_error':ctypes.get_last_error(),'caller_functions':[frame.function for frame in inspect.stack()[1:5]]}),flush=True)
        raise
m.process_identity=observed
try: m.main()
except RuntimeError as error:
    print(json.dumps({'operation':'read_only_prepare_diagnostic','code':str(error),'dispatched':m.DISPATCHED}),flush=True)
    sys.exit(1)
