"""Run the real PowerShell launcher with local fixture modules, never a gateway."""
import json
from contextlib import suppress
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from urllib.request import urlopen
from urllib.error import URLError

import pytest


@pytest.mark.skipif(sys.platform != 'win32' or not shutil.which('pwsh'), reason='Windows demo launcher')
def test_demo_excludes_sentinel_from_viewer_and_passes_executor_args(tmp_path: Path):
    # Unique fixture files, fixed candidate port; never stop an existing listener.
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 7526))
    source = Path(__file__).resolve().parents[2]
    (tmp_path/'demo').mkdir()
    shutil.copyfile(source/'demo/run-demo.ps1', tmp_path/'demo/run-demo.ps1')
    scripts = tmp_path/'.venv/Scripts'
    scripts.mkdir(parents=True)
    shutil.copyfile(sys.executable, scripts/'python.exe')
    shutil.copyfile(Path(sys.prefix)/'pyvenv.cfg', tmp_path/'.venv/pyvenv.cfg')
    for package in ('viz', 'orchestration'):
        (tmp_path/package).mkdir()
        (tmp_path/package/'__init__.py').write_text('', encoding='utf-8')
    (tmp_path/'viz/server.py').write_text('''import json, os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'fixture-only')
server = HTTPServer(('127.0.0.1', 7526), Handler)
server.timeout = 25
Path('viewer-env.json').write_text(json.dumps({'key_present': 'MORPH_EVOMAP_API_KEY' in os.environ, 'pid': os.getpid()}))
server.handle_request()
server.server_close()
''', encoding='utf-8')
    (tmp_path/'orchestration/rehearsal.py').write_text('''import json, os, sys
from pathlib import Path
Path('executor-env.json').write_text(json.dumps({'key_present': 'MORPH_EVOMAP_API_KEY' in os.environ, 'argv': sys.argv[1:]}))
''', encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if k.upper() != 'MORPH_EVOMAP_API_KEY'}
    env.update(MORPH_EVOMAP_API_KEY='fixture-only-not-a-secret', TEMP=str(tmp_path), TMP=str(tmp_path))
    try:
        completed = subprocess.run(['pwsh', '-NoProfile', '-File', str(tmp_path/'demo/run-demo.ps1'),
                                    '-AuthorizeLive', '-Executor', 'evomap', '-Mode', 'manual', '-Port', '7526'],
                                   env=env, capture_output=True, text=True, encoding='utf-8', timeout=30)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert not json.loads((tmp_path/'viewer-env.json').read_text())['key_present']
        executor = json.loads((tmp_path/'executor-env.json').read_text())
        assert executor['key_present']
        args = executor['argv']
        assert args[args.index('--executor')+1] == 'evomap'
        assert args[args.index('--model')+1] == 'evomap-gpt-5.6-luna'
        assert args[args.index('--mode')+1] == 'manual'
        assert args.count('--authorize-task') == 2
        assert 'fixture-only-not-a-secret' not in completed.stdout + completed.stderr
    finally:
        # This fixture viewer exits after its first HTTP request or its bounded timeout.
        if (tmp_path/'viewer-env.json').exists():
            # Start-Process may keep the capturing parent open until the bounded
            # viewer already exits; connection refusal then requires no cleanup.
            with suppress(URLError):
                with urlopen('http://127.0.0.1:7526/', timeout=3) as response:
                    assert response.read() == b'fixture-only'
