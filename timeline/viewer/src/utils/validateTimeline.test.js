import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

describe('Timeline YAML Validation', () => {
  const eventsDir = path.join(process.cwd(), '..', 'data', 'events');
  
  test('all YAML files have IDs matching their filenames', () => {
    // Skip if running in CI or events directory doesn't exist
    if (!fs.existsSync(eventsDir)) {
      console.log('Skipping YAML validation - events directory not found');
      return;
    }
    
    const files = fs.readdirSync(eventsDir)
      .filter(file => file.endsWith('.yaml'));
    
    const mismatches = [];
    
    files.forEach(file => {
      const filePath = path.join(eventsDir, file);
      const expectedId = file.replace('.yaml', '');
      
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const data = yaml.load(content);
        
        if (data.id !== expectedId) {
          mismatches.push({
            file,
            expected: expectedId,
            actual: data.id
          });
        }
      } catch (error) {
        mismatches.push({
          file,
          error: error.message
        });
      }
    });
    
    if (mismatches.length > 0) {
      const errorMsg = mismatches.map(m => 
        m.error 
          ? `${m.file}: ${m.error}`
          : `${m.file}: expected '${m.expected}', got '${m.actual}'`
      ).join('\n');
      
      throw new Error(`ID/filename mismatches found:\n${errorMsg}`);
    }
  });
  
  test('all YAML files have required fields', () => {
    // Skip if running in CI or events directory doesn't exist
    if (!fs.existsSync(eventsDir)) {
      console.log('Skipping YAML validation - events directory not found');
      return;
    }
    
    const files = fs.readdirSync(eventsDir)
      .filter(file => file.endsWith('.yaml'));
    
    const requiredFields = ['id', 'date', 'title', 'summary'];
    const missingFields = [];
    
    files.forEach(file => {
      const filePath = path.join(eventsDir, file);
      
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const data = yaml.load(content);
        
        requiredFields.forEach(field => {
          if (!data[field]) {
            missingFields.push({
              file,
              field
            });
          }
        });
      } catch (error) {
        // Parsing errors handled in separate test
      }
    });
    
    if (missingFields.length > 0) {
      const errorMsg = missingFields.map(m => 
        `${m.file}: missing field '${m.field}'`
      ).join('\n');
      
      throw new Error(`Missing required fields:\n${errorMsg}`);
    }
  });
  
  test('all YAML files are valid YAML', () => {
    // Skip if running in CI or events directory doesn't exist  
    if (!fs.existsSync(eventsDir)) {
      console.log('Skipping YAML validation - events directory not found');
      return;
    }
    
    const files = fs.readdirSync(eventsDir)
      .filter(file => file.endsWith('.yaml'));
    
    const parseErrors = [];
    
    files.forEach(file => {
      const filePath = path.join(eventsDir, file);
      
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        yaml.load(content);
      } catch (error) {
        parseErrors.push({
          file,
          error: error.message
        });
      }
    });
    
    if (parseErrors.length > 0) {
      const errorMsg = parseErrors.map(e => 
        `${e.file}: ${e.error}`
      ).join('\n');
      
      throw new Error(`YAML parsing errors:\n${errorMsg}`);
    }
  });
});