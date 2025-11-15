/**
 * Language Switcher Component
 *
 * Dropdown to switch between available languages
 *
 * Features:
 * - Language detection
 * - Persistent selection (localStorage)
 * - Animated dropdown
 * - Flag icons
 * - WCAG 2.1 AA compliant (keyboard nav, ARIA, screen reader)
 */

import React, { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { LANGUAGE_METADATA } from "../../i18n/config";
import { useFocusTrap } from "../../hooks/useFocusTrap";
import { useKeyboardNavigation } from "../../hooks/useKeyboardNavigation";
import { announcer } from "../../utils/accessibility";
import "./LanguageSwitcher.css";

export const LanguageSwitcher = ({ position = "top-right" }) => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef(null);

  const currentLanguage = i18n.language || "pt-BR";
  const currentLangData =
    LANGUAGE_METADATA[currentLanguage] || LANGUAGE_METADATA["pt-BR"];

  const availableLanguages = Object.values(LANGUAGE_METADATA).filter(
    (lang) => lang.code !== currentLanguage,
  );

  // Focus trap for dropdown
  const dropdownRef = useFocusTrap({
    active: isOpen,
    autoFocus: true,
    returnFocus: true,
    onEscape: () => setIsOpen(false),
    allowOutsideClick: true,
  });

  // Keyboard navigation for language options
  const { getItemProps } = useKeyboardNavigation({
    itemCount: availableLanguages.length,
    onSelect: (index) => handleLanguageChange(availableLanguages[index].code),
    onEscape: () => setIsOpen(false),
    orientation: "vertical",
    loop: true,
    autoFocus: false,
  });

  const handleLanguageChange = (langCode) => {
    const newLangData = LANGUAGE_METADATA[langCode];
    i18n.changeLanguage(langCode);
    setIsOpen(false);

    // Announce to screen readers
    announcer.announce(
      `${t("language.change")}: ${newLangData.name}`,
      "polite",
    );
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      announcer.announce(t("language.selector"), "polite");
    }
  };

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        isOpen &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, dropdownRef]);

  return (
    <div className={`language-switcher language-switcher-${position}`}>
      <button
        ref={triggerRef}
        className="language-switcher-trigger"
        onClick={handleToggle}
        aria-label={`${t("language.current")}: ${currentLangData.name}`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls="language-listbox"
        type="button"
      >
        <span className="language-flag" aria-hidden="true">
          {currentLangData.flag}
        </span>
        <span className="language-code">{currentLanguage}</span>
        <span
          className={`language-arrow ${isOpen ? "open" : ""}`}
          aria-hidden="true"
        >
          ▼
        </span>
      </button>

      {isOpen && (
        <>
          <div
            className="language-switcher-backdrop"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <div
            ref={dropdownRef}
            id="language-listbox"
            className="language-switcher-dropdown"
            role="listbox"
            aria-label={t("language.selector")}
          >
            <div className="language-switcher-header" aria-hidden="true">
              {t("language.selector")}
            </div>

            {/* Current language */}
            <div
              className="language-option current"
              role="option"
              aria-selected="true"
              aria-current="true"
            >
              <span className="language-flag" aria-hidden="true">
                {currentLangData.flag}
              </span>
              <div className="language-info">
                <div className="language-name">{currentLangData.name}</div>
                <div className="language-native">
                  {currentLangData.nativeName}
                </div>
              </div>
              <span className="language-check" aria-hidden="true">
                ✓
              </span>
            </div>

            <div
              className="language-divider"
              role="separator"
              aria-hidden="true"
            />

            {/* Available languages */}
            {availableLanguages.map((lang, index) => (
              <button
                key={lang.code}
                {...getItemProps(index, {
                  className: "language-option",
                  onClick: () => handleLanguageChange(lang.code),
                  role: "option",
                  "aria-selected": false,
                  "aria-label": `${t("language.change")}: ${lang.name}`,
                })}
              >
                <span className="language-flag" aria-hidden="true">
                  {lang.flag}
                </span>
                <div className="language-info">
                  <div className="language-name">{lang.name}</div>
                  <div className="language-native">{lang.nativeName}</div>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default LanguageSwitcher;
