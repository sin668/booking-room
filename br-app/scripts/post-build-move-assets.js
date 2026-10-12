#!/usr/bin/env node

/**
 * Post-build script to move TUIKit-only files from main package to TUIKit subpackage.
 *
 * uni-app's subpackage optimization incorrectly places:
 * 1. TUIKit icon assets in main package's assets/ directory
 * 2. common/assets.js in main package's common/ directory
 * Even though they're only used by TUIKit subpackage components.
 *
 * This script moves them to the correct location and updates all references.
 */

const fs = require('fs');
const path = require('path');

const BUILD_DIR = path.join(__dirname, '../dist/build/mp-weixin');
const MAIN_ASSETS_DIR = path.join(BUILD_DIR, 'assets');
const TUIKIT_ASSETS_DIR = path.join(BUILD_DIR, 'TUIKit/assets');
const COMMON_ASSETS_JS = path.join(BUILD_DIR, 'common/assets.js');
const TUIKIT_ASSETS_JS = path.join(BUILD_DIR, 'TUIKit/tui-assets.js');

function main() {
  console.log('[post-build] Moving TUIKit assets to subpackage...');

  let mainPackageShrunk = false;

  // Step 1: Move asset files (SVG/PNG) from main package to TUIKit subpackage
  if (fs.existsSync(MAIN_ASSETS_DIR)) {
    if (!fs.existsSync(TUIKIT_ASSETS_DIR)) {
      fs.mkdirSync(TUIKIT_ASSETS_DIR, { recursive: true });
    }

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
    fs.rmSync(MAIN_ASSETS_DIR, { recursive: true, force: true });
    console.log(`[post-build] Moved ${movedCount} asset files → TUIKit/assets/`);
    mainPackageShrunk = true;
  }

  // Step 2: Move common/assets.js to TUIKit/tui-assets.js and update paths
  if (fs.existsSync(COMMON_ASSETS_JS)) {
    let content = fs.readFileSync(COMMON_ASSETS_JS, 'utf8');
    content = content.replace(/"\/assets\//g, '"/TUIKit/assets/');
    fs.writeFileSync(TUIKIT_ASSETS_JS, content, 'utf8');
    fs.unlinkSync(COMMON_ASSETS_JS);
    console.log('[post-build] Moved common/assets.js → TUIKit/tui-assets.js');
    mainPackageShrunk = true;

    // Step 3: Update all TUIKit files that require("../../common/assets.js")
    const tuiDir = path.join(BUILD_DIR, 'TUIKit');
    let updatedCount = 0;
    updateRequires(tuiDir, tuiDir, updatedCount);
    console.log(`[post-build] Updated require paths in TUIKit files`);
  }

  if (!mainPackageShrunk) {
    console.log('[post-build] Nothing to move, skipping.');
    return;
  }

  const mainPackageSize = getDirectorySize(BUILD_DIR, ['TUIKit', 'pages-sub']);
  console.log(`[post-build] Main package size: ${(mainPackageSize / 1024 / 1024).toFixed(2)}MB`);
}

/**
 * Recursively update require paths in all .js files under dir.
 * Replaces require("...common/assets.js") with the correct relative path to TUIKit/tui-assets.js.
 */
function updateRequires(dir, tuiDir, count) {
  const items = fs.readdirSync(dir);
  for (const item of items) {
    const itemPath = path.join(dir, item);
    const stat = fs.statSync(itemPath);
    if (stat.isDirectory()) {
      updateRequires(itemPath, tuiDir, count);
    } else if (item.endsWith('.js')) {
      let content = fs.readFileSync(itemPath, 'utf8');
      if (!content.includes('common/assets')) continue;

      const fileDir = path.dirname(itemPath);
      const relPath = path.relative(fileDir, TUIKIT_ASSETS_JS);
      const requirePath = relPath.startsWith('.') ? relPath : './' + relPath;

      content = content.replace(
        /require\("[^"]*common\/assets\.js"\)/g,
        `require("${requirePath}")`
      );
      fs.writeFileSync(itemPath, content, 'utf8');
    }
  }
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
