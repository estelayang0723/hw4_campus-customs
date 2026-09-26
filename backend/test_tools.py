import unittest
from contextlib import closing
from backend.tools import search_products, get_product, check_stock, connect

class ToolTests(unittest.TestCase):
    def test_database_values(self):
        with closing(connect()) as db:
            for row in db.execute('SELECT product_id, description, price FROM catalogue'):
                p=get_product(row['product_id']).product
                self.assertEqual((p.description,p.price),(row['description'],row['price']))
                rows=db.execute('SELECT size,quantity FROM inventory WHERE product_id=?',(p.product_id,)).fetchall()
                self.assertEqual(check_stock(p.product_id).total_quantity,sum(r['quantity'] for r in rows))
                for r in rows:
                    stock=check_stock(p.product_id,r['size'].lower()).stock[0]
                    self.assertEqual(stock.quantity,r['quantity'])
                    self.assertEqual(stock.status,'out_of_stock' if r['quantity']==0 else 'in_stock')
    def test_missing_and_search(self):
        self.assertEqual(get_product('missing').status,'product_not_found')
        self.assertEqual(check_stock('missing').status,'product_not_found')
        self.assertEqual(check_stock('baseball-left-chest-crewneck','3XL').status,'size_not_found')
        self.assertEqual(check_stock('baseball-left-chest-crewneck','XS').stock[0].status,'out_of_stock')
        self.assertEqual(check_stock('baseball-left-chest-crewneck','small').stock[0].size,'S')
        self.assertEqual(search_products("' OR 1=1 --").total_matches,0)
        self.assertEqual(search_products('baseball left chest crewneck').products[0].product_id,'baseball-left-chest-crewneck')
        self.assertLessEqual(len(search_products('Yale').products),10)
