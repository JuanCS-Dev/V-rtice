/**
 * useBrainActivity - MAXIMUS AI Brain Activity Hook
 *
 * Simulates AI brain activity stream with random events.
 * In production, this would be replaced with real-time WebSocket.
 *
 * @returns {Array} brainActivity - Array of AI activity events (max 50)
 */

import { useState, useEffect } from "react";
import { formatTime } from "@/utils/dateHelpers";

const ACTIVITY_INTERVAL = 8000; // 8s
const ACTIVITY_PROBABILITY = 0.7; // 70% chance
const MAX_ACTIVITY_ITEMS = 50;

const ACTIVITY_TYPES = [
  {
    type: "ORÁCULO",
    action: "Scanning codebase for improvements...",
    severity: "info",
  },
  {
    type: "EUREKA",
    action: "Pattern detection: Analyzing file signatures",
    severity: "info",
  },
  {
    type: "CORE",
    action: "Chain-of-thought reasoning initiated",
    severity: "success",
  },
  { type: "ADR", action: "Playbook execution completed", severity: "success" },
  {
    type: "ORÁCULO",
    action: "Suggestion generated: Security enhancement",
    severity: "warning",
  },
  {
    type: "EUREKA",
    action: "IOC extracted: Suspicious domain detected",
    severity: "critical",
  },
];

export const useBrainActivity = () => {
  const [brainActivity, setBrainActivity] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > ACTIVITY_PROBABILITY) {
        const randomActivity =
          ACTIVITY_TYPES[Math.floor(Math.random() * ACTIVITY_TYPES.length)];
        const newActivity = {
          id: Date.now(),
          ...randomActivity,
          timestamp: formatTime(new Date(), "--:--:--"),
        };
        setBrainActivity((prev) =>
          [newActivity, ...prev].slice(0, MAX_ACTIVITY_ITEMS),
        );
      }
    }, ACTIVITY_INTERVAL);

    return () => clearInterval(interval);
  }, []);

  return brainActivity;
};

export default useBrainActivity;
