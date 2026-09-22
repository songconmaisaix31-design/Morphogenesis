"""Parse/list the opt-in provider in a fresh isolated process; never run a model."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def check(executable: Path, config: Path) -> dict:
    root = Path(tempfile.mkdtemp(prefix='morph-opencode-config-'))
    # Whitelist process essentials, never forward account/provider credentials.
    env = {k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'PATH', 'COMSPEC')}
    for variable, folder in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),
                             ('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),
                             ('OPENCODE_CONFIG_DIR','config-dir'),('OPENCODE_TEST_HOME','home')]:
        target = root/folder
        target.mkdir()
        env[variable] = str(target)
    env.update(TEMP=str(root), TMP=str(root), OPENCODE_CONFIG=str(config.resolve()),
               OPENCODE_DISABLE_PROJECT_CONFIG='true', OPENCODE_DISABLE_CLAUDE_CODE='true',
               OPENCODE_DISABLE_DEFAULT_PLUGINS='true', OPENCODE_DISABLE_MODELS_FETCH='true',
               OPENCODE_DISABLE_AUTOUPDATE='true', OPENCODE_DISABLE_LSP_DOWNLOAD='true',
               MORPH_EVOMAP_API_KEY='local-config-sentinel-not-a-credential')

    def run(*args: str) -> str:
        completed = subprocess.run([str(executable), *args], cwd=root, env=env,
                                   capture_output=True, text=True, encoding='utf-8', timeout=45)
        assert completed.returncode == 0, f'OpenCode {args[0]} failed (exit {completed.returncode}); inspect isolated logs at {root}'
        assert env['MORPH_EVOMAP_API_KEY'] not in completed.stdout + completed.stderr
        (root/('-'.join(args)+'.stdout.log')).write_text(completed.stdout, encoding='utf-8')
        (root/('-'.join(args)+'.stderr.log')).write_text(completed.stderr, encoding='utf-8')
        return completed.stdout.strip()

    version = run('--version')
    paths = run('debug','paths')
    # Verify the executable resolves all data/config/cache into this isolated root
    # before allowing its provider/config loader to run.
    for name in ('data','config','cache','state'):
        lines = [line for line in paths.splitlines() if line.startswith(name)]
        assert len(lines) == 1 and str(root).lower() in lines[0].lower(), f'{name} isolation not confirmed'
    listed = run('models','evomap').splitlines()
    expected = sorted('evomap/'+model for model in json.loads(config.read_text(encoding='utf-8'))['provider']['evomap']['models'])
    assert sorted(listed) == expected
    return {'version':version,'provider':'evomap','models':listed,'isolated_root':str(root),
            'configuration_parsed':True,'model_requests':0,'tool_streaming_compatibility':'not_run'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=Path('opencode.evomap.json'))
    args=parser.parse_args()
    print(json.dumps(check(args.executable.resolve(),args.config.resolve()),indent=2))
