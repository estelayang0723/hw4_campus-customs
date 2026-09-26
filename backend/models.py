from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)

class PageContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    path: str = Field(default='/', max_length=300)

class CustomerContext(BaseModel):
    name: str
    email: str

class AgentDependencies(BaseModel):
    customer: CustomerContext | None = None
    page_path: str = '/'
    product_id: str | None = None

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=2000)
    page: PageContext = Field(default_factory=PageContext)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @field_validator('message')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('Message cannot be blank')
        return value.strip()

class AgentReply(BaseModel):
    reply: str = Field(min_length=1, max_length=4000)
    product_ids: list[str] = Field(default_factory=list, max_length=10)

class ProductCard(BaseModel):
    total_stock: int | None = Field(default=None, ge=0)
    product_id: str
    name: str
    price: float = Field(ge=0, allow_inf_nan=False)
    description: str
    image_url: str

class ChatReply(BaseModel):
    reply: str = Field(min_length=1, max_length=4000)
    products: list[ProductCard] = Field(default_factory=list, max_length=10)

class ProductInfo(BaseModel):
    colors: list[str] = Field(default_factory=list)
    product_id: str
    name: str
    description: str
    price: float = Field(ge=0, allow_inf_nan=False)

class ProductSearch(BaseModel):
    products: list[ProductInfo]
    total_matches: int = Field(ge=0)

class ProductLookup(BaseModel):
    status: Literal['found', 'product_not_found']
    product: ProductInfo | None = None

class SizeStock(BaseModel):
    size: str
    quantity: int = Field(ge=0)
    status: Literal['in_stock', 'out_of_stock']

class StockLookup(BaseModel):
    status: Literal['found', 'product_not_found', 'size_not_found', 'inventory_unknown']
    product_id: str
    product_name: str | None = None
    requested_size: str | None = None
    stock: list[SizeStock] = Field(default_factory=list)
    total_quantity: int | None = Field(default=None, ge=0)


class RelatedItem(BaseModel):
    product: ProductInfo
    reason: str

class RelatedProducts(BaseModel):
    status: Literal['found', 'product_not_found', 'no_matches']
    source_product_id: str
    items: list[RelatedItem] = Field(default_factory=list)
