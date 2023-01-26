import uvicorn

if __name__ == "__main__":
    uvicorn.run("example_project.asgi:application", reload=True)
