import webview
import threading
import uvicorn
import time
from main import app

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="critical")

if __name__ == '__main__':
    print("SYS_BOOT // INITIALIZING TASKER_OS...")

    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    time.sleep(1)

    window = webview.create_window(
        title='Tasker_OS', 
        url='http://127.0.0.1:8000', 
        width=1366, 
        height=768,
        background_color='#000000',
        min_size=(1024, 600)
    )

    webview.start()