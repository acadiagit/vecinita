import React from 'react';
import { X, Type, Contrast, Minimize2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useAccessibility } from '../context/AccessibilityContext';

interface AccessibilityPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AccessibilityPanel({ isOpen, onClose }: AccessibilityPanelProps) {
  const { t } = useLanguage();
  const { settings, setFontSize, toggleHighContrast, toggleReduceMotion } = useAccessibility();

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className="fixed top-0 right-0 h-full w-full sm:w-96 bg-card border-l border-border z-50 shadow-xl overflow-hidden"
        role="dialog"
        aria-labelledby="accessibility-title"
        aria-modal="true"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-3 sm:p-4 border-b border-border">
            <h2 id="accessibility-title" className="text-base sm:text-lg text-foreground">
              {t('accessibility')}
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-accent transition-colors"
              aria-label={t('close') || 'Close'}
            >
              <X className="w-5 h-5 text-foreground" aria-hidden="true" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-4 sm:space-y-6">
            {/* Font Size */}
            <div className="space-y-2 sm:space-y-3">
              <div className="flex items-center gap-2">
                <Type className="w-4 h-4 sm:w-5 sm:h-5 text-primary" aria-hidden="true" />
                <h3 className="text-sm sm:text-base text-foreground">{t('fontSize')}</h3>
              </div>
              <div className="space-y-2">
                <label htmlFor="font-size-select" className="sr-only">
                  {t('fontSize')}
                </label>
                <select
                  id="font-size-select"
                  value={settings.fontSize}
                  onChange={(e) => setFontSize(e.target.value as any)}
                  className="w-full px-3 py-2 text-sm sm:text-base rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  aria-label={t('fontSize')}
                >
                  <option value="small">
                    {t('small') || 'Small'} (14px)
                  </option>
                  <option value="medium">
                    {t('medium') || 'Medium'} (16px)
                  </option>
                  <option value="large">
                    {t('large') || 'Large'} (18px)
                  </option>
                  <option value="extra-large">
                    {t('extraLarge') || 'Extra Large'} (20px)
                  </option>
                </select>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  {t('fontSizeDescription') || 'Adjust the size of text throughout the application.'}
                </p>
              </div>
            </div>

            {/* High Contrast */}
            <div className="space-y-2 sm:space-y-3">
              <div className="flex items-center gap-2">
                <Contrast className="w-4 h-4 sm:w-5 sm:h-5 text-primary" aria-hidden="true" />
                <h3 className="text-sm sm:text-base text-foreground">{t('contrast')}</h3>
              </div>
              <div className="space-y-2">
                <label className="flex items-center justify-between p-2.5 sm:p-3 rounded-lg border border-border bg-background cursor-pointer hover:bg-accent transition-colors">
                  <span className="text-sm sm:text-base text-foreground">
                    {t('highContrastMode') || 'High contrast mode'}
                  </span>
                  <input
                    type="checkbox"
                    checked={settings.highContrast}
                    onChange={toggleHighContrast}
                    className="w-5 h-5 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-0"
                    aria-label={t('contrast')}
                  />
                </label>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  {t('highContrastDescription') || 'Increase color contrast for better visibility.'}
                </p>
              </div>
            </div>

            {/* Reduce Motion */}
            <div className="space-y-2 sm:space-y-3">
              <div className="flex items-center gap-2">
                <Minimize2 className="w-4 h-4 sm:w-5 sm:h-5 text-primary" aria-hidden="true" />
                <h3 className="text-sm sm:text-base text-foreground">{t('reduceMotion')}</h3>
              </div>
              <div className="space-y-2">
                <label className="flex items-center justify-between p-2.5 sm:p-3 rounded-lg border border-border bg-background cursor-pointer hover:bg-accent transition-colors">
                  <span className="text-sm sm:text-base text-foreground">
                    {t('reduceMotionMode') || 'Reduce motion'}
                  </span>
                  <input
                    type="checkbox"
                    checked={settings.reduceMotion}
                    onChange={toggleReduceMotion}
                    className="w-5 h-5 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-0"
                    aria-label={t('reduceMotion')}
                  />
                </label>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  {t('reduceMotionDescription') || 'Minimize animations and transitions.'}
                </p>
              </div>
            </div>

            {/* Keyboard Shortcuts Info */}
            <div className="space-y-2 sm:space-y-3 pt-3 sm:pt-4 border-t border-border">
              <h3 className="text-sm sm:text-base text-foreground">
                {t('keyboardShortcuts') || 'Keyboard Shortcuts'}
              </h3>
              <div className="space-y-2 text-xs sm:text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">
                    {t('sendMessage') || 'Send message'}
                  </span>
                  <kbd className="px-2 py-1 bg-muted rounded text-foreground text-xs">Enter</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">
                    {t('newLine') || 'New line'}
                  </span>
                  <kbd className="px-2 py-1 bg-muted rounded text-foreground text-xs">Shift + Enter</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">
                    {t('closePanel') || 'Close panel'}
                  </span>
                  <kbd className="px-2 py-1 bg-muted rounded text-foreground text-xs">Esc</kbd>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}