import { apiClient } from "@/lib/api/client";

// ========= TYPES (SINESP - Brazilian Public Security) =========

export interface VehicleInfo {
  placa: string;
  marca: string;
  modelo: string;
  cor: string;
  ano: string;
  chassi?: string;
  municipio?: string;
  situacao: "regular" | "restricao" | "roubo" | "unknown";
  restricoes?: string[];
  data_consulta: string;
}

export interface CrimeType {
  codigo: string;
  descricao: string;
  categoria: "violento" | "patrimonial" | "transito" | "outros";
  gravidade: "baixa" | "media" | "alta";
}

export interface CrimeHeatmapPoint {
  lat: number;
  lng: number;
  tipo: string;
  data: string;
  gravidade: "baixa" | "media" | "alta";
  endereco?: string;
}

// ========= SINESP SERVICE =========

export const sinespService = {
  // Consulta de Veículos
  async consultarVeiculo(placa: string): Promise<VehicleInfo> {
    // Remove hífens e espaços da placa
    const placaLimpa = placa.replace(/[-\s]/g, "").toUpperCase();

    const response = await apiClient.get<VehicleInfo>(
      `/veiculos/${placaLimpa}`,
    );
    return response.data;
  },

  // Tipos de Ocorrências
  async getTiposOcorrencias(): Promise<CrimeType[]> {
    const response = await apiClient.get<CrimeType[]>("/ocorrencias/tipos");
    return response.data;
  },

  // Heatmap Criminal
  async getHeatmap(filters?: {
    tipo?: string;
    data_inicio?: string;
    data_fim?: string;
    municipio?: string;
  }): Promise<CrimeHeatmapPoint[]> {
    const response = await apiClient.get<CrimeHeatmapPoint[]>(
      "/ocorrencias/heatmap",
      {
        params: filters,
      },
    );
    return response.data;
  },
};
