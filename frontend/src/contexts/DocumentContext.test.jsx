import { describe, it, expect } from 'vitest';
import { documentReducer, initialState } from './DocumentContext';

describe('DocumentContext Reducer', () => {
  it('should handle SET_UPLOADED_FILE', () => {
    const action = { type: 'SET_FILE', payload: { name: 'test.pdf' } };
    const state = documentReducer(initialState, action);
    expect(state.uploadedFile).toEqual({ name: 'test.pdf' });
  });

  it('should handle SET_EXTRACTION_DATA', () => {
    const action = { 
      type: 'SET_EXTRACTION_DATA', 
      payload: { extractedText: 'hello world', documentType: 'PDF' } 
    };
    const state = documentReducer(initialState, action);
    expect(state.extractedText).toBe('hello world');
    expect(state.documentType).toBe('PDF');
  });

  it('should handle RESET_CONTEXT', () => {
    const dirtyState = { ...initialState, uploadedFile: { name: 'test.pdf' } };
    const state = documentReducer(dirtyState, { type: 'RESET' });
    expect(state).toEqual(initialState);
  });
});
