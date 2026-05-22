I'll architect this as a clean, accessible two-file solution with proper separation of concerns and UX-first design.

**pipeline.py** (Backend):
```python
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
from threading import Thread

class PostHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/posts':
            start = time.time()
            try:
                with urllib.request.urlopen('https://jsonplaceholder.typicode.com/posts') as res:
                    posts = json.loads(res.read())[:10]
                fetch_time = round(time.time() - start, 3)
                response = {'posts': posts, 'count': len(posts), 'fetch_time': fetch_time}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Server running. Access /posts endpoint.')
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), PostHandler)
    print('✓ Server running on http://localhost:8080/posts')
    server.serve_forever()
```

**index.html** (Frontend):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Posts Feed</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { margin-bottom: 24px; }
        h1 { font-size: 28px; color: #222; margin-bottom: 8px; }
        .meta { font-size: 14px; color: #666; }
        .loading { color: #999; font-style: italic; }
        .error { background: #fee; border-left: 4px solid #c33; padding: 12px; border-radius: 4px; color: #c33; margin-bottom: 16px; }
        .card { background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: box-shadow 0.2s; }
        .card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        .card-title { font-weight: 600; color: #222; margin-bottom: 8px; font-size: 16px; line-height: 1.4; }
        .card-body { color: #666; font-size: 14px; line-height: 1.5; }
        .card-meta { font-size: 12px; color: #999; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Posts Feed</h1>
            <div class="meta" id="status">Loading...</div>
        </div>
        <div id="posts"></div>
    </div>

    <script>
        const postsContainer = document.getElementById('posts');
        const statusEl = document.getElementById('status');

        async function loadPosts() {
            try {
                const fetchStart = performance.now();
                const res = await fetch('http://localhost:8080/posts');
                const data = await res.json();
                const fetchTime = ((performance.now() - fetchStart) / 1000).toFixed(3);

                statusEl.innerHTML = `<strong>${data.count}</strong> posts loaded in <strong>${fetchTime}s</strong>`;
                
                postsContainer.innerHTML = data.posts.map(post => `
                    <article class="card">
                        <h2 class="card-title">${post.title}</h2>
                        <p class="card-body">${post.body}</p>
                        <div class="card-meta">Post #${post.id} by User #${post.userId}</div>
                    </article>
                `).join('');
            } catch (err) {
                statusEl.innerHTML = '<div class="error">⚠ Connection failed. Ensure pipeline.py is running on port 8080.</div>';
            }
        }

        loadPosts();
    </script>
</body>
</html>
```

**Key UX decisions:** CORS headers enable cross-origin access, client-side fetch timer measures actual perceived performance, semantic HTML/ARIA-ready structure supports accessibility, and card hover states provide tactile feedback—all while keeping the frontend zero-dependency and openable directly in any modern browser.