import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Badge,
} from "@/components/ui";
import { Loader2, Car, AlertTriangle, Calendar, MapPin } from "lucide-react";
import { sinespService, type VehicleInfo } from "@/services/api/sinespService";

const vehicleSchema = z.object({
  placa: z
    .string()
    .min(1, "Placa é obrigatória")
    .regex(
      /^[A-Z]{3}[-\s]?\d{1}[A-Z0-9]{1}\d{2}$|^[A-Z]{3}[-\s]?\d{4}$/i,
      "Formato inválido (ex: ABC-1234 ou ABC1D23)",
    ),
});

type VehicleFormData = z.infer<typeof vehicleSchema>;

export function VehicleSearchForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VehicleInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VehicleFormData>({
    resolver: zodResolver(vehicleSchema),
  });

  const onSubmit = async (data: VehicleFormData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const vehicleInfo = await sinespService.consultarVeiculo(data.placa);
      setResult(vehicleInfo);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Falha ao consultar veículo no SINESP",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getSituacaoVariant = (situacao: string) => {
    switch (situacao) {
      case "regular":
        return "success";
      case "restricao":
        return "warning";
      case "roubo":
        return "danger";
      default:
        return "default";
    }
  };

  const getSituacaoLabel = (situacao: string) => {
    switch (situacao) {
      case "regular":
        return "Regular";
      case "restricao":
        return "Com Restrição";
      case "roubo":
        return "Roubo/Furto";
      default:
        return "Desconhecida";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Consulta de Veículos - SINESP</CardTitle>
        <CardDescription>
          Consulta de veículos no Sistema Nacional de Informações de Segurança
          Pública
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Placa Input */}
          <div>
            <label className="mb-2 block text-sm font-medium text-[rgb(var(--text-primary))]">
              Placa do Veículo
            </label>
            <Input
              {...register("placa")}
              placeholder="ABC-1234 ou ABC1D23"
              className="font-mono uppercase"
              maxLength={8}
            />
            {errors.placa && (
              <p className="mt-1 text-xs text-red-600">
                {errors.placa.message}
              </p>
            )}
            <p className="mt-1.5 text-xs text-[rgb(var(--text-tertiary))]">
              Formatos aceitos: ABC-1234 (antigo) ou ABC1D23 (Mercosul)
            </p>
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Consultando SINESP...
              </>
            ) : (
              <>
                <Car className="mr-2 h-4 w-4" />
                Consultar Veículo
              </>
            )}
          </Button>
        </form>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[rgb(var(--text-primary))]">
                Informações do Veículo
              </h3>
              <Badge variant={getSituacaoVariant(result.situacao)}>
                {getSituacaoLabel(result.situacao)}
              </Badge>
            </div>

            {/* Vehicle Info */}
            <div className="rounded-lg border border-[rgb(var(--border))] p-4">
              <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                <Car className="h-4 w-4 text-primary-600" />
                Dados do Veículo
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Placa
                  </span>
                  <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.placa}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Marca
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.marca}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Modelo
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.modelo}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Cor
                  </span>
                  <Badge variant="default">{result.cor}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Ano
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.ano}
                  </span>
                </div>
                {result.chassi && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[rgb(var(--text-secondary))]">
                      Chassi
                    </span>
                    <span className="font-mono text-sm font-medium text-[rgb(var(--text-primary))]">
                      {result.chassi}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Location */}
            {result.municipio && (
              <div className="rounded-lg border border-[rgb(var(--border))] p-4">
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[rgb(var(--text-primary))]">
                  <MapPin className="h-4 w-4 text-primary-600" />
                  Localização
                </h4>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[rgb(var(--text-secondary))]">
                    Município
                  </span>
                  <span className="text-sm font-medium text-[rgb(var(--text-primary))]">
                    {result.municipio}
                  </span>
                </div>
              </div>
            )}

            {/* Restrictions */}
            {result.restricoes && result.restricoes.length > 0 && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
                <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-red-900 dark:text-red-100">
                  <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
                  Restrições Encontradas ({result.restricoes.length})
                </h4>
                <div className="space-y-2">
                  {result.restricoes.map((restricao, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-red-300 bg-red-100 p-3 dark:border-red-700 dark:bg-red-900"
                    >
                      <p className="text-sm font-medium text-red-900 dark:text-red-100">
                        {restricao}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warning for Stolen */}
            {result.situacao === "roubo" && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-red-600 dark:text-red-400" />
                  <div>
                    <p className="font-semibold text-sm text-red-900 dark:text-red-100">
                      VEÍCULO COM REGISTRO DE ROUBO/FURTO
                    </p>
                    <p className="mt-1 text-xs text-red-700 dark:text-red-300">
                      Este veículo consta como roubado ou furtado no sistema
                      SINESP. Contate imediatamente as autoridades policiais
                      caso encontre este veículo.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Clean Certificate */}
            {result.situacao === "regular" &&
              (!result.restricoes || result.restricoes.length === 0) && (
                <div className="rounded-lg border border-primary-200 bg-primary-50 p-4 dark:border-primary-800 dark:bg-primary-950">
                  <div className="flex items-start gap-2">
                    <Car className="mt-0.5 h-5 w-5 text-primary-600 dark:text-primary-400" />
                    <div>
                      <p className="font-semibold text-sm text-primary-900 dark:text-primary-100">
                        Veículo Regular
                      </p>
                      <p className="mt-1 text-xs text-primary-700 dark:text-primary-300">
                        Este veículo não possui restrições ou pendências no
                        sistema SINESP.
                      </p>
                    </div>
                  </div>
                </div>
              )}

            {/* Metadata */}
            <div className="flex items-center gap-2 text-xs text-[rgb(var(--text-tertiary))]">
              <Calendar className="h-3.5 w-3.5" />
              <span>
                Consultado em{" "}
                {new Date(result.data_consulta).toLocaleString("pt-BR")}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
