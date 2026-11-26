#!/usr/bin/env node

/**
 * Post-build script to move TUIKit-only files from main package to TUIKit subpackage.
 *
 * uni-app's subpackage optimization incorrectly places:
 * 1. TUIKit icon assets in main package's assets/ directory
 * 2. common/assets.js in main package's common/ directory
 * 3. src/utils modules that only TUIKit components import (uni-app hoists all of
 *    src/utils into the main package)
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

// 主包里只被 TUIKit 子包引用的 JS，微信开发者工具会报「主包内不应存在主包未使用的 JS 文件」
const MOVES = [
  { from: 'utils/im-history.js', to: 'TUIKit/utils/im-history.js' },
];

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

  // Step 4: 把只被 TUIKit 用到的主包 JS 搬进子包，并重写两侧相对路径
  for (const move of MOVES) {
    if (moveMainPackageJs(move.from, move.to)) {
      mainPackageShrunk = true;
    }
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

/**
 * 把主包里的一个 JS 搬进子包：搬之前先改写它自己的相对 require（层级变了），
 * 搬完之后改写子包内指向旧路径的 require。
 */
function moveMainPackageJs(fromRel, toRel) {
  const fromPath = path.join(BUILD_DIR, fromRel);
  if (!fs.existsSync(fromPath)) return false;

  const toPath = path.join(BUILD_DIR, toRel);
  fs.mkdirSync(path.dirname(toPath), { recursive: true });

  let content = fs.readFileSync(fromPath, 'utf8');
  content = content.replace(/require\("(\.[^"]+)"\)/g, (all, spec) => {
    const target = resolveRelative(path.dirname(fromRel), spec);
    return `require("${relativize(path.dirname(toRel), target)}")`;
  });
  fs.writeFileSync(toPath, content, 'utf8');
  fs.unlinkSync(fromPath);

  let updated = 0;
  rewriteRequires(path.join(BUILD_DIR, path.dirname(toRel).split(path.sep)[0]), (spec, basedir) => {
    if (resolveRelative(basedir, spec) !== fromRel) return null;
    return relativize(basedir, toRel);
  }, () => updated++);
  console.log(`[post-build] Moved ${fromRel} → ${toRel} (rewrote ${updated} require)`);
  return true;
}

/** 相对 require → 相对构建根目录的路径 */
function resolveRelative(basedir, spec) {
  return path.normalize(path.join(basedir, spec)).split(path.sep).join('/');
}

function relativize(fromDir, targetRel) {
  const rel = path.relative(fromDir, targetRel).split(path.sep).join('/');
  return rel.startsWith('.') ? rel : `./${rel}`;
}

/** 递归改写 dir 下所有 .js 的相对 require；rewrite 返回新路径或 null 表示不改 */
function rewriteRequires(dir, rewrite, touched) {
  for (const item of fs.readdirSync(dir)) {
    const itemPath = path.join(dir, item);
    if (fs.statSync(itemPath).isDirectory()) {
      rewriteRequires(itemPath, rewrite, touched);
      continue;
    }
    if (!item.endsWith('.js')) continue;
    const content = fs.readFileSync(itemPath, 'utf8');
    const basedir = path.relative(BUILD_DIR, path.dirname(itemPath)).split(path.sep).join('/');
    let changed = false;
    const next = content.replace(/require\("(\.[^"]+)"\)/g, (all, spec) => {
      const replacement = rewrite(spec, basedir);
      if (replacement === null) return all;
      changed = true;
      touched();
      return `require("${replacement}")`;
    });
    if (changed) fs.writeFileSync(itemPath, next, 'utf8');
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
