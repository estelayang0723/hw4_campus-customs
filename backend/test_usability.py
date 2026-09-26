import unittest, tempfile, shutil, sqlite3
from pathlib import Path
from unittest.mock import patch
from backend.context import truncate_history
from backend.models import ChatMessage
from backend import tools, main
from backend.tools import suggest_related_products

class UsabilityTests(unittest.TestCase):
 def test_context(self):
  messages=[ChatMessage(role=role,content=str(i)+'x'*1999) for i in range(10) for role in ('user','assistant')]
  kept=truncate_history(messages)
  self.assertEqual(kept,messages[-4:])
  self.assertLessEqual(sum(len(m.content) for m in kept),8000)
  self.assertEqual(truncate_history([ChatMessage(role='assistant',content='orphan')]),[])
  self.assertEqual(len(truncate_history([ChatMessage(role=role,content='short') for _ in range(20) for role in ('user','assistant')])),12)
 def test_recommendations_and_badges(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'test.db';shutil.copy2(tools.DATABASE,path)
   with sqlite3.connect(path) as db:
    db.execute("UPDATE inventory SET quantity=0 WHERE product_id='baseball-left-chest-crewneck'")
    db.execute("DELETE FROM inventory WHERE product_id='basic-hoodie-big-yale'")
   def connect():
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row;return db
   with patch.object(tools,'DATABASE',path),patch.object(main,'connect',connect):
    products={p['product_id']:p for p in main.products()}
    self.assertEqual(products['baseball-left-chest-crewneck']['total_stock'],0)
    self.assertIsNone(products['basic-hoodie-big-yale']['total_stock'])
    result=suggest_related_products('champion-full-zip-hood',3)
    self.assertTrue(result.items)
    self.assertLessEqual(len(result.items),3)
    for item in result.items:
     self.assertNotEqual(item.product.product_id,'champion-full-zip-hood')
     self.assertGreater(products[item.product.product_id]['total_stock'],0)
     self.assertEqual(item.product.price,products[item.product.product_id]['price'])
    self.assertEqual(suggest_related_products('missing').status,'product_not_found')
