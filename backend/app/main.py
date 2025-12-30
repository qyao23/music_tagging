import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.schemas import ApiResponse, BizException
from app.database import engine, Base
from app.routers import api_router

app = FastAPI(title="音乐打标平台")

# 配置 CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 不使用 cookies
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
    expose_headers=["*"],  # 暴露所有响应头
)

# 注册路由
app.include_router(api_router)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册异常处理器
# 业务异常
@app.exception_handler(BizException)
async def biz_exception_handler(request: Request, exc: BizException) -> JSONResponse:
    return JSONResponse(
        status_code = 200,
        content = ApiResponse.error_response(exc.error).model_dump()
    )
# 系统未知异常
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code = 500,
        content = ApiResponse.error_response(str(exc)).model_dump()
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host = "127.0.0.1", port = 8000, reload = True)

