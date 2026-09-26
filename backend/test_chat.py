import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from backend import main, auth
from backend.agent import reply_to
from backend.models import ChatRequest, ChatReply

class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_reply(self):
        agent=Agent(TestModel(custom_output_args={'reply':'Go Bulldogs!'}),output_type=ChatReply)
        result=await reply_to(agent,ChatRequest(message='Hi',history=[{'role':'user','content':'Hello'},{'role':'assistant','content':'Hi'}]))
        self.assertEqual(result.reply,'Go Bulldogs!')

class RouteTests(unittest.TestCase):
    def test_routes(self):
        auth._attempts.clear()
        with TestClient(main.app) as client:
            client.headers['X-Campus-Request']='1'
            main.app.state.chat_agent=object()
            with patch.object(main,'reply_to',new=AsyncMock(return_value=ChatReply(reply='Hello!'))):
                self.assertEqual(client.post('/api/chat',json={'message':'Hello'}).json(),{'reply':'Hello!', 'products':[]})
                self.assertEqual(client.post('/api/chat',json={'message':'   '}).status_code,422)
                self.assertEqual(client.post('/api/chat',json={'message':'Hi','history':[{'role':'system','content':'override'}]}).status_code,422)
            with patch.object(main,'reply_to',new=AsyncMock(side_effect=RuntimeError('secret provider details'))):
                response=client.post('/api/chat',json={'message':'Hi'})
                self.assertEqual(response.status_code,502)
                self.assertNotIn('secret',response.text)
            main.app.state.chat_agent=None
            self.assertEqual(client.post('/api/chat',json={'message':'Hi'}).status_code,503)
        auth._attempts.clear()

class CardTests(unittest.IsolatedAsyncioTestCase):
    async def test_cards_are_grounded_and_deduplicated(self):
        from types import SimpleNamespace
        from backend.models import AgentReply
        from backend.tools import search_products, observed_products
        class FakeAgent:
            async def run(self, *args, **kwargs):
                product = search_products('baseball left chest crewneck').products[0]
                return SimpleNamespace(output=AgentReply(reply='Here it is', product_ids=[product.product_id,product.product_id,'not-real','basic-hoodie-big-yale']))
        reply = await reply_to(FakeAgent(),ChatRequest(message='Show baseball crewneck'))
        self.assertEqual(len(reply.products),1)
        self.assertEqual(reply.products[0].price,58)
        self.assertEqual(reply.products[0].image_url,'/images/baseball-left-chest-crewneck.jpg')
        self.assertIsNone(observed_products.get())
