#!/usr/bin/env node
/**
 * Auto Label Fixer - Phase 4 Completion
 * Automatically adds htmlFor to labels and id to inputs
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const targetDir = args[0] || 'src/components';
const dryRun = args[1] === '--dry-run';

console.log('🔧 AUTO LABEL FIXER - Phase 4');
console.log('==============================\n');

if (dryRun) {
  console.log('🔍 DRY RUN MODE - No files will be modified\n');
}

let fixedCount = 0;
let fileCount = 0;

// Find all JSX files
function findJSXFiles(dir) {
  const files = [];
  
  const items = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    
    if (item.isDirectory() && !item.name.includes('migration-backup') && item.name !== 'node_modules') {
      files.push(...findJSXFiles(fullPath));
    } else if (item.isFile() && item.name.endsWith('.jsx')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// Fix labels in a file
function fixLabelsInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  let fixCount = 0;
  
  // Pattern 1: <label>Text</label><input ... />
  // Fix: Add htmlFor to label and id to input
  
  // Find labels without htmlFor
  const labelRegex = /<label(?![^>]*htmlFor)([^>]*)>(.*?)<\/label>\s*<(input|textarea|select)([^>]*?)>/g;
  
  let match;
  let replacements = [];
  
  while ((match = labelRegex.exec(content)) !== null) {
    const [fullMatch, labelAttrs, labelText, inputType, inputAttrs] = match;
    
    // Generate unique ID based on label text
    const idBase = labelText
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    
    const uniqueId = `${inputType}-${idBase}-${Math.random().toString(36).substr(2, 5)}`;
    
    // Check if input already has id
    if (inputAttrs.includes('id=')) {
      continue;
    }
    
    const newLabel = `<label htmlFor="${uniqueId}"${labelAttrs}>${labelText}</label>`;
    const newInput = `<${inputType} id="${uniqueId}"${inputAttrs}>`;
    
    replacements.push({
      old: fullMatch,
      new: newLabel + '\n' + newInput
    });
    
    fixCount++;
  }
  
  // Apply replacements
  for (const { old, new: newText } of replacements) {
    content = content.replace(old, newText);
    modified = true;
  }
  
  if (modified && !dryRun) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ Fixed ${fixCount} labels in ${path.relative(process.cwd(), filePath)}`);
    fixedCount += fixCount;
    fileCount++;
  } else if (modified && dryRun) {
    console.log(`🔍 Would fix ${fixCount} labels in ${path.relative(process.cwd(), filePath)}`);
    fixedCount += fixCount;
  }
  
  return modified;
}

// Main
try {
  const files = findJSXFiles(targetDir);
  console.log(`📁 Found ${files.length} JSX files\n`);
  
  for (const file of files) {
    fixLabelsInFile(file);
  }
  
  console.log('\n==============================');
  console.log('📊 SUMMARY:');
  console.log(`  Files modified: ${fileCount}`);
  console.log(`  Labels fixed: ${fixedCount}`);
  
  if (dryRun) {
    console.log('\n🔄 Run without --dry-run to apply changes');
  } else {
    console.log('\n✅ All changes applied!');
    console.log('   Run: npm run lint to verify');
  }
  
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}

console.log('\n🙏 Em nome de Jesus, pela acessibilidade!');
