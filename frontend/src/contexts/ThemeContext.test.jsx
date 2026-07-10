import { render, screen, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ThemeProvider, useThemeContext } from './ThemeContext';

const TestComponent = () => {
  const { isDarkMode, toggleTheme } = useThemeContext();
  return (
    <div>
      <span data-testid="theme">{isDarkMode ? 'dark' : 'light'}</span>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  );
};

describe('ThemeContext', () => {
  it('should toggle theme mode', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );
    
    const themeSpan = screen.getByTestId('theme');
    const button = screen.getByRole('button');
    
    const initialTheme = themeSpan.textContent;
    act(() => {
      button.click();
    });
    
    expect(themeSpan.textContent).not.toBe(initialTheme);
  });
});
