import logging
from utils import util
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request,status
from fastapi.exceptions import RequestValidationError
from utils.dependencies import middlewares
from middleware.http import LoggingMiddleware
from routers import auth, admin, customer, payment, transaction,notification,product,configuration

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(debug=False,
    title="SMART TAP ADMIN",
    root_path="/api/v1",
    contact={
        "name": "Abiola Bello",
        "url": "https://www.linkedin.com/in/babiola",
    },
    middleware=middlewares,
)
mobileApp = FastAPI(
    title="SMART TAP MOBILE",
    middleware=middlewares,
    root_path="/api/v1",
    contact={
        "name": "Abiola Bello",
        "url": "https://www.linkedin.com/in/babiola",
    },
    )
# User API
mobileApp.include_router(auth.router,prefix="/auth")
mobileApp.include_router(customer.router,prefix="/customer")
mobileApp.include_router(payment.router,prefix="/payment")
mobileApp.include_router(product.router,prefix="/product")
mobileApp.include_router(notification.router,prefix="/notifications")
mobileApp.include_router(transaction.router,prefix="/transactions")
mobileApp.add_middleware(LoggingMiddleware)
mobileApp.mount("/static", StaticFiles(directory="templates"), name="static")
@mobileApp.exception_handler(util.UnicornException)
async def unicorn_exception_handler(request: Request, exc: util.UnicornException):
    return JSONResponse(status_code=exc.status,content=exc.name, )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]["msg"] if exc.errors() else "Invalid input"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "statusCode": str(status.HTTP_400_BAD_REQUEST),
            "statusDescription": f"{exc.errors()[0]['loc'][1]}:{first_error}",
        },
    )

# admin API
app.include_router(admin.router,prefix="/admin")
app.include_router(configuration.router,prefix="/admin")
app.include_router(customer.adminRouter,prefix="/admin")
app.include_router(notification.adminRouter,prefix="/admin")
app.include_router(payment.adminRouter,prefix="/admin")
app.include_router(product.adminRouter,prefix="/admin")
app.mount("/mobile", mobileApp)
app.mount("/static", StaticFiles(directory="templates"), name="static")
# Add the logging middleware to FastAPI
app.add_middleware(LoggingMiddleware)
@app.exception_handler(util.UnicornException)
async def unicorn_exception_handler(request: Request, exc: util.UnicornException):
    return JSONResponse(
        status_code=exc.status,
        content=exc.name,
    )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]["msg"] if exc.errors() else "Invalid input"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "statusCode": str(status.HTTP_400_BAD_REQUEST),
            "statusDescription": f"{exc.errors()[0]['loc'][1]}:{first_error}",
        },
    )
