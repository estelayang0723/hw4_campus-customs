import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from backend import audit
from backend.models import ChatReply
from backend.tools import get_product

class AuditTests(unittest.IsolatedAsyncioTestCase):
 async def test_append_and_stop(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'audit_trail.json'
   path.write_text('{"previous":true}\n')
   prefix=path.read_bytes()
   with patch.object(audit,'AUDIT_PATH',path):
    @audit.audit_run
    async def success():
     audit.audit_tool(get_product)('baseball-left-chest-crewneck')
     return ChatReply(reply='Done')
    await success();await success()
    @audit.audit_run
    async def failure(): raise ValueError('private text')
    with self.assertRaises(ValueError): await failure()
   self.assertTrue(path.read_bytes().startswith(prefix))
   rows=[json.loads(line) for line in path.read_text().splitlines()][1:]
   self.assertEqual([r['stop_reason'] for r in rows if r['event']=='run_stop'],['completed','completed','error'])
   self.assertEqual(len({r['run_id'] for r in rows}),3)
   self.assertTrue(any(r['tool_name']=='get_product' and r['event']=='tool_result' for r in rows))
   self.assertNotIn('private text',path.read_text())
