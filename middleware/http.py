from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request
import logging
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request details
        request_start_time = time.time()
        logging.info(f"Request: {request.method} {request.url}")
        logging.info(f"Headers: {request.headers}")
        
        if request.method in ["POST", "PUT", "PATCH"]:
            request_body = await request.body()
            logging.info(f"Request Body: {request_body.decode('utf-8')}")

        # Process request and get the response
        response = await call_next(request)
        
        # Capture the response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Extract the response body
        #response_body = [section async for section in response.body_iterator]
        #response.body_iterator = iter(response_body)

        # Log response details
        request_end_time = time.time()
        process_time = request_end_time - request_start_time
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response Body: {response_body}")
        #logging.info(f"Response Body: {b''.join(response_body).decode('utf-8')}")
        logging.info(f"Processed in {process_time:.4f} seconds")

        return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers))

        return response
