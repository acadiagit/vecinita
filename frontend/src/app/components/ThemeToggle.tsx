import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

interface ThemeToggleProps {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

export function ThemeToggle({ theme, setTheme }: ThemeToggleProps) {
  const { t } = useLanguage();

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg hover:bg-accent transition-colors"
      aria-label={theme === 'light' ? t('darkMode') : t('lightMode')}
      title={theme === 'light' ? t('darkMode') : t('lightMode')}
    >
      {theme === 'light' ? (
        <Moon className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
      ) : (
        <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
      )}
    </button>
  );
}