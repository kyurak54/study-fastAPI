from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="My FastAPI Example API",
    description="A simple example API demonstrating FastAPI features.",
    version="1.0.0"
)

# 데이터 모델 정의  (Pydantic 사용)
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

# 임시 데이터베이스 (실제로는 DB 사용)
fake_db = {
    1: {"id": 1, "name": "Apple", "description": "Red fruit", "price": 1.20},
    2: {"id": 2, "name": "Banana", "description": "Yellow fruit", "price": 0.80},
}

@app.get('/papi')
async def read_root():
    """루트 엔드포인트: 환영메세지 """
    return {"message": "Welcom to My FastAPI Example API!"}

@app.get('/papi/hello')
async def read_hello():
    """간단한 인사 메세지 API"""
    return {"message", "Hello from FastAPI on /api/hello!"}


@app.get('/papi/status')
async def get_status():
    """API 상태 정보"""
    return {"status": "OK", "version": "1.0.0", "framework": "FastAPI"}

@app.get("/papi/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    """특정 ID의 아이템 조회"""
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_db[item_id]

@app.post("/papi/items/", response_model=Item)
async def create_item(item: Item):
    """새로운 아이템 생성"""
    if item.id in fake_db:
        raise HTTPException(status_code=400, detail="Item with this ID already exists")
    fake_db[item.id] = item.dict()
    return item