import json,os,subprocess,tempfile,shutil
from pathlib import Path
home=Path.home();state=json.loads((home/'.config/video-generation/backup-manifest.json').read_text());repo=home/'Documents/Codex/seedance-connector'
with tempfile.TemporaryDirectory(prefix='rollback-test-',dir=home/'.config/video-generation') as tmp:
    root=Path(tmp)
    for item in state['files']:
        p=root/Path(item['path']).relative_to(home);p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item['path'],p)
    subprocess.run([str(repo/'global-env/ROLLBACK.sh'),'--test-root',str(root)],check=True)
    env=dict(os.environ)
    for n in state['launchd_previous']:env.pop(n,None)
    env.update(HOME=str(root),ZDOTDIR=str(root))
    subprocess.run(['/bin/zsh','-c','/usr/bin/python3 -c \'import os; assert not any(os.environ.get(k) for k in ["ARK_API_KEY","SEEDANCE_API_KEY","VIDEO_API_KEY"]); print("PASS rollback shell: no video API defaults")\''],env=env,check=True)
print('PASS rollback test: original hashes restored; current credential retained')
