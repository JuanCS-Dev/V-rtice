import { useState, useEffect, useContext, useCallback } from "react";
import logger from "@/utils/logger";
import { AuthContext } from "../../../../contexts/AuthContext";

import { API_ENDPOINTS } from "@/config/api";
const API_BASE = API_ENDPOINTS.socialEng;

export const useSocialEngineering = () => {
  const { user, getAuthToken } = useContext(AuthContext);

  const [socialEngData, setSocialEngData] = useState({
    campaigns: [],
    templates: [],
    activeCampaign: null,
  });

  const [loading, setLoading] = useState({});

  const hasOffensivePermission =
    user?.permissions?.includes("offensive") ||
    user?.email === "juan.brainfarma@gmail.com";

  const getHeaders = useCallback(() => {
    const token = getAuthToken();
    return {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
    };
  }, [getAuthToken]);

  /**
   * Carrega templates disponíveis
   */
  const loadTemplates = useCallback(async () => {
    if (!hasOffensivePermission) return;

    setLoading((prev) => ({ ...prev, templates: true }));
    try {
      const response = await fetch(`${API_BASE}/templates`, {
        headers: getHeaders(),
      });
      const data = await response.json();

      if (response.ok) {
        setSocialEngData((prev) => ({
          ...prev,
          templates: data.templates || [],
        }));
      } else {
        logger.error("Erro ao carregar templates:", data.detail);
      }
    } catch (error) {
      logger.error("Erro ao carregar templates:", error);
    } finally {
      setLoading((prev) => ({ ...prev, templates: false }));
    }
  }, [hasOffensivePermission, getHeaders]);

  /**
   * Cria campanha de phishing
   */
  const createCampaign = useCallback(
    async (formData) => {
      if (!hasOffensivePermission) {
        alert("Permissão ofensiva necessária para criar campanhas");
        return false;
      }

      setLoading((prev) => ({ ...prev, campaign: true }));
      try {
        const emails = formData.target_emails
          .split(",")
          .map((email) => email.trim());
        const campaignData = { ...formData, target_emails: emails };

        const response = await fetch(`${API_BASE}/campaign`, {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify(campaignData),
        });

        const data = await response.json();

        if (response.ok) {
          alert(`Campanha criada: ${data.message}`);
          loadTemplates(); // Recarrega dados
          return true;
        } else {
          alert(`Erro: ${data.detail}`);
          return false;
        }
      } catch (error) {
        logger.error("Erro ao criar campanha:", error);
        alert("Erro ao criar campanha");
        return false;
      } finally {
        setLoading((prev) => ({ ...prev, campaign: false }));
      }
    },
    [hasOffensivePermission, getHeaders, loadTemplates],
  );

  /**
   * Cria treinamento de awareness
   */
  const createAwarenessCampaign = useCallback(
    async (formData) => {
      if (!hasOffensivePermission) {
        alert("Permissão necessária");
        return false;
      }

      setLoading((prev) => ({ ...prev, awareness: true }));
      try {
        const response = await fetch(`${API_BASE}/awareness`, {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify(formData),
        });

        const data = await response.json();

        if (response.ok) {
          alert(`Treinamento criado: ${data.message}`);
          return true;
        } else {
          alert(`Erro: ${data.detail}`);
          return false;
        }
      } catch (error) {
        logger.error("Erro:", error);
        alert("Erro ao criar treinamento");
        return false;
      } finally {
        setLoading((prev) => ({ ...prev, awareness: false }));
      }
    },
    [hasOffensivePermission, getHeaders],
  );

  useEffect(() => {
    if (hasOffensivePermission) {
      loadTemplates();
    }
  }, [hasOffensivePermission, loadTemplates]);

  return {
    socialEngData,
    loading,
    hasOffensivePermission,
    createCampaign,
    createAwarenessCampaign,
  };
};

export default useSocialEngineering;
