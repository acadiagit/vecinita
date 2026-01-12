import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AccessibilitySettings {
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  highContrast: boolean;
  reduceMotion: boolean;
}

interface AccessibilityContextType {
  settings: AccessibilitySettings;
  setFontSize: (size: AccessibilitySettings['fontSize']) => void;
  toggleHighContrast: () => void;
  toggleReduceMotion: () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

const fontSizeMap = {
  'small': '14px',
  'medium': '16px',
  'large': '18px',
  'extra-large': '20px',
};

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    // Load from localStorage if available
    const saved = localStorage.getItem('accessibility-settings');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return {
          fontSize: 'medium',
          highContrast: false,
          reduceMotion: false,
        };
      }
    }
    return {
      fontSize: 'medium',
      highContrast: false,
      reduceMotion: false,
    };
  });

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));

    // Apply font size
    document.documentElement.style.setProperty('--font-size', fontSizeMap[settings.fontSize]);

    // Apply high contrast
    if (settings.highContrast) {
      document.documentElement.classList.add('high-contrast');
    } else {
      document.documentElement.classList.remove('high-contrast');
    }

    // Apply reduce motion
    if (settings.reduceMotion) {
      document.documentElement.classList.add('reduce-motion');
    } else {
      document.documentElement.classList.remove('reduce-motion');
    }
  }, [settings]);

  const setFontSize = (size: AccessibilitySettings['fontSize']) => {
    setSettings((prev) => ({ ...prev, fontSize: size }));
  };

  const toggleHighContrast = () => {
    setSettings((prev) => ({ ...prev, highContrast: !prev.highContrast }));
  };

  const toggleReduceMotion = () => {
    setSettings((prev) => ({ ...prev, reduceMotion: !prev.reduceMotion }));
  };

  return (
    <AccessibilityContext.Provider
      value={{
        settings,
        setFontSize,
        toggleHighContrast,
        toggleReduceMotion,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}
