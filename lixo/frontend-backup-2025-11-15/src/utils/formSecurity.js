/**
 * Form Security Utilities
 * Combines validation + sanitization for easy form integration
 *
 * Boris Cherny Standard - Type-safe form handling
 */

import * as validation from "./validation";
import sanitization from "./sanitization";

// ============================================================================
// SECURE INPUT HANDLERS
// ============================================================================

/**
 * Creates a secure onChange handler that sanitizes and validates
 *
 * @param {Function} setState - State setter function
 * @param {Function} validator - Validation function (optional)
 * @param {Function} sanitizer - Sanitization function (default: sanitizePlainText)
 * @param {Function} setError - Error setter function (optional)
 * @returns {Function} - Secure onChange handler
 *
 * @example
 * const handleIPChange = createSecureHandler(
 *   setIP,
 *   validation.validateIP,
 *   sanitization.sanitizeIP,
 *   setError
 * );
 */
export function createSecureHandler(
  setState,
  validator = null,
  sanitizer = sanitization.sanitizePlainText,
  setError = null,
) {
  return (event) => {
    const rawValue = event.target?.value ?? event;

    // Sanitize first
    const sanitized = sanitizer(rawValue);

    // Update state with sanitized value
    setState(sanitized);

    // Validate if validator provided
    if (validator && setError) {
      const result = validator(sanitized);
      if (!result.valid) {
        setError(result.error);
      } else {
        setError(null);
      }
    }
  };
}

/**
 * Creates a secure onBlur validator (validates on blur, not on every keystroke)
 *
 * @param {Function} getValue - Function that returns current value
 * @param {Function} validator - Validation function
 * @param {Function} setError - Error setter function
 * @returns {Function} - onBlur handler
 */
export function createSecureBlurValidator(getValue, validator, setError) {
  return () => {
    const value = getValue();
    const result = validator(value);

    if (!result.valid) {
      setError(result.error);
    } else {
      setError(null);
    }
  };
}

/**
 * Creates a secure form submission handler
 *
 * @param {Object} validations - Map of field names to { value, validator } objects
 * @param {Function} onSuccess - Called if all validations pass with sanitized data
 * @param {Function} setErrors - Error setter for form-level errors
 * @returns {Function} - Form submit handler
 *
 * @example
 * const handleSubmit = createSecureSubmitHandler(
 *   {
 *     ip: { value: ipValue, validator: validation.validateIP },
 *     port: { value: portValue, validator: validation.validatePorts }
 *   },
 *   (sanitizedData) => submitToAPI(sanitizedData),
 *   setFormErrors
 * );
 */
export function createSecureSubmitHandler(validations, onSuccess, setErrors) {
  return (event) => {
    if (event?.preventDefault) {
      event.preventDefault();
    }

    const errors = {};
    const sanitizedData = {};
    let isValid = true;

    // Validate all fields
    for (const [fieldName, config] of Object.entries(validations)) {
      const { value, validator } = config;
      const result = validator(value);

      if (!result.valid) {
        errors[fieldName] = result.error;
        isValid = false;
      } else {
        sanitizedData[fieldName] = result.sanitized;
      }
    }

    // Update errors
    if (setErrors) {
      setErrors(isValid ? {} : errors);
    }

    // Call success handler if valid
    if (isValid && onSuccess) {
      onSuccess(sanitizedData);
    }

    return isValid;
  };
}

// ============================================================================
// REACT HOOK FOR SECURE FORM FIELD
// ============================================================================

/**
 * React hook for a secure form field with built-in validation and sanitization
 *
 * @param {*} initialValue - Initial field value
 * @param {Function} validator - Validation function
 * @param {Function} sanitizer - Sanitization function
 * @returns {Object} - { value, error, onChange, onBlur, isValid }
 *
 * @example
 * const ipField = useSecureField('', validation.validateIP, sanitization.sanitizeIP);
 *
 * <input
 *   value={ipField.value}
 *   onChange={ipField.onChange}
 *   onBlur={ipField.onBlur}
 * />
 * {ipField.error && <span>{ipField.error}</span>}
 */
