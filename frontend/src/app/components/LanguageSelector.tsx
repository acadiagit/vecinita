import React from 'react';
import { Languages } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export function LanguageSelector() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="relative">
      <label htmlFor="language-select" className="sr-only">
        {t('language')}
      </label>
      <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg hover:bg-accent transition-colors">
        <Languages className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
        <select
          id="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value as 'en' | 'es')}
          className="bg-transparent text-foreground border-none outline-none cursor-pointer text-sm sm:text-base"
          aria-label={t('language')}
        >
          <option value="en">{t('english')}</option>
          <option value="es">{t('spanish')}</option>
        </select>
      </div>
    </div>
  );
}