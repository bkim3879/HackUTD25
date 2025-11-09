from fastapi import FastAPI
from routes import jira_routes, workorders

app = FastAPI(title="Dynamic Work Orders API")

app.include_router(jira_routes.router)
app.include_router(workorders.router)


@app.get("/")
def root():
    return {"message": "Backend running with Jira DWOS integration"}
