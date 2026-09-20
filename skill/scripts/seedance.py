#!/usr/bin/env python3
"""Small Volcengine Seedance client; no external Python dependencies."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3'
MODEL = 'doubao-seedance-2-5-260628'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def settings(path):
    cfg = json.loads(Path(path).read_text())
    if cfg.get('provider') != 'volcengine' or cfg.get('model') != MODEL:
        raise ValueError('Unexpected provider or model; review settings before use.')
    return cfg


def request(cfg, method, route, payload=None):
    if not cfg.get('enabled'):
        raise ValueError('Connector is disabled.')
    if not (route == '/contents/generations/tasks?page_size=1' or route == '/contents/generations/tasks' or re.fullmatch(r'/contents/generations/tasks/[A-Za-z0-9_-]{1,160}', route)):
        raise ValueError('Unsupported API route.')
    credentials = Path(cfg['credential_file']).expanduser()
    if credentials.stat().st_mode & 0o077:
        raise ValueError('Credential file permissions must be 600 or stricter.')
    key = json.loads(credentials.read_text()).get('api_key')
    if not isinstance(key, str) or not key:
        raise ValueError('API key is missing.')
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(BASE_URL + route, data=data, method=method, headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        # Do not retry POST: a timeout may occur after the task was accepted.
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        raw = exc.read(65536).decode('utf-8', 'replace').replace(key, '[REDACTED]')
        try:
            error = json.loads(raw).get('error', {})
            detail = {'http_status': exc.code, 'code': error.get('code'), 'message': error.get('message', '')}
        except (ValueError, AttributeError):
            detail = {'http_status': exc.code, 'message': raw[:300]}
        raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from None
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeError(type(exc).__name__ + ': request outcome uncertain; do not repeat a generation request automatically.') from None


def validate_payload(data):
    if not isinstance(data, dict) or data.get('model') != MODEL:
        raise ValueError('The request must explicitly select Seedance 2.5.')
    duration = data.get('duration')
    if type(duration) is not int or not 4 <= duration <= 30:
        raise ValueError('Set an explicit duration from 4 to 30 seconds.')
    if data.get('resolution') not in ('480p', '720p', '1080p'):
        raise ValueError('Use an explicit supported resolution.')
    if not isinstance(data.get('content'), list) or not data['content']:
        raise ValueError('content must be a nonempty array.')
    for item in data['content']:
        if not isinstance(item, dict):
            raise ValueError('Invalid content item.')
        kind = item.get('type')
        if kind == 'text':
            if not isinstance(item.get('text'), str) or not item['text'].strip():
                raise ValueError('Prompt text must not be empty.')
        elif kind in ('image_url', 'video_url', 'audio_url'):
            part = item.get(kind)
            if not isinstance(part, dict) or not isinstance(part.get('url'), str):
                raise ValueError('Invalid media reference.')
            url = urlsplit(part['url'])
            if url.scheme not in ('https', 'asset') or not url.netloc or url.username or url.password:
                raise ValueError('Use an approved HTTPS URL or official asset:// identifier.')
        else:
            raise ValueError('Unsupported content type.')
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--settings', default=str(ROOT / 'settings.json'))
    subs = p.add_subparsers(dest='command', required=True)
    check = subs.add_parser('check'); check.add_argument('--offline', action='store_true')
    prep = subs.add_parser('prepare')
    prep.add_argument('--prompt-file', required=True, type=Path)
    prep.add_argument('--request-out', required=True, type=Path)
    prep.add_argument('--duration', type=int, default=5)
    prep.add_argument('--resolution', choices=['480p', '720p', '1080p'], default='720p')
    prep.add_argument('--ratio', default='16:9')
    prep.add_argument('--silent', action='store_true')
    submit = subs.add_parser('submit')
    submit.add_argument('--request', required=True, type=Path)
    submit.add_argument('--confirm-create', action='store_true')
    status = subs.add_parser('status'); status.add_argument('task_id')
    args = p.parse_args(argv)
    if args.command == 'submit' and not args.confirm_create:
        p.error('Submitting may incur charges. Obtain user approval, then use --confirm-create.')
    cfg = settings(args.settings)
    if args.command == 'check':
        if args.offline:
            result = {'status': 'configured' if cfg.get('enabled') else 'disabled', 'provider': 'volcengine', 'model': MODEL, 'network_requests': 0}
        else:
            http, body = request(cfg, 'GET', '/contents/generations/tasks?page_size=1')
            result = {'status': 'authenticated', 'http_status': http, 'model': MODEL, 'generation_permission': 'not_tested', 'generation_tasks_created': 0}
    elif args.command == 'prepare':
        data = validate_payload({'model': MODEL, 'content': [{'type': 'text', 'text': args.prompt_file.read_text()}], 'duration': args.duration, 'resolution': args.resolution, 'ratio': args.ratio, 'generate_audio': not args.silent, 'watermark': True})
        # Exclusive creation keeps an existing approved request intact.
        with args.request_out.open('x') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        args.request_out.chmod(0o600)
        result = {'status': 'prepared_not_submitted', 'request_file': str(args.request_out.resolve()), 'network_requests': 0}
    elif args.command == 'submit':
        raw = args.request.read_bytes(); data = validate_payload(json.loads(raw))
        http, body = request(cfg, 'POST', '/contents/generations/tasks', data)
        # Persist the task id immediately; no key or signed result URL is logged.
        receipt = {'task_id': body.get('id'), 'status': body.get('status', 'submitted'), 'request_sha256': hashlib.sha256(raw).hexdigest(), 'http_status': http}
        if not isinstance(receipt['task_id'], str) or not receipt['task_id']:
            raise RuntimeError('Server returned no task id; do not resubmit automatically.')
        directory = Path.home() / '.config' / 'seedance' / 'tasks'
        try:
            directory.mkdir(parents=True, exist_ok=True); directory.chmod(0o700)
            receipt_file = directory / (hashlib.sha256(receipt['task_id'].encode()).hexdigest()[:20] + '.json')
            fd = os.open(receipt_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f: json.dump(receipt, f, indent=2)
        except OSError:
            receipt['receipt_warning'] = 'Task accepted but local receipt was not saved. Preserve this task id; do not resubmit.'
        result = receipt
    else:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', args.task_id):
            raise ValueError('Invalid task id.')
        _, body = request(cfg, 'GET', '/contents/generations/tasks/' + args.task_id)
        result = {k: body[k] for k in ('id', 'status', 'content', 'usage', 'error') if k in body}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
