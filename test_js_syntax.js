// Simple syntax test
try {
    // Read and evaluate the brand compliance validator
    const fs = require('fs');
    const content = fs.readFileSync('static/js/brand-compliance-validator.js', 'utf8');
    
    // Count parentheses
    const openParens = (content.match(/\(/g) || []).length;
    const closeParens = (content.match(/\)/g) || []).length;
    
    console.log(`Open parentheses: ${openParens}`);
    console.log(`Close parentheses: ${closeParens}`);
    console.log(`Difference: ${openParens - closeParens}`);
    
    // Try to parse as JavaScript (basic check)
    new Function(content);
    console.log('✅ JavaScript syntax is valid');
    
} catch (error) {
    console.error('❌ JavaScript syntax error:', error.message);
}