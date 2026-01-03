#!/bin/bash
# Start the FastAPI application using Uvicorn, serving the app 
#defined in api.main:app, and listening on all network interfaces 
#(0.0.0.0) at port 8000, making the API accessible both inside 
#and outside the container. 

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
