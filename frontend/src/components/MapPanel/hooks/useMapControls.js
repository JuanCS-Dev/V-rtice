import { useState } from 'react';

/**
 * Custom hook to manage map visualization and UI control states.
 */
export const useMapControls = () => {
  // Layer visibility states
  const [heatmapVisible, setHeatmapVisible] = useState(true);
  const [showOccurrenceMarkers, setShowOccurrenceMarkers] = useState(true);
  const [showPredictiveHotspots, setShowPredictiveHotspots] = useState(true);

  // AI analysis parameter states
  const [analysisRadius, setAnalysisRadius] = useState(2.5);
  const [minSamples, setMinSamples] = useState(5);

  return {
    heatmapVisible, setHeatmapVisible,
    showOccurrenceMarkers, setShowOccurrenceMarkers,
    showPredictiveHotspots, setShowPredictiveHotspots,
    analysisRadius, setAnalysisRadius,
    minSamples, setMinSamples
  };
};

export default useMapControls;
