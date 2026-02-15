const path = require('path');

// Wrapper so you can start the backend from the repository root with
// `node src/index.js` or `npm start` (which runs that command).
const serverPath = path.join(__dirname, '..', 'app', 'backend', 'src', 'index.js');
require(serverPath);
