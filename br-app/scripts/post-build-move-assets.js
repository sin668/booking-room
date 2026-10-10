#!/usr/bin/env node

/**
 * Post-build script to move TUIKit assets from main package to TUIKit subpackage.
 *
 * uni-app's subpackage optimization incorrectly places TUIKit icon assets
 * in the main package's assets/ directory, even though they're only used by
 * TUIKit subpackage components. This script moves them to the correct location
 * and updates all references.
 */

const fs = require('fs');
const path = require('path');

const BUILD_DIR = path.join(__dirname, '../dist/build/mp-weixin');
const MAIN_ASSETS_DIR = path.join(BUILD_DIR, 'assets');
const TUIKIT_ASSETS_DIR = path.join(BUILD_DIR, 'TUIKit/assets');
const COMMON_ASSETS_JS = path.join(BUILD_DIR, 'common/assets.js');

function main() {
  console.log('[post-build] Moving TUIKit assets to subpackage...');

  // Check if main package assets exist
  if (!fs.existsSync(MAIN_ASSETS_DIR)) {
    console.log('[post-build] No assets/ directory in main package, skipping.');
    return;
  }

  // Create TUIKit/assets directory
  if (!fs.existsSync(TUIKIT_ASSETS_DIR)) {
    fs.mkdirSync(TUIKIT_ASSETS_DIR, { recursive: true });
  }

  // Move all asset files from main package to TUIKit subpackage
  const files = fs.readdirSync(MAIN_ASSETS_DIR);
  let movedCount = 0;

  for (const file of files) {
    const srcPath = path.join(MAIN_ASSETS_DIR, file);
    const destPath = path.join(TUIKIT_ASSETS_DIR, file);

    if (fs.statSync(srcPath).isFile()) {
      fs.copyFileSync(srcPath, destPath);
      movedCount++;
    }
  }

  console.log(`[post-build] Moved ${movedCount} asset files to TUIKit/assets/`);

  // Update common/assets.js to reference TUIKit/assets instead of /assets
  if (fs.existsSync(COMMON_ASSETS_JS)) {
    let content = fs.readFileSync(COMMON_ASSETS_JS, 'utf8');
    // Replace "/assets/" with "/TUIKit/assets/"
    content = content.replace(/"\/assets\//g, '"/TUIKit/assets/');
    fs.writeFileSync(COMMON_ASSETS_JS, content, 'utf8');
    console.log('[post-build] Updated common/assets.js paths');
  }

  // Remove the main package assets directory
  fs.rmSync(MAIN_ASSETS_DIR, { recursive: true, force: true });
  console.log('[post-build] Removed main package assets/ directory');

  // Calculate new main package size
  const mainPackageSize = getDirectorySize(BUILD_DIR, ['TUIKit']);
  console.log(`[post-build] New main package size: ${(mainPackageSize / 1024 / 1024).toFixed(2)}MB`);
}

function getDirectorySize(dirPath, excludeDirs = []) {
  let size = 0;

  function traverse(currentPath) {
    const items = fs.readdirSync(currentPath);

    for (const item of items) {
      if (excludeDirs.includes(item)) continue;

      const itemPath = path.join(currentPath, item);
      const stat = fs.statSync(itemPath);

      if (stat.isDirectory()) {
        traverse(itemPath);
      } else {
        size += stat.size;
      }
    }
  }

  traverse(dirPath);
  return size;
}

main();
