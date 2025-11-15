import React from "react";
import styles from "./GeolocationPanel.module.css";

export const GeolocationPanel = ({ data }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>GEOLOCALIZAÇÃO</h3>

      <div className={styles.fields}>
        <div className={styles.field}>
          <span className={styles.label}>ENDEREÇO IP</span>
          <span className={styles.value}>{data.ip}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>PAÍS</span>
          <span className={styles.value}>{data.location.country}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>REGIÃO/ESTADO</span>
          <span className={styles.value}>{data.location.region}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>CIDADE</span>
          <span className={styles.value}>{data.location.city}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>COORDENADAS</span>
          <span className={styles.valueMono}>
            {data.location.latitude.toFixed(3)},{" "}
            {data.location.longitude.toFixed(3)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default GeolocationPanel;
