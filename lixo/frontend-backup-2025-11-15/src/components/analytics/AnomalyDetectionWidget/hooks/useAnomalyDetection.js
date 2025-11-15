import { useState, useCallback } from 'react';
import { detectAnomalies } from '../../../../api/worldClassTools';

/**
 * Custom hook for the anomaly detection logic.
 */
export const useAnomalyDetection = () => {
  const [dataInput, setDataInput] = useState('');
  const [method, setMethod] = useState('isolation_forest');
  const [sensitivity, setSensitivity] = useState(0.05);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const detect = useCallback(async () => {
    if (!dataInput.trim()) {
      setError('Dados são obrigatórios');
      return;
    }

    let data;
    try {
      data = dataInput.split(',').map(val => parseFloat(val.trim())).filter(val => !isNaN(val));
      if (data.length < 10) {
        setError('Mínimo de 10 valores necessários para análise');
        return;
      }
    } catch (err) {
      setError('Formato inválido. Use números separados por vírgula.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await detectAnomalies(data, { method, sensitivity });
      setResult(response.result);
    } catch (err) {
      setError(err.message || 'Erro ao detectar anomalias');
    } finally {
      setLoading(false);
    }
  }, [dataInput, method, sensitivity]);

  const generateSampleData = useCallback(() => {
    const baseline = Array.from({ length: 40 }, () => 1.2 + Math.random() * 0.3);
    const anomalies = [15.7, 0.2, 18.3];
    const shuffled = [...baseline.slice(0, 20), anomalies[0], ...baseline.slice(20, 30), anomalies[1], ...baseline.slice(30), anomalies[2]];
    setDataInput(shuffled.map(v => v.toFixed(2)).join(', '));
  }, []);

  return {
    dataInput, setDataInput,
    method, setMethod,
    sensitivity, setSensitivity,
    loading,
    result,
    error,
    detect,
    generateSampleData
  };
};

export default useAnomalyDetection;
