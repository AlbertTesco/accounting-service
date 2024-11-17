from fastapi import FastAPI
from starlette.responses import RedirectResponse

from app.handlers import project, employee, assignment

app = FastAPI()

app.include_router(project.router, prefix="/api", tags=["Projects"])
app.include_router(employee.router, prefix="/api", tags=["Employee"])
app.include_router(assignment.router, prefix="/api", tags=["Assignment"])


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")
