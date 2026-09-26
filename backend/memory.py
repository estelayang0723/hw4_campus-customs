"""Owner-scoped persistent chat turns. Credentials never enter history."""
import json
from contextlib import closing
from urllib.parse import unquote
if __package__:
    from . import auth
    from .models import AgentDependencies, CustomerContext, ChatMessage
else:
    import auth
    from models import AgentDependencies, CustomerContext, ChatMessage


def initialize():
    with closing(auth.connect()) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS chat_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_message TEXT NOT NULL, assistant_reply TEXT NOT NULL,
            products_json TEXT NOT NULL, page_path TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
        db.execute('CREATE INDEX IF NOT EXISTS chat_turns_user ON chat_turns(user_id,id)')


def history(user_id, limit=50):
    with closing(auth.connect()) as db:
        rows=db.execute('SELECT * FROM chat_turns WHERE user_id=? ORDER BY id DESC LIMIT ?', (user_id,limit)).fetchall()
    messages=[]
    with closing(auth.connect()) as db:
        totals = dict(db.execute('SELECT product_id,SUM(quantity) FROM inventory GROUP BY product_id').fetchall())
    for row in reversed(rows):
        cards=json.loads(row['products_json'])
        for card in cards: card['total_stock']=totals.get(card['product_id'])
        messages.extend([{'role':'user','content':row['user_message']},
                         {'role':'assistant','content':row['assistant_reply'],'products':cards}])
    return messages


def dependencies(user, page):
    product_id=None
    if page.path.startswith('/products/'):
        candidate=unquote(page.path[len('/products/'):])
        with closing(auth.connect()) as db:
            row=db.execute('SELECT product_id FROM catalogue WHERE product_id=?',(candidate,)).fetchone()
            if row: product_id=row['product_id']
    return AgentDependencies(customer=CustomerContext(name=user['name'],email=user['email']) if user else None,
                             page_path=page.path,product_id=product_id)


def save(user_id, payload, reply):
    with closing(auth.connect()) as db, db:
        db.execute('INSERT INTO chat_turns(user_id,user_message,assistant_reply,products_json,page_path) VALUES(?,?,?,?,?)',
                   (user_id,payload.message,reply.reply,json.dumps([p.model_dump() for p in reply.products]),payload.page.path))
