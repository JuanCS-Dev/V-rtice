import React, { forwardRef } from "react";
import styles from "./Input.module.css";

export const Input = forwardRef(
  (
    {
      label,
      error,
      hint,
      icon,
      iconPosition = "left",
      variant = "cyber",
      size = "md",
      fullWidth = false,
      className = "",
      ...props
    },
    ref,
  ) => {
    const wrapperClasses = [
      styles.wrapper,
      fullWidth && styles.fullWidth,
      className,
    ]
      .filter(Boolean)
      .join(" ");

    const inputWrapperClasses = [
      styles.inputWrapper,
      styles[variant],
      styles[size],
      error && styles.hasError,
      props.disabled && styles.disabled,
    ]
      .filter(Boolean)
      .join(" ");

    const inputClasses = [
      styles.input,
      icon && iconPosition === "left" && styles.hasIconLeft,
      icon && iconPosition === "right" && styles.hasIconRight,
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <div className={wrapperClasses}>
        {label && (
          <label className={styles.label}>
            {label}
            {props.required && <span className={styles.required}>*</span>}
          </label>
        )}

        <div className={inputWrapperClasses}>
          {icon && iconPosition === "left" && (
            <span className={styles.iconLeft}>{icon}</span>
          )}

          <input ref={ref} className={inputClasses} {...props} />

          {icon && iconPosition === "right" && (
            <span className={styles.iconRight}>{icon}</span>
          )}
        </div>

        {error && (
          <span className={styles.errorText}>
            <span className={styles.errorIcon}>⚠</span>
            {error}
          </span>
        )}

        {hint && !error && <span className={styles.hint}>{hint}</span>}
      </div>
    );
  },
);

Input.displayName = "Input";

export default Input;
