import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useFileUpload from './useFileUpload';
import * as api from '../services/api';
import { DocumentProvider } from '../contexts/DocumentContext';

vi.mock('../services/api');

describe('useFileUpload', () => {
  it('should initialize with IDLE state', () => {
    const { result } = renderHook(() => useFileUpload(), { wrapper: DocumentProvider });
    expect(result.current.uploadState).toBe('idle');
  });

  it('should transition to SELECTED when file is selected', () => {
    const { result } = renderHook(() => useFileUpload(), { wrapper: DocumentProvider });
    
    act(() => {
      result.current.selectFile({ name: 'test.pdf', type: 'application/pdf', size: 1000 });
    });
    
    expect(result.current.uploadState).toBe('selected');
    expect(result.current.selectedFile.name).toBe('test.pdf');
  });
});
