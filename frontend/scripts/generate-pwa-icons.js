#!/usr/bin/env node

import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const publicDir = path.join(__dirname, '../public');
const iconDir = path.join(publicDir, 'icons');
const faviconPath = path.join(publicDir, 'favicon.svg');

// Create icons directory if it doesn't exist
if (!fs.existsSync(iconDir)) {
  fs.mkdirSync(iconDir, { recursive: true });
}

console.log('Generating PWA icons...');
console.log(`Source: ${faviconPath}`);
console.log(`Output: ${iconDir}`);

// Define icon sizes
const sizes = [
  { name: 'icon-192', size: 192 },
  { name: 'icon-512', size: 512 },
  { name: 'apple-touch-icon', size: 180 },
];

// Generate icons
Promise.all(
  sizes.map(({ name, size }) => {
    const outputPath = path.join(iconDir, `${name}.png`);
    console.log(`  → Generating ${size}×${size}px (${name}.png)...`);

    return sharp(faviconPath)
      .resize(size, size, {
        fit: 'contain',
        background: { r: 255, g: 255, b: 255, alpha: 1 },
      })
      .png()
      .toFile(outputPath)
      .then(() => {
        console.log(`     ✓ Created ${name}.png`);
      });
  })
)
  .then(() => {
    console.log('\n✓ All PWA icons generated successfully!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n✗ Error generating icons:', error);
    process.exit(1);
  });
