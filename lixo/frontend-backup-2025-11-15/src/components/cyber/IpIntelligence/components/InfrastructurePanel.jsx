import React from "react";
import styles from "./InfrastructurePanel.module.css";

export const InfrastructurePanel = ({ data }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>INFRAESTRUTURA</h3>

      <div className={styles.fields}>
        <div className={styles.field}>
          <span className={styles.label}>ISP</span>
          <span className={styles.value}>{data.isp}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>ASN</span>
          <span className={styles.valueMono}>{data.asn.number}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>ORG ASN</span>
          <span className={styles.value}>{data.asn.name}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>PTR RECORD</span>
          <span className={styles.valueMono}>{data.ptr_record}</span>
        </div>
      </div>
    </div>
  );
};

export default InfrastructurePanel;
