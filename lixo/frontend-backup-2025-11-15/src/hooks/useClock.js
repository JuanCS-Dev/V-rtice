/**
 * useClock - Shared Clock Hook
 *
 * Provides real-time clock updates for dashboards.
 * Used by: MaximusDashboard, OSINTDashboard
 *
 * @returns {Date} currentTime - Current time updated every second
 */

import { useState, useEffect } from "react";

export const useClock = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return currentTime;
};

export default useClock;
