import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
from urllib.error import URLError

class ResponseCache:
    """Simple in-memory cache with TTL."""
    def __init__(self, ttl=60):
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}
    
    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = time.time()

cache = ResponseCache(ttl=60)

class PostHandler(BaseHTTPRequestHandler):
    """HTTP handler for posts endpoint with caching and retry logic."""
    
    def do_GET(self):
        if self.path == '/':
            self._handle_posts_request()
        elif self.path == '/health':
            self._handle_health()
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """CORS preflight support."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _handle_health(self):
        """Lightweight health check endpoint."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'max-age=5')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    
    def _handle_posts_request(self):
        """Fetch posts with caching and error resilience."""
        cache_key = 'posts_top10'
        cached = cache.get(cache_key)
        
        if cached:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'max-age=60, public')
            self.send_header('X-Cache', 'HIT')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(cached).encode())
            return
        
        start_time = time.time()
        try:
            posts_data = self._fetch_posts_with_retry()
            fetch_time = round(time.time() - start_time, 3)
            
            response = {
                "posts": posts_data,
                "record_count": len(posts_data),
                "fetch_time_seconds": fetch_time
            }
            
            cache.set(cache_key, response)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'max-age=60, public')
            self.send_header('X-Cache', 'MISS')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self._handle_error(e)
    
    def _fetch_posts_with_retry(self, max_retries=2):
        """Fetch posts from JSONPlaceholder with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(
                    'https://jsonplaceholder.typicode.com/posts',
                    timeout=5
                ) as res:
                    all_posts = json.loads(res.read().decode())
                    return all_posts[:10]
            except URLError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise e
    
    def _handle_error(self, error):
        """Structured error response."""
        error_msg = str(error)
        status = 502 if 'timeout' in error_msg.lower() else 503
        
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache, no-store')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "error": error_msg,
            "status": status,
            "record_count": 0,
            "fetch_time_seconds": None
        }
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), PostHandler)
    print("✓ Server running on http://localhost:8080")
    print("✓ Endpoints: / (posts), /health (status check)")
    print("✓ Cache TTL: 60s | Timeout: 5s | Max retries: 2")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server shutdown clean")
        server.shutdown()