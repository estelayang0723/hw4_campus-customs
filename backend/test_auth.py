import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend import main, auth

class AuthTests(unittest.TestCase):
    def test_flow(self):
        original = auth.connect
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'test.db'
            shutil.copy2(main.DATA / 'campus_customs.db', database)
            def connect():
                db = sqlite3.connect(database)
                db.row_factory = sqlite3.Row
                return db
            auth.connect = connect
            auth._attempts.clear()
            try:
                with TestClient(main.app) as client:
                    client.headers['X-Campus-Request'] = '1'
                    seed = {'email':'test@campuscustoms.yale.edu','password':'password'}
                    self.assertEqual(client.post('/api/auth/login',json=seed).status_code,200)
                    self.assertEqual(client.get('/api/auth/me').json()['email'],seed['email'])
                    with connect() as db:
                        self.assertTrue(db.execute('SELECT password_hash FROM users WHERE email=?',(seed['email'],)).fetchone()[0].startswith('pbkdf2_sha256$600000$'))
                    token = client.cookies.get(auth.COOKIE)
                    self.assertEqual(client.post('/api/auth/logout').status_code,204)
                    client.cookies.set(auth.COOKIE,token)
                    self.assertEqual(client.get('/api/auth/me').status_code,401)
                    client.cookies.clear()
                    body={'first_name':'New','last_name':'Student','email':'NEW@example.com','password':'a long test password','confirm_password':'a long test password'}
                    response=client.post('/api/auth/register',json=body)
                    self.assertEqual(response.status_code,201)
                    self.assertNotIn('password',response.text)
                    self.assertIn('HttpOnly',response.headers['set-cookie'])
                    self.assertIn('SameSite=strict',response.headers['set-cookie'])
                    self.assertEqual(client.get('/api/auth/me').json()['first_name'],'New')
                    self.assertEqual(client.post('/api/auth/register',json=body).status_code,409)
                    client.post('/api/auth/logout')
                    self.assertEqual(client.post('/api/auth/login',json={'email':'new@example.com','password':body['password']}).status_code,200)
                    self.assertEqual(client.post('/api/auth/login',json={**seed,'password':'wrong'}).status_code,401)
                    self.assertEqual(client.post('/api/auth/register',json={**body,'confirm_password':'different'}).status_code,422)
                    response=client.post('/api/auth/register',json={**body,'password':'x'*129})
                    self.assertEqual(response.status_code,422)
                    self.assertNotIn('x'*129,response.text)
                    self.assertEqual(client.post('/api/auth/login',json=seed,headers={'X-Campus-Request':''}).status_code,403)
                    with connect() as db:
                        row=db.execute('SELECT * FROM users WHERE email=?',('new@example.com',)).fetchone()
                        self.assertEqual(row['name'],'New Student')
                        self.assertTrue(auth.verify_password(body['password'],row['password_hash']))
                        db.execute('UPDATE auth_sessions SET expires_at=0');db.commit()
                    self.assertEqual(client.get('/api/auth/me').status_code,401)
                    auth._attempts['testclient']=[auth.time.monotonic()]*15
                    self.assertEqual(client.post('/api/auth/login',json=seed).status_code,429)
            finally:
                auth.connect=original
                auth._attempts.clear()

if __name__=='__main__': unittest.main()
