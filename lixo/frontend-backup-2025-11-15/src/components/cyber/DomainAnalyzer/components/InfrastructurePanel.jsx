import React from "react";
import { Badge } from "../../../shared";
import styles from "./InfrastructurePanel.module.css";

export const InfrastructurePanel = ({ data }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>INFRAESTRUTURA</h3>

      <div className={styles.fields}>
        <div className={styles.field}>
          <span className={styles.label}>IPS ASSOCIADOS</span>
          <div className={styles.list}>
            {data.ip_addresses.map((ip, index) => (
              <div key={index} className={styles.listItem}>
                {ip}
              </div>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>NAMESERVERS</span>
          <div className={styles.list}>
            {data.nameservers.map((ns, index) => (
              <div key={index} className={styles.listItem}>
                {ns}
              </div>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>CERTIFICADO SSL</span>
          <div className={styles.sslInfo}>
            <div className={styles.sslRow}>
              <span className={styles.sslLabel}>Emissor:</span>
              <span className={styles.sslValue}>{data.ssl_cert.issuer}</span>
            </div>
            <div className={styles.sslRow}>
              <span className={styles.sslLabel}>Expira:</span>
              <span className={styles.sslValue}>{data.ssl_cert.expires}</span>
            </div>
            <div className={styles.sslRow}>
              <span className={styles.sslLabel}>Status:</span>
              <Badge
                variant={data.ssl_cert.valid ? "success" : "critical"}
                size="sm"
              >
                {data.ssl_cert.valid ? "VÁLIDO" : "INVÁLIDO"}
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfrastructurePanel;
