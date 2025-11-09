from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import jira_routes, rag_routes, workorders

app = FastAPI(title="Dynamic Work Orders API")

# Allow local dev UIs to call the API directly (e.g., Vite on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jira_routes.router)
app.include_router(rag_routes.router)
app.include_router(workorders.router)


@app.get("/")
def root():
    return {"message": "Backend running with Jira DWOS integration"}
