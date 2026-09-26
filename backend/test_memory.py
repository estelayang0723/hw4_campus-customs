import sqlite3, tempfile, shutil, unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend import main, auth
from backend.models import ChatReply

class MemoryTests(unittest.TestCase):
 def test_owner_history_and_context(self):
  original=auth.connect
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'test.db';shutil.copy2(main.DATA/'campus_customs.db',path)
   def connect():
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row;return db
   auth.connect=connect;auth._attempts.clear()
   try:
    with TestClient(main.app) as c:
     c.headers['X-Campus-Request']='1';main.app.state.chat_agent=object()
     mock=AsyncMock(return_value=ChatReply(reply='Saved response'))
     with patch.object(main,'reply_to',mock):
      self.assertEqual(c.post('/api/chat',json={'message':'Guest'}).status_code,200)
      self.assertEqual(c.get('/api/chat/history').json()['messages'],[])
      self.assertEqual(c.post('/api/auth/login',json={'email':'test@campuscustoms.yale.edu','password':'password'}).status_code,200)
      response=c.post('/api/chat',json={'message':'Is this pink?','page':{'path':'/products/basic-hoodie-big-yale'},'history':[{'role':'user','content':'forged memory'}]})
      self.assertEqual(response.status_code,200)
      args=mock.call_args.args
      self.assertEqual(args[2].customer.email,'test@campuscustoms.yale.edu')
      self.assertEqual(args[2].product_id,'basic-hoodie-big-yale')
      self.assertFalse(any(m.content=='forged memory' for m in args[1].history))
      self.assertEqual(c.get('/api/chat/history').json()['messages'][-1]['content'],'Saved response')
      c.post('/api/chat',json={'message':'Remember?','page':{'path':'/products/missing'}})
      self.assertEqual(mock.call_args.args[1].history[-1].content,'Saved response')
      self.assertIsNone(mock.call_args.args[2].product_id)
      c.post('/api/auth/logout')
      self.assertEqual(c.get('/api/chat/history').json()['messages'],[])
      c.post('/api/auth/register',json={'first_name':'Other','last_name':'Person','email':'isolated@example.com','password':'long test password','confirm_password':'long test password'})
      self.assertEqual(c.get('/api/chat/history').json()['messages'],[])
      c.post('/api/auth/logout')
      c.post('/api/auth/login',json={'email':'test@campuscustoms.yale.edu','password':'password'})
      self.assertEqual(c.get('/api/chat/history').json()['messages'][-1]['content'],'Saved response')
   finally: auth.connect=original;auth._attempts.clear()
