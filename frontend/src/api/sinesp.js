// frontend/src/api/sinesp.js
const API_BASE_URL = 'http://localhost:8000';

export const consultarPlacaApi = async (placa) => {
  try {
    const response = await fetch(`${API_BASE_URL}/veiculos/${placa}`);
    if (!response.ok) {
      // Tenta extrair uma mensagem de erro mais detalhada do backend
      const errorData = await response.json();
      throw new Error(errorData.detail || `Erro da API: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Falha ao consultar a placa:", error);
    // Retorna um objeto de erro para a UI poder mostrar uma mensagem útil
    return { error: error.message };
  }
};
