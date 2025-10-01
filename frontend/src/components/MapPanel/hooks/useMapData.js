import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

/**
 * Custom hook to manage all data fetching, state, and analysis logic for the MapPanel.
 */
export const useMapData = () => {
  // Data and filter states
  const [occurrenceData, setOccurrenceData] = useState([]);
  const [timeFilter, setTimeFilter] = useState('all');
  const [crimeTypeFilter, setCrimeTypeFilter] = useState('todos');

  // UI and loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // AI results states
  const [predictedHotspots, setPredictedHotspots] = useState([]);
  const [aiMetrics, setAiMetrics] = useState(null);

  // Statistics state
  const [statistics, setStatistics] = useState({
    totalOccurrences: 0,
    criticalZones: 0,
    activePredictions: 0
  });

  // Fetch occurrence data based on filters
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setPredictedHotspots([]);
      setPredictionError(null);

      const params = new URLSearchParams({
        periodo: timeFilter,
        tipo: crimeTypeFilter
      });

      try {
        const response = await axios.get(`http://localhost:8000/ocorrencias/heatmap?${params.toString()}`);
        const data = response.data || [];
        setOccurrenceData(data);

        // Update statistics
        setStatistics(prev => ({
          ...prev,
          totalOccurrences: data.length,
          criticalZones: data.filter(d => d.intensity > 0.7).length || 0,
          activePredictions: 0 // Reset predictions on new data
        }));

      } catch (error) {
        console.error("Falha ao buscar dados de ocorrências:", error);
        setOccurrenceData([]);
        setPredictionError("Erro ao carregar dados. Verifique a conexão.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [timeFilter, crimeTypeFilter]);

  // Predictive analysis function
  const handlePredictiveAnalysis = useCallback(async (analysisRadius, minSamples) => {
    if (occurrenceData.length < minSamples) {
      setPredictionError(`Dados insuficientes. Mínimo necessário: ${minSamples} ocorrências.`);
      return;
    }

    setIsPredicting(true);
    setPredictionError(null);
    setSuccessMessage(null);
    setPredictedHotspots([]);

    try {
      const payload = {
        occurrences: occurrenceData,
        eps_km: analysisRadius,
        min_samples: minSamples
      };

      const response = await axios.post('http://localhost:8000/predict/crime-hotspots', payload, {
        timeout: 90000,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const { hotspots, metrics } = response.data;

      setPredictedHotspots(hotspots || []);
      setAiMetrics(metrics);

      // Update statistics with AI data
      setStatistics(prev => ({
        ...prev,
        activePredictions: hotspots?.length || 0
      }));

      setSuccessMessage(`Análise concluída: ${hotspots?.length || 0} hotspots identificados.`);

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);

    } catch (error) {
      console.error("Erro na análise preditiva:", error);
      const detail = error.response?.data?.detail || "Serviço de IA indisponível ou timeout.";
      setPredictionError(`Falha na análise: ${detail}`);
    } finally {
      setIsPredicting(false);
    }
  }, [occurrenceData]);

  return {
    occurrenceData,
    timeFilter, setTimeFilter,
    crimeTypeFilter, setCrimeTypeFilter,
    isLoading,
    isPredicting,
    predictionError,
    successMessage,
    predictedHotspots,
    aiMetrics,
    statistics,
    handlePredictiveAnalysis
  };
};

export default useMapData;
