"""Read-only, parameterized catalogue and inventory lookups."""
import sqlite3
import json
from contextvars import ContextVar
from contextlib import closing
from pathlib import Path
from typing import Annotated
from pydantic import Field
if __package__:
    from .audit import audit_tool
    from .models import ProductInfo, ProductSearch, ProductLookup, SizeStock, StockLookup, RelatedItem, RelatedProducts
else:
    from audit import audit_tool
    from models import ProductInfo, ProductSearch, ProductLookup, SizeStock, StockLookup, RelatedItem, RelatedProducts

observed_products: ContextVar[set[str] | None] = ContextVar("observed_products", default=None)

def remember(ids):
    seen = observed_products.get()
    if seen is not None: seen.update(ids)

DATABASE = Path(__file__).resolve().parents[1] / 'data/campus_customs.db'
FIELDS = 'product_id, name, description, price, colors'

def product_info(row):
    values = dict(row)
    values['colors'] = json.loads(values['colors'])
    return ProductInfo(**values)

def connect():
    db = sqlite3.connect(f'{DATABASE.as_uri()}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


def search_products(query: Annotated[str, Field(min_length=1, max_length=200)]) -> ProductSearch:
    """Find real products by name, product ID, garment type, or tags. Use short keywords. If multiple matches fit, ask which product; never guess an ID."""
    words = query.strip().lower().split()
    aliases = {'hoodies':'hoodie', 'shirts':'shirt', 'tees':'shirt', 'sweatshirts':'sweatshirt', 'jackets':'jacket'}
    words = [aliases.get(word, word) for word in words]
    if not words: return ProductSearch(products=[], total_matches=0)
    columns = "lower(product_id || ' ' || name || ' ' || garment_type || ' ' || search_tags)"
    where = ' AND '.join(f'instr({columns}, ?) > 0' for _ in words)
    with closing(connect()) as db:
        count = db.execute(f'SELECT count(*) FROM catalogue WHERE {where}', words).fetchone()[0]
        rows = db.execute(f'SELECT {FIELDS} FROM catalogue WHERE {where} ORDER BY name LIMIT 10', words).fetchall()
    remember(r["product_id"] for r in rows)
    return ProductSearch(products=[product_info(r) for r in rows], total_matches=count)


def get_product(product_id: Annotated[str, Field(min_length=1, max_length=200)]) -> ProductLookup:
    """Get the exact current database description and price for a known product ID. Search first if the ID is unknown."""
    with closing(connect()) as db:
        row = db.execute(f'SELECT {FIELDS} FROM catalogue WHERE product_id=?', (product_id,)).fetchone()
    if row: remember([row['product_id']])
    return ProductLookup(status='found', product=product_info(row)) if row else ProductLookup(status='product_not_found')


def check_stock(product_id: Annotated[str, Field(min_length=1, max_length=200)], size: Annotated[str, Field(max_length=40)] | None = None) -> StockLookup:
    """Read current stock for a product, optionally a specific size. Zero means out of stock; absent rows mean unknown/not listed, not zero. No color-specific inventory exists."""
    aliases = {'EXTRA SMALL':'XS','SMALL':'S','MEDIUM':'M','LARGE':'L','EXTRA LARGE':'XL','EXTRA-LARGE':'XL','2XL':'XXL','XX-LARGE':'XXL','EXTRA EXTRA LARGE':'XXL'}
    normalized = size.strip().upper() if size is not None else None
    normalized = aliases.get(normalized, normalized)
    result = dict(product_id=product_id, requested_size=normalized)
    with closing(connect()) as db:
        product = db.execute('SELECT name FROM catalogue WHERE product_id=?', (product_id,)).fetchone()
        if not product: return StockLookup(status='product_not_found', **result)
        result['product_name'] = product['name']
        rows = db.execute('SELECT size, quantity FROM inventory WHERE product_id=? ORDER BY id', (product_id,)).fetchall()
    if not rows: return StockLookup(status='inventory_unknown', **result)
    if normalized is not None:
        rows = [r for r in rows if r['size'].upper() == normalized]
        if not rows: return StockLookup(status='size_not_found', **result)
    stock = [SizeStock(size=r['size'], quantity=r['quantity'], status='out_of_stock' if r['quantity']==0 else 'in_stock') for r in rows]
    return StockLookup(status='found', stock=stock, total_quantity=sum(r.quantity for r in stock), **result)



def suggest_related_products(product_id: Annotated[str, Field(min_length=1, max_length=200)], limit: Annotated[int, Field(ge=1, le=6)] = 4) -> RelatedProducts:
    """Suggest real related or complementary items by shared catalogue tags and garment type. Excludes the source and products without positive total stock. Check requested size separately."""
    with closing(connect()) as db:
        source = db.execute('SELECT * FROM catalogue WHERE product_id=?', (product_id,)).fetchone()
        if not source: return RelatedProducts(status='product_not_found', source_product_id=product_id)
        rows = db.execute('SELECT c.* FROM catalogue c WHERE product_id != ? AND (SELECT SUM(quantity) FROM inventory i WHERE i.product_id=c.product_id)>0', (product_id,)).fetchall()
    source_tags = {t.lower() for t in json.loads(source['search_tags'])} - {'yale','campus customs'}
    ranked=[]
    for row in rows:
        overlap=source_tags & {t.lower() for t in json.loads(row['search_tags'])}
        same_type=row['garment_type']==source['garment_type']
        if not overlap and not same_type: continue
        score=len(overlap)*3 + int(same_type)*2
        reason=('Same garment type' if same_type else 'Different garment type with shared catalogue tags')
        if overlap: reason += ': ' + ', '.join(sorted(overlap)[:3])
        ranked.append((score,row['name'],row,reason))
    ranked.sort(key=lambda x:(-x[0],x[1]))
    items=[RelatedItem(product=product_info(row),reason=reason) for _,_,row,reason in ranked[:limit]]
    remember(item.product.product_id for item in items)
    return RelatedProducts(status='found' if items else 'no_matches',source_product_id=product_id,items=items)


def register_tools(agent):
    for tool in (search_products, get_product, check_stock, suggest_related_products):
        agent.tool_plain(audit_tool(tool))
    return agent
