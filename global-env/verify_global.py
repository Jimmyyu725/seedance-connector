#!/usr/bin/env python3
"""Verify defaults without emitting any credential values."""
import argparse
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser();p.add_argument('--expect',choices=['absent','present'],required=True);args=p.parse_args()
home=Path.home();key=json.loads((home/'.config/seedance/credentials.json').read_text())['api_key']
names=['ARK_API_KEY','SEEDANCE_API_KEY','VIDEO_API_KEY']
code='''import os,json
from pathlib import Path
key=json.loads((Path.home()/'.config/seedance/credentials.json').read_text())['api_key']
print(json.dumps({k:os.environ.get(k)==key for k in ['ARK_API_KEY','SEEDANCE_API_KEY','VIDEO_API_KEY']}))
'''
env=dict(os.environ)
for name in names+['VIDEO_API_BASE_URL','VIDEO_API_MODEL','VIDEO_API_PROVIDER']:env.pop(name,None)
shell={}
for flag in ['-c','-lc']:
 q=subprocess.run(['/bin/zsh',flag,'/usr/bin/python3 -c '+__import__('shlex').quote(code)],capture_output=True,text=True,env=env,check=True)
 shell[flag]=all(json.loads(q.stdout).values())
launch={}
for name in names:
 q=subprocess.run(['/bin/launchctl','getenv',name],capture_output=True,text=True)
 launch[name]=q.returncode==0 and q.stdout.rstrip('\n')==key
loaded=subprocess.run(['/bin/launchctl','print',f'gui/{os.getuid()}/com.jingtianyu.video-api-env'],capture_output=True).returncode==0
result={'zsh_nonlogin':shell['-c'],'zsh_login':shell['-lc'],'launchd_key_matches':all(launch.values()),'launch_agent_loaded':loaded}
expected=args.expect=='present';assert all(v==expected for v in result.values()),result
if expected:
 assert (home/'.config/video-generation/default.env').stat().st_mode & 0o777==0o600
 assert (home/'.zshenv').stat().st_mode & 0o777==0o600
 result['credential_file_mode']='600'
print('PASS '+args.expect+': '+json.dumps(result,sort_keys=True))
