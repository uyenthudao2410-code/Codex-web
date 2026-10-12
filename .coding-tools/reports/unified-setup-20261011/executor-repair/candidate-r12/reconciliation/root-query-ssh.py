"""Root-only read-only query streamed in memory; no staging or remote writes."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
HERE = Path(__file__).resolve().parent
FROZEN = HERE.parents[1] / 'candidate-r11/activation-server/root-ssh.py'
need = lambda value: None if value else (_ for _ in ()).throw(ValueError())
need(hashlib.sha256(FROZEN.read_bytes()).hexdigest() == 'd6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba')
spec = importlib.util.spec_from_file_location('frozen_readonly_transport', FROZEN)
transport = importlib.util.module_from_spec(spec); spec.loader.exec_module(transport)
WRAPPER = "import hashlib,sys; raw=sys.stdin.buffer.read(262145); assert len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==sys.argv[1]; exec(compile(raw,'<pinned-memory-readonly-query>','exec'),{'__name__':'__main__'})"
def main():
    raw = (HERE / 'observe-exact-action.py').read_bytes()
    need(hashlib.sha256(raw).hexdigest() == json.loads((HERE/'query-manifest.json').read_bytes())['query_sha256'])
    argv = ['/usr/bin/python3', '-B', '-c', WRAPPER, hashlib.sha256(raw).hexdigest()]
    ssh = shutil.which('ssh'); need(ssh)
    result = subprocess.run([ssh, '-T', '-oBatchMode=yes', '-oStrictHostKeyChecking=yes', '-oConnectTimeout=15',
      '-oServerAliveInterval=15', '-oServerAliveCountMax=2', 'svhome@100.116.112.22', shlex.join(argv)],
      input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    need(len(result.stdout) <= 65536 and b'Bearer ' not in result.stdout and b'PRIVATE KEY' not in result.stdout)
    receipt = {'phase':'root_r12_exact_action_read_only_query', 'public_receipts':transport.safe_receipt(result.stdout),
      'ssh_returncode':result.returncode, 'remote_mutation':False, 'stderr_disclosed':False, 'staged_files':False}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with (HERE / ('query-receipt-'+stamp+'.json')).open('x',encoding='utf-8') as handle:
        json.dump(receipt,handle,sort_keys=True,indent=2)
    print(json.dumps(receipt,separators=(',',':')))
    raise SystemExit(result.returncode)
if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('{"phase":"root_r12_exact_action_read_only_query","ok":false,"remote_mutation":false,"code":"SAFE_READ_ONLY_QUERY_FAILED","stderr_disclosed":false,"replay_forbidden":true}')
        raise SystemExit(2) from None
