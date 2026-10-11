// Notifications only: fetch personalized data through the normal HTTP API.
export function connectLiveUpdates(refresh) {
  let socket, retry, heartbeat, timer, stopped = false, running = false;
  let pending = false, delay = 1000;

  function schedule() {
    if (!stopped && !timer && !running) timer = setTimeout(flush, 150);
  }
  async function flush() {
    timer = undefined;
    if (stopped || !pending) return;
    pending = false;
    running = true;
    try {
      // Defer to a foreground request (navigation, login, or submitting).
      if (await refresh() === false) pending = true;
    } finally {
      running = false;
      if (pending) schedule();
    }
  }
  function invalidate() { pending = true; schedule(); }
  function connect() {
    const url = new URL('/ws/comments/', location.href);
    url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(url);
    let alive = true;
    socket.onopen = () => {
      if (stopped) { socket.close(); return; }
      delay = 1000;
      invalidate(); // Catch changes missed during loading or disconnection.
      heartbeat = setInterval(() => {
        if (!alive) { socket.close(); return; }
        alive = false;
        socket.send(JSON.stringify({ type: 'ping' }));
      }, 30000);
    };
    socket.onmessage = ({ data }) => {
      let event;
      try { event = JSON.parse(data); } catch { return; }
      if (event?.type === 'pong') alive = true;
      if (event?.type === 'comments.changed') invalidate();
    };
    socket.onclose = () => {
      clearInterval(heartbeat);
      if (!stopped) {
        retry = setTimeout(connect, delay);
        delay = Math.min(delay * 2, 30000);
      }
    };
  }
  connect();
  return () => {
    stopped = true;
    clearTimeout(retry);
    clearTimeout(timer);
    clearInterval(heartbeat);
    socket.close();
  };
}