export function useSecureField(
  initialValue = "",
  validator = null,
  sanitizer = sanitization.sanitizePlainText,
) {
  const [value, setValue] = React.useState(initialValue);
  const [error, setError] = React.useState(null);

  const onChange = React.useCallback(
    (event) => {
      const rawValue = event.target?.value ?? event;
      const sanitized = sanitizer(rawValue);
      setValue(sanitized);

      // Clear error on change
      if (error) {
        setError(null);
      }
    },
    [sanitizer, error],
  );

  const onBlur = React.useCallback(() => {
    if (validator) {
      const result = validator(value);
      setError(result.valid ? null : result.error);
    }
  }, [validator, value]);

  const isValid = error === null;

  return {
    value,
    error,
    onChange,
    onBlur,
    isValid,
    setValue,
    setError,
  };
}

// Note: Import React where this hook is used
import React from "react";

// ============================================================================
// PRE-CONFIGURED FIELD TYPES
// ============================================================================

/**
 * Field type configurations for common inputs
 */
export const FIELD_TYPES = {
  IP: {
    validator: validation.validateIP,
    sanitizer: sanitization.sanitizeIP,
    maxLength: 45, // IPv6 max length
    placeholder: "e.g., 192.168.1.1",
  },

  EMAIL: {
    validator: validation.validateEmail,
    sanitizer: sanitization.sanitizeEmail,
    maxLength: 500,
    placeholder: "email@example.com",
    type: "email",
  },

  PORT: {
    validator: validation.validatePorts,
    sanitizer: sanitization.sanitizePort,
    maxLength: 100,
    placeholder: "e.g., 80,443,8080-8090",
  },

  CVE: {
    validator: validation.validateCVE,
    sanitizer: sanitization.sanitizePlainText,
    maxLength: 50,
    placeholder: "CVE-2021-44228",
  },

  DOMAIN: {
    validator: validation.validateDomain,
    sanitizer: sanitization.sanitizeDomain,
    maxLength: 500,
    placeholder: "example.com",
  },

  URL: {
    validator: validation.validateURL,
    sanitizer: sanitization.sanitizeURL,
    maxLength: 1000,
    placeholder: "https://example.com",
    type: "url",
  },

  PHONE: {
    validator: validation.validatePhone,
    sanitizer: sanitization.sanitizePlainText,
    maxLength: 20,
    placeholder: "+1 (555) 123-4567",
    type: "tel",
  },

  USERNAME: {
    validator: validation.validateUsername,
    sanitizer: sanitization.sanitizePlainText,
    maxLength: 100,
    placeholder: "username",
  },

  NMAP_ARGS: {
    validator: validation.validateNmapArgs,
    sanitizer: sanitization.sanitizeCommandArgs,
    maxLength: 500,
    placeholder: "-sV -A",
  },

  SEARCH: {
    validator: (value) =>
      validation.validateText(value, {
        minLength: 2,
        maxLength: 1000,
        fieldName: "Search query",
      }),
    sanitizer: sanitization.sanitizeSearchQuery,
    maxLength: 1000,
    placeholder: "Search...",
  },
};

/**
 * Creates a field hook with pre-configured type
 *
 * @param {string} fieldType - Key from FIELD_TYPES
 * @param {*} initialValue - Initial value
 * @returns {Object} - Same as useSecureField
 *
 * @example
 * const ipField = useTypedField('IP', '');
 */
export function useTypedField(fieldType, initialValue = "") {
  const config = FIELD_TYPES[fieldType];
  if (!config) {
    throw new Error(`Unknown field type: ${fieldType}`);
  }

  return useSecureField(initialValue, config.validator, config.sanitizer);
}

// ============================================================================
// INPUT PROPS GENERATOR
// ============================================================================

/**
 * Generates secure input props with all security measures
 *
 * @param {string} fieldType - Field type from FIELD_TYPES
 * @param {Object} field - Field object from useSecureField
 * @param {Object} additionalProps - Additional props to merge
 * @returns {Object} - Props to spread on input element
 *
 * @example
 * const ipField = useTypedField('IP');
 *
 * <input {...getSecureInputProps('IP', ipField, { id: 'ip-input' })} />
 */
export function getSecureInputProps(fieldType, field, additionalProps = {}) {
  const config = FIELD_TYPES[fieldType];

  return {
    value: field.value,
    onChange: field.onChange,
    onBlur: field.onBlur,
    maxLength: config.maxLength,
    placeholder: config.placeholder,
    type: config.type || "text",
    "aria-invalid": !field.isValid,
    "aria-describedby": field.error ? `${additionalProps.id}-error` : undefined,
    ...additionalProps,
  };
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  createSecureHandler,
  createSecureBlurValidator,
  createSecureSubmitHandler,
  useSecureField,
  useTypedField,
  getSecureInputProps,
  FIELD_TYPES,
};
