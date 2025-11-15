/**
 * i18next Configuration
 *
 * Internationalization setup for the application
 *
 * Features:
 * - Automatic language detection
 * - Fallback language (pt-BR)
 * - Lazy loading translations
 * - Browser language detection
 * - Local storage persistence
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// Import translations
import ptBR from "./locales/pt-BR.json";
import enUS from "./locales/en-US.json";

// Language detection configuration
const languageDetectorOptions = {
  // Order of detection methods
  order: ["localStorage", "navigator", "htmlTag"],

  // Cache user language
  caches: ["localStorage"],

  // Cookie options (if using cookies)
  cookieMinutes: 10080, // 7 days

  // localStorage key
  lookupLocalStorage: "i18nextLng",

  // Check HTML tag lang attribute
  htmlTag: document.documentElement,
};

i18n
  // Detect user language
  .use(LanguageDetector)

  // Pass i18n instance to react-i18next
  .use(initReactI18next)

  // Initialize i18next
  .init({
    // Available languages
    resources: {
      "pt-BR": {
        translation: ptBR,
      },
      "en-US": {
        translation: enUS,
      },
    },

    // Fallback language
    fallbackLng: "pt-BR",

    // Supported languages
    supportedLngs: ["pt-BR", "en-US"],

    // Debug mode (only in development)
    debug: process.env.NODE_ENV === "development",

    // Interpolation options
    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Language detection
    detection: languageDetectorOptions,

    // React options
    react: {
      useSuspense: true,
      bindI18n: "languageChanged loaded",
      bindI18nStore: "added removed",
      transEmptyNodeValue: "",
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ["br", "strong", "i", "p"],
    },
  });

export default i18n;

/**
 * Available language codes
 */
export const LANGUAGES = {
  PT_BR: "pt-BR",
  EN_US: "en-US",
};

/**
 * Language metadata
 */
export const LANGUAGE_METADATA = {
  "pt-BR": {
    code: "pt-BR",
    name: "Português (Brasil)",
    flag: "🇧🇷",
    nativeName: "Português",
  },
  "en-US": {
    code: "en-US",
    name: "English (US)",
    flag: "🇺🇸",
    nativeName: "English",
  },
};
