/**
 * MaximusClassificationBanner - Security Classification Footer
 *
 * Displays security classification and project information.
 * Used by: MaximusDashboard
 */

import React from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";

export const MaximusClassificationBanner = () => {
  const { t } = useTranslation();

  return (
    <div className="classification-banner">
      <span>🔒 {t("dashboard.maximus.classification.level")}</span>
      <span>|</span>
      <span>{t("dashboard.maximus.classification.platform")}</span>
      <span>|</span>
      <span>{t("dashboard.maximus.classification.project")}</span>
    </div>
  );
};

export default MaximusClassificationBanner;
