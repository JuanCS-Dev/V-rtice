import logger from '@/utils/logger';
// Conecta-se ao backend real rodando no Docker
const API_BASE_URL = API_BASE_URL;

export const consultarPlacaApi = async (placa) => {
  try {
    const response = await fetch(`${API_BASE_URL}/veiculos/${placa}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Erro da API: ${response.statusText}`);
    }
    
    return await response.json();

  } catch (error) {
    logger.error("Falha ao consultar a placa via API:", error);
    // Propaga o erro para a UI tratar
    return { error: error.message };
  }
};
