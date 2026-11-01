"""Test the real image entrypoint, discovery and fresh readings with no external network."""
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

image = sys.argv[1]
root = Path(__file__).resolve().parent
prefix = 'winet-test-' + uuid.uuid4().hex[:12]
network, fixture, app = prefix + '-net', prefix + '-fixture', prefix + '-app'
def run(*args, check=True):
    return subprocess.run(['docker', *args], text=True, capture_output=True, check=check, timeout=45)
try:
    run('network', 'create', '--internal', network)
    run('run', '-d', '--name', fixture, '--network', network, '--network-alias', 'fixture',
        '--memory', '256m', '--pids-limit', '128', '--entrypoint', 'node',
        '-v', str(root / 'fixture.cjs') + ':/tmp/fixture.cjs:ro', image, '/tmp/fixture.cjs')
    for _ in range(30):
        if 'fixture-ready' in run('logs', fixture).stdout: break
        time.sleep(1)
    else: raise AssertionError('Synthetic server did not start')
    run('run', '-d', '--name', app, '--network', network, '--memory', '256m', '--pids-limit', '128',
        '-e', 'WINET_HOST=fixture', '-e', 'MQTT_URL=mqtt://fixture:1883', '-e', 'MQTT_PREFIX=homeassistant',
        '-e', 'WINET_USER=fixture-user', '-e', 'WINET_PASS=fixture-only', '-e', 'POLL_INTERVAL=1',
        '-e', 'ANALYTICS=false', '-e', 'SSL=false', '-e', 'SITE_TOTALS=false', image)
    proof = {}
    for _ in range(45):
        result = run('exec', fixture, 'node', '-e', "require('http').get('http://127.0.0.1/proof',r=>r.pipe(process.stdout))")
        proof = json.loads(result.stdout)
        if all(proof.values()): break
        time.sleep(1)
    else:
        print(run('logs', app).stdout[-12000:]); raise AssertionError(proof)
    assert run('inspect', app, '--format', '{{.State.Running}}').stdout.strip() == 'true'
    # The vendor runtime contains no npm/dev toolchain, test fixtures or private input.
    result = run('exec', app, 'node', '-e', "const f=require('fs'); for(const p of ['/usr/src/app/.env','/usr/src/app/data','/usr/src/app/src','/usr/src/app/test','/usr/src/app/node_modules/typescript','/usr/src/app/node_modules/gts'])if(f.existsSync(p))throw Error('Unexpected runtime content: '+p);if(process.arch!=='x64')throw Error('Wrong architecture');console.log('runtime-content-ok')")
    assert 'runtime-content-ok' in result.stdout
    receipt = {'status': 'passed', 'external_network': False, 'real_upstream_entrypoint': True,
               'proof': proof, 'architecture': 'amd64', 'private_inputs_in_image': False,
               'physical_inverter_tested': False, 'HomeLab_integration': False}
    Path('runtime-smoke.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
finally:
    for name in [app, fixture]: run('rm', '-f', name, check=False)
    run('network', 'rm', network, check=False)
