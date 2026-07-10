import { describe, it, expect } from 'vitest';
import { formatFileSize, validateFile } from './fileHelpers';

describe('fileHelpers', () => {
  describe('formatFileSize', () => {
    it('should format bytes to KB', () => {
      expect(formatFileSize(1024)).toBe('1.0 KB');
    });
    
    it('should format bytes to MB', () => {
      expect(formatFileSize(1024 * 1024)).toBe('1.00 MB');
    });
  });

  describe('validateFile', () => {
    it('should pass valid file', () => {
      const file = { name: 'test.pdf', type: 'application/pdf', size: 1000 };
      expect(validateFile(file).isValid).toBe(true);
    });

    it('should reject invalid extension', () => {
      const file = { name: 'test.exe', type: 'application/x-msdownload', size: 1000 };
      expect(validateFile(file).isValid).toBe(false);
    });

    it('should reject large files', () => {
      const file = { name: 'test.pdf', type: 'application/pdf', size: 10 * 1024 * 1024 };
      expect(validateFile(file).isValid).toBe(false);
    });
  });
});
