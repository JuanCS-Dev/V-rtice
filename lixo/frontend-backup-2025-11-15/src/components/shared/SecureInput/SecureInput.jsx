/**
 * SecureInput Component
 * Boris Cherny Standard - Secure input with built-in validation & sanitization
 *
 * Addresses ALL input security gaps: #9-16
 */

import React, { useState, useCallback } from "react";
import { Input } from "../Input";
import styles from "./SecureInput.module.css";

/**
 * Secure input component with automatic sanitization and validation
 *
 * @param {Object} props
 * @param {string} props.value - Current value
 * @param {Function} props.onChange - Change handler (receives sanitized value)
 * @param {Function} props.validator - Validation function from utils/validation
 * @param {Function} props.sanitizer - Sanitization function from utils/sanitization
 * @param {string} props.label - Input label
 * @param {string} props.placeholder - Placeholder text
 * @param {number} props.maxLength - Maximum length
 * @param {boolean} props.required - Is required
 * @param {boolean} props.validateOnBlur - Validate only on blur (default: true)
 * @param {boolean} props.showError - Show error message (default: true)
 * @param {string} props.errorPrefix - Prefix for error message (default: '⚠️')
 * @param {...any} props.rest - Other props passed to Input component
 *
 * @example
 * <SecureInput
 *   label="IP Address"
 *   value={ip}
 *   onChange={setIP}
 *   validator={validateIP}
 *   sanitizer={sanitizeIP}
 *   maxLength={45}
 *   placeholder="192.168.1.1"
 *   required
 * />
 */
export const SecureInput = ({
  value,
  onChange,
  validator = null,
  sanitizer = null,
  label,
  placeholder,
  maxLength = 1000,
  required = false,
  validateOnBlur = true,
  showError = true,
  errorPrefix = "⚠️",
  id,
  ...rest
}) => {
  const [error, setError] = useState(null);

  // Generate unique ID if not provided
  const inputId =
    id || `secure-input-${label?.replace(/\s/g, "-").toLowerCase()}`;
  const errorId = `${inputId}-error`;

  // Handle change with sanitization
  const handleChange = useCallback(
    (e) => {
      const rawValue = e.target?.value ?? e;

      // Sanitize if sanitizer provided
      const sanitized = sanitizer ? sanitizer(rawValue) : rawValue;

      // Update parent state
      onChange(sanitized);

      // Clear error on change (will re-validate on blur)
      if (error) {
        setError(null);
      }
    },
    [onChange, sanitizer, error],
  );

  // Handle blur with validation
  const handleBlur = useCallback(() => {
    if (!validator || !validateOnBlur) {
      return;
    }

    // Don't validate empty optional fields
    if (!required && !value?.trim()) {
      setError(null);
      return;
    }

    // Validate required empty fields
    if (required && !value?.trim()) {
      setError(`${label || "This field"} is required`);
      return;
    }

    // Run validator
    const result = validator(value);
    if (!result.valid) {
      setError(result.error);
    } else {
      setError(null);
    }
  }, [validator, validateOnBlur, value, required, label]);

  return (
    <div className={styles.container}>
      <Input
        id={inputId}
        label={label}
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        maxLength={maxLength}
        aria-required={required}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        {...rest}
      />
      {showError && error && (
        <div
          id={errorId}
          className={styles.error}
          role="alert"
          aria-live="polite"
        >
          {errorPrefix} {error}
        </div>
      )}
    </div>
  );
};

export default SecureInput;
