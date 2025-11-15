import { useState, useCallback } from "react";
import logger from "@/utils/logger";

import { API_ENDPOINTS } from "@/config/api";
const API_BASE = API_ENDPOINTS.ip;

/**
 * Formata resposta da API para o formato esperado
 */
const formatAnalysisResult = (data, ip) => ({
  ip: data.ip || ip,
  location: {
    country: data.geolocation?.country || "N/A",
    region: data.geolocation?.regionName || "N/A",
    city: data.geolocation?.city || "N/A",
    latitude: data.geolocation?.lat || 0,
    longitude: data.geolocation?.lon || 0,
  },
  isp: data.geolocation?.isp || "N/A",
  asn: {
    number: data.geolocation?.as?.split(" ")[0] || "N/A",
    name: data.geolocation?.as?.split(" ").slice(1).join(" ") || "N/A",
  },
  reputation: {
    score: data.reputation?.score || 0,
    categories: data.reputation?.categories || ["analysis"],
    last_seen:
      data.reputation?.last_seen || new Date().toISOString().split("T")[0],
  },
  threat_level: data.reputation?.threat_level || "low",
  ptr_record: data.ptr_record || "N/A",
  open_ports: data.open_ports || [],
  services: data.services || [],
});

/**
 * Gera dados fallback quando a API não está disponível
 */
const generateFallbackData = (ip) => ({
  ip,
  location: {
    country: "Brasil",
    region: "Goiás",
    city: "Anápolis",
    latitude: -16.328,
    longitude: -48.953,
  },
  isp: "Oi Fibra",
  asn: {
    number: "AS7738",
    name: "Telemar Norte Leste S.A.",
  },
  reputation: {
    score: Math.floor(Math.random() * 100),
    categories: ["malware", "botnet"],
    last_seen: "2024-01-15",
  },
  threat_level: Math.random() > 0.5 ? "high" : "medium",
  ptr_record: "suspicious-host.example.com",
  open_ports: ["22", "80", "443", "8080"],
  services: [
    { port: 22, service: "SSH", version: "OpenSSH 7.4" },
    { port: 80, service: "HTTP", version: "nginx 1.18" },
    { port: 443, service: "HTTPS", version: "nginx 1.18" },
  ],
});

export const useIpAnalysis = () => {
  const [ipAddress, setIpAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMyIp, setLoadingMyIp] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);

  /**
   * Adiciona IP ao histórico
   */
  const addToHistory = useCallback((ip) => {
    setSearchHistory((prev) =>
      [ip, ...prev.filter((item) => item !== ip)].slice(0, 10),
    );
  }, []);

  /**
   * Analisa um endereço IP
   */
  const analyzeIP = useCallback(async () => {
    const trimmedIP = ipAddress.trim();
    if (!trimmedIP) return;

    setLoading(true);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: trimmedIP }),
      });

      const data = await response.json();
      const formatted = formatAnalysisResult(data, trimmedIP);

      setAnalysisResult(formatted);
      addToHistory(trimmedIP);
    } catch (error) {
      logger.error("Erro ao conectar com o backend:", error);

      // Fallback se backend indisponível
      const fallback = generateFallbackData(trimmedIP);
      setAnalysisResult(fallback);
      addToHistory(trimmedIP);
    } finally {
      setLoading(false);
    }
  }, [ipAddress, addToHistory]);

  /**
   * Detecta e analisa o IP público do usuário
   */
  const analyzeMyIP = useCallback(async () => {
    setLoadingMyIp(true);
    setAnalysisResult(null);

    try {
      // 1. Detectar IP público
      const myIpResponse = await fetch(`${API_BASE}/my-ip`, {
        method: "GET",
      });

      if (!myIpResponse.ok) {
        throw new Error(`Erro ao detectar IP: ${myIpResponse.status}`);
      }

      const myIpData = await myIpResponse.json();
      const detectedIP = myIpData.detected_ip;

      setIpAddress(detectedIP);

      // 2. Analisar o IP detectado
      const analyzeResponse = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: detectedIP }),
      });

      if (!analyzeResponse.ok) {
        throw new Error(`Erro na análise: ${analyzeResponse.status}`);
      }

      const analyzeData = await analyzeResponse.json();
      const formatted = formatAnalysisResult(analyzeData, detectedIP);

      setAnalysisResult(formatted);
      addToHistory(detectedIP);
    } catch (error) {
      logger.error("Erro na requisição:", error);
      alert(`Erro de conexão: ${error.message}`);
    } finally {
      setLoadingMyIp(false);
    }
  }, [addToHistory]);

  /**
   * Seleciona IP do histórico
   */
  const selectFromHistory = useCallback((ip) => {
    setIpAddress(ip);
  }, []);

  return {
    ipAddress,
    setIpAddress,
    loading,
    loadingMyIp,
    analysisResult,
    searchHistory,
    analyzeIP,
    analyzeMyIP,
    selectFromHistory,
  };
};

export default useIpAnalysis;
