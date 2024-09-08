from fastapi import FastAPI
from logging_config import set_logger
from mac_address_checker.views import router as mac_router

# 他のツールのエンドポイントも同様にインポート

app = FastAPI()

# 各ツールのルーターをマウント
app.include_router(mac_router, prefix="/mac_address_checker")

# 他のツールのルーターも同様にマウント
# app.include_router(another_tool_router, prefix="/another_tool")

if __name__ == "__main__":
    import uvicorn

    set_logger()
    uvicorn.run(app, host="0.0.0.0", port=8000)
