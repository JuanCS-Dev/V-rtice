import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { useFocusTrap } from "../../../hooks/useFocusTrap";
import styles from "./Modal.module.css";

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  variant = "cyber",
  size = "md",
  footer,
  closeOnEscape = true,
  closeOnBackdrop = true,
  className = "",
  ariaLabel,
  ariaDescribedBy,
  ...props
}) => {
  // Focus trap for accessibility
  const modalRef = useFocusTrap({
    active: isOpen,
    autoFocus: true,
    returnFocus: true,
    onEscape: closeOnEscape ? onClose : null,
    allowOutsideClick: false,
  });

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modalClasses = [styles.modal, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(" ");

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && closeOnBackdrop) {
      onClose();
    }
  };

  return (
    <div
      className={styles.backdrop}
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={modalRef}
        className={modalClasses}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel || title}
        aria-describedby={ariaDescribedBy}
        {...props}
      >
        {/* Header */}
        <div className={styles.header}>
          {title && (
            <h3 className={styles.title} id="modal-title">
              {title}
            </h3>
          )}
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close modal"
          >
            <i className="fas fa-times" aria-hidden="true"></i>
          </button>
        </div>

        {/* Body */}
        <div
          className={styles.body}
          id={ariaDescribedBy || "modal-description"}
        >
          {children}
        </div>

        {/* Footer */}
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>
  );
};

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string,
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(["cyber", "default", "dark"]),
  size: PropTypes.oneOf(["sm", "md", "lg", "xl"]),
  footer: PropTypes.node,
  closeOnEscape: PropTypes.bool,
  closeOnBackdrop: PropTypes.bool,
  className: PropTypes.string,
  ariaLabel: PropTypes.string,
  ariaDescribedBy: PropTypes.string,
};

export default Modal;
