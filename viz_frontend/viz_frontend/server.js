const cors_anywhere = require('cors-anywhere');

const host = 'localhost';
const port = 8080;

cors_anywhere.createServer({
  originWhitelist: [], // Allow all origins
}).listen(port, host, () => {
  console.log(`CORS Anywhere server running on http://${host}:${port}`);
});