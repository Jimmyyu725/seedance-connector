#!/usr/bin/env python3
"""Publish the user's existing video API credential to shell and launchd environments."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

HOME = Path.home()
ROOT = HOME / '.config/video-generation'
CONFIG = HOME / '.config/seedance/credentials.json'

def main():
    if CONFIG.stat().st_mode & 0o077:
        raise ValueError('Credential permissions must be 600 or stricter.')
    key = json.loads(CONFIG.read_text())['api_key']
    if not isinstance(key, str) or not key or '\n' in key or '\r' in key:
        raise ValueError('Invalid credential format.')
    values = {
        'ARK_API_KEY': key, 'SEEDANCE_API_KEY': key, 'VIDEO_API_KEY': key,
        'VIDEO_API_BASE_URL': 'https://ark.cn-beijing.volces.com/api/v3',
        'VIDEO_API_MODEL': 'doubao-seedance-2-5-260628',
        'VIDEO_API_PROVIDER': 'volcengine',
    }
    ROOT.mkdir(parents=True, exist_ok=True); ROOT.chmod(0o700)
    lines = ['# Managed video API defaults. Never print this file.']
    for name, value in values.items():
        lines.append('if [ -z "${'+name+':-}" ]; then export '+name+'='+shlex.quote(value)+'; fi')
    fd, tmp = tempfile.mkstemp(prefix='.env-', dir=str(ROOT))
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write('\n'.join(lines)+'\n')
        os.chmod(tmp, 0o600); os.replace(tmp, ROOT/'default.env')
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    for name,value in values.items():
        result = subprocess.run(['/bin/launchctl','setenv',name,value],capture_output=True)
        if result.returncode:
            raise RuntimeError('launchctl setenv failed for '+name)
    print('PASS global video environment synchronized; values hidden')

if __name__ == '__main__':
    main()
