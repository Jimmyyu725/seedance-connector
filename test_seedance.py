import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('seedance', ROOT/'skill/scripts/seedance.py')
client = importlib.util.module_from_spec(spec); spec.loader.exec_module(client)

class ConnectorTests(unittest.TestCase):
    def payload(self):
        return {'model':client.MODEL,'duration':5,'resolution':'720p','content':[{'type':'text','text':'A sunset over the sea.'}]}

    def test_explicit_model_duration_and_media(self):
        client.validate_payload(self.payload())
        for key,value in [('model','another-model'),('duration',31),('duration',True),('resolution','4k')]:
            data=self.payload();data[key]=value
            with self.assertRaises(ValueError):client.validate_payload(data)
        data=self.payload();data['content']=[{'type':'image_url','image_url':{'url':'file:///etc/passwd'}}]
        with self.assertRaises(ValueError):client.validate_payload(data)

    def test_offline_baseline_and_modified(self):
        for file,expected in [(ROOT/'.verification/baseline-settings.json','disabled'),(ROOT/'settings.json','configured')]:
            output=io.StringIO()
            with patch.object(client,'request',side_effect=AssertionError('Unexpected network')), contextlib.redirect_stdout(output):
                self.assertEqual(client.main(['--settings',str(file),'check','--offline']),0)
            self.assertEqual(json.loads(output.getvalue())['status'],expected)

    def test_submit_requires_explicit_flag(self):
        with patch.object(client,'request',side_effect=AssertionError('Unexpected network')), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:client.main(['submit','--request','unused.json'])
        self.assertEqual(error.exception.code,2)

    def test_preparation_never_sends_or_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);prompt=p/'prompt.txt';prompt.write_text('A sunset over the sea.');out=p/'request.json'
            args=['prepare','--prompt-file',str(prompt),'--request-out',str(out)]
            with patch.object(client,'request',side_effect=AssertionError('Unexpected network')), contextlib.redirect_stdout(io.StringIO()):
                client.main(args)
                with self.assertRaises(FileExistsError):client.main(args)
            self.assertEqual(json.loads(out.read_text())['model'],client.MODEL)
            self.assertEqual(out.stat().st_mode & 0o777,0o600)

    def test_auth_is_fixed_origin_and_redirects_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'credentials.json';p.write_text(json.dumps({'api_key':'test-key'}));p.chmod(0o600)
            cfg={'enabled':True,'credential_file':str(p)};response=io.BytesIO(b'{"items":[],"total":0}');response.status=200
            with patch.object(client.urllib.request,'build_opener') as build:
                build.return_value.open.return_value=response
                status,body=client.request(cfg,'GET','/contents/generations/tasks?page_size=1')
                request=build.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url,client.BASE_URL+'/contents/generations/tasks?page_size=1')
                self.assertEqual(request.method,'GET');self.assertIsNone(request.data)
                self.assertIs(build.call_args.args[0],client.NoRedirect)
                self.assertEqual(status,200)
            with self.assertRaises(ValueError):client.request(cfg,'GET','https://unrelated.example/')
            self.assertIsNone(client.NoRedirect().redirect_request(None,None,None,None,None,None))

    def test_live_check_does_not_expose_account_tasks(self):
        private={'items':[{'prompt':'PRIVATE','video_url':'SIGNED_URL'}],'total':1};output=io.StringIO()
        with patch.object(client,'request',return_value=(200,private)),contextlib.redirect_stdout(output):client.main(['check'])
        result=json.loads(output.getvalue());self.assertEqual(result['generation_tasks_created'],0)
        self.assertEqual(result['generation_permission'],'not_tested');self.assertNotIn('PRIVATE',output.getvalue());self.assertNotIn('SIGNED_URL',output.getvalue())

if __name__=='__main__':unittest.main()
