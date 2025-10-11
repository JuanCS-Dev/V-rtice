/**
 * Accessible Form Components
 * MAXIMUS Vértice - Phase 4C
 * 
 * Form components with built-in accessibility
 */

import React, { useRef, useId } from 'react';
import PropTypes from 'prop-types';

/**
 * Accessible Input - Always use this for text inputs
 * Automatically handles label association and ARIA
 */
export const Input = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  error,
  helperText,
  className = '',
  ...rest
}) => {
  const inputId = useId();
  const errorId = useId();
  const helperId = useId();

  const hasError = Boolean(error);

  return (
    <div className={`form-group ${className}`}>
      {label && (
        <label 
          htmlFor={inputId}
          className="form-label block text-sm font-medium mb-1"
        >
          {label}
          {required && <span className="text-error ml-1" aria-label="required">*</span>}
        </label>
      )}
      
      <input
        id={inputId}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={`form-input w-full px-3 py-2 border rounded-lg transition-base ${
          hasError ? 'border-error focus:ring-error' : 'border-border focus:ring-primary'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-invalid={hasError}
        aria-describedby={`${hasError ? errorId : ''} ${helperText ? helperId : ''}`.trim()}
        {...rest}
      />
      
      {error && (
        <p id={errorId} className="form-error text-error text-sm mt-1" role="alert">
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p id={helperId} className="form-helper text-text-secondary text-sm mt-1">
          {helperText}
        </p>
      )}
    </div>
  );
};

Input.propTypes = {
  label: PropTypes.string,
  type: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  error: PropTypes.string,
  helperText: PropTypes.string,
  className: PropTypes.string,
};

/**
 * Accessible Textarea
 */
export const Textarea = ({
  label,
  value,
  onChange,
  rows = 4,
  placeholder,
  required = false,
  disabled = false,
  error,
  helperText,
  className = '',
  ...rest
}) => {
  const textareaId = useId();
  const errorId = useId();
  const helperId = useId();

  const hasError = Boolean(error);

  return (
    <div className={`form-group ${className}`}>
      {label && (
        <label 
          htmlFor={textareaId}
          className="form-label block text-sm font-medium mb-1"
        >
          {label}
          {required && <span className="text-error ml-1" aria-label="required">*</span>}
        </label>
      )}
      
      <textarea
        id={textareaId}
        value={value}
        onChange={onChange}
        rows={rows}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={`form-textarea w-full px-3 py-2 border rounded-lg transition-base ${
          hasError ? 'border-error focus:ring-error' : 'border-border focus:ring-primary'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-invalid={hasError}
        aria-describedby={`${hasError ? errorId : ''} ${helperText ? helperId : ''}`.trim()}
        {...rest}
      />
      
      {error && (
        <p id={errorId} className="form-error text-error text-sm mt-1" role="alert">
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p id={helperId} className="form-helper text-text-secondary text-sm mt-1">
          {helperText}
        </p>
      )}
    </div>
  );
};

Textarea.propTypes = {
  label: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func,
  rows: PropTypes.number,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  error: PropTypes.string,
  helperText: PropTypes.string,
  className: PropTypes.string,
};

/**
 * Accessible Select
 */
export const Select = ({
  label,
  value,
  onChange,
  options = [],
  placeholder,
  required = false,
  disabled = false,
  error,
  helperText,
  className = '',
  ...rest
}) => {
  const selectId = useId();
  const errorId = useId();
  const helperId = useId();

  const hasError = Boolean(error);

  return (
    <div className={`form-group ${className}`}>
      {label && (
        <label 
          htmlFor={selectId}
          className="form-label block text-sm font-medium mb-1"
        >
          {label}
          {required && <span className="text-error ml-1" aria-label="required">*</span>}
        </label>
      )}
      
      <select
        id={selectId}
        value={value}
        onChange={onChange}
        required={required}
        disabled={disabled}
        className={`form-select w-full px-3 py-2 border rounded-lg transition-base ${
          hasError ? 'border-error focus:ring-error' : 'border-border focus:ring-primary'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-invalid={hasError}
        aria-describedby={`${hasError ? errorId : ''} ${helperText ? helperId : ''}`.trim()}
        {...rest}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      
      {error && (
        <p id={errorId} className="form-error text-error text-sm mt-1" role="alert">
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p id={helperId} className="form-helper text-text-secondary text-sm mt-1">
          {helperText}
        </p>
      )}
    </div>
  );
};

Select.propTypes = {
  label: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  options: PropTypes.arrayOf(PropTypes.shape({
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    label: PropTypes.string.isRequired,
  })),
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  error: PropTypes.string,
  helperText: PropTypes.string,
  className: PropTypes.string,
};

/**
 * Accessible Checkbox
 */
export const Checkbox = ({
  label,
  checked,
  onChange,
  disabled = false,
  error,
  className = '',
  ...rest
}) => {
  const checkboxId = useId();
  const errorId = useId();

  return (
    <div className={`form-group ${className}`}>
      <div className="flex items-center">
        <input
          id={checkboxId}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          className="form-checkbox w-4 h-4 transition-base"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          {...rest}
        />
        {label && (
          <label 
            htmlFor={checkboxId}
            className="ml-2 text-sm cursor-pointer"
          >
            {label}
          </label>
        )}
      </div>
      
      {error && (
        <p id={errorId} className="form-error text-error text-sm mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

Checkbox.propTypes = {
  label: PropTypes.string,
  checked: PropTypes.bool,
  onChange: PropTypes.func,
  disabled: PropTypes.bool,
  error: PropTypes.string,
  className: PropTypes.string,
};

export default { Input, Textarea, Select, Checkbox };
