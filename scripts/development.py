import uvicorn


def main():
    uvicorn.run(
        "planitor.main:app",
        host="0.0.0.0",
        port=5000,
        log_level="info",
        reload=True,
        reload_dirs=["./planitor"],
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
