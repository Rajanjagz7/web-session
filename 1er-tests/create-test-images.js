const fs = require('fs');
const path = require('path');

const imgDir = path.join(__dirname, 'test-images');
if (!fs.existsSync(imgDir)) {
  fs.mkdirSync(imgDir, { recursive: true });
}

// A valid 100x100 PNG buffer
// Minimal valid PNG:
function createDummyPng(filePath, label) {
  // Let's create a minimal valid PNG
  // 1x1 pixel PNG raw bytes
  const pngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAALUlEQVR42u3BAQ0AAADCoPdPbQ8HFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeBg0QAAB7bXy7wAAAABJRU5ErkJggg==';
  fs.writeFileSync(filePath, Buffer.from(pngBase64, 'base64'));
  console.log(`Created image: ${filePath}`);
}

createDummyPng(path.join(imgDir, 'energy-bill-coastal-enterprises.png'), 'Energy Bill');
createDummyPng(path.join(imgDir, 'energy-bill-sydney-tech.png'), 'Energy Bill Tech');
createDummyPng(path.join(imgDir, 'pre-installation-water-heater.jpg'), 'Pre Installation');
createDummyPng(path.join(imgDir, 'heat-pump-nameplate.jpg'), 'Heat Pump Nameplate');
createDummyPng(path.join(imgDir, 'air-conditioner-outdoor-unit.jpg'), 'AC Outdoor Unit');
