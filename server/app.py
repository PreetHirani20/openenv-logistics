import uvicorn
from src.server import app

def main():
    # The grader will call this function to start your app
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()