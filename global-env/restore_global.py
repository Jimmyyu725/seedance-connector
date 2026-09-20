#!/usr/bin/env python3
"""Restore the recorded prior configuration; test mode touches only mapped copies."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

p=argparse.ArgumentParser();p.add_argument('--test-root',type=Path);a=p.parse_args()
m=Path.home()/'.config/video-generation/backup-manifest.json';state=json.loads(m.read_text());home=Path(state['home'])
def target(item):
    source=Path(item['path'])
    return a.test_root/source.relative_to(home) if a.test_root else source
# Refuse to replace files edited since this installation.
for item in state['files']:
    f=target(item)
    if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=item['installed_sha256']:
        raise SystemExit('Configuration changed since installation; preserve it before rollback: '+str(f))
rescue=Path(state['backup'])/('rescue-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));rescue.mkdir(mode=0o700)
for i,item in enumerate(state['files']):
    shutil.copy2(target(item),rescue/(str(i)+'.before-restore'));(rescue/(str(i)+'.before-restore')).chmod(0o600)
if not a.test_root:
    subprocess.run(['/bin/launchctl','bootout',f'gui/{os.getuid()}/{state["label"]}'],capture_output=True)
    for name,value in state['launchd_previous'].items():
        command=['/bin/launchctl','unsetenv',name] if value is None else ['/bin/launchctl','setenv',name,value]
        subprocess.run(command,capture_output=True,check=True)
for item in state['files']:
    f=target(item)
    if item['existed']:
        original=Path(item['backup']);assert hashlib.sha256(original.read_bytes()).hexdigest()==item['sha256']
        shutil.copy2(original,f);f.chmod(item['mode'])
        assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']
    else:
        f.unlink();assert not f.exists()
print('PASS rollback: '+('copied files restored; live environment unchanged' if a.test_root else 'prior files and launchd environment restored; credential retained'))
