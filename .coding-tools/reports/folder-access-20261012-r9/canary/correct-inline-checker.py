"""Correct reviewed inline fixture escaping before any live canary dispatch."""
from pathlib import Path
import ast
import base64
import hashlib
import json
root = Path(__file__).parent
script = root / 'run-autocad-folder-access-canary-r9.py'
before = script.read_bytes()
assert hashlib.sha256(before).hexdigest() == '3f6339d63faa0f4f8c8c13c5098a20da76daf69a3ec40f78b40e99255cfed4e6'
source = before.decode()
tree = ast.parse(source)
values = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
          if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
          and node.targets[0].id in {'FINAL', 'NODE_CODE', 'TARGET', 'MARKER'}}
final = values['FINAL'].encode()
digest = hashlib.sha256(final).hexdigest()
code = "'use strict'; const assert=require('node:assert/strict'); const fs=require('node:fs'); const path=require('node:path'); const crypto=require('node:crypto'); const child=require('node:child_process'); "
code += "assert.equal(process.platform,'win32'); assert.ok(Number(process.versions.node.split('.')[0])>=22); assert.equal(path.basename(process.cwd()),'share-0'); assert.equal(path.basename(path.dirname(process.cwd())),'CodexWorkspace'); "
code += f"const expected=Buffer.from('{base64.b64encode(final).decode()}','base64'); const actual=fs.readFileSync({json.dumps(values['TARGET'])}); assert.deepEqual(actual,expected); const digest=crypto.createHash('sha256').update(actual).digest('hex'); assert.equal(digest,{json.dumps(digest)}); "
code += "const dotnet=child.spawnSync('dotnet',['--version'],{encoding:'utf8',shell:false,timeout:45000,maxBuffer:65536}); assert.equal(dotnet.error,undefined); assert.equal(dotnet.status,0); assert.equal(dotnet.stdout.trim(),'10.0.102'); "
code += f"console.log({json.dumps(values['MARKER'])}+' sha256='+digest+' cwd='+process.cwd()); console.log('AUTOCAD_DOTNET_CHILD_VERSION=10.0.102');"
lines = source.splitlines(keepends=True)
index = next(index for index, line in enumerate(lines) if line.startswith('NODE_CODE = '))
lines[index] = 'NODE_CODE = ' + repr(code) + '\n'
script.write_text(''.join(lines), encoding='utf-8', newline='\n')
check = root / 'inline-checker-corrected.cjs'
check.write_text(code, encoding='utf-8')
receipt = {'operation':'inline_checker_escape_review', 'live_dispatches':0,
           'original_hash':hashlib.sha256(before).hexdigest(),
           'corrected_hash':hashlib.sha256(script.read_bytes()).hexdigest(),
           'expected_final_sha256':digest, 'inline_expected_bytes':len(final),
           'fix':'Base64 expected bytes; path component checks avoid double escaping'}
(root / 'inline-checker-correction-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
