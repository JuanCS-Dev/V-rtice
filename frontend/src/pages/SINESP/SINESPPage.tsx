import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui";
import { MapPin } from "lucide-react";
import { VehicleSearchForm } from "@/features/sinesp/components/VehicleSearchForm";

export default function SINESPPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[rgb(var(--text-primary))]">
          SINESP Brasil
        </h1>
        <p className="mt-1 text-sm text-[rgb(var(--text-secondary))]">
          Sistema Nacional de Informações de Segurança Pública
        </p>
      </div>

      {/* Vehicle Search Form */}
      <VehicleSearchForm />

      {/* Info Card */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary-600" />
            <CardTitle>Integração SINESP</CardTitle>
          </div>
          <CardDescription className="mt-2">
            Consulta integrada ao Sistema Nacional de Informações de Segurança
            Pública do Brasil. Acesso a informações de veículos, ocorrências
            criminais e estatísticas de segurança pública em todo território
            nacional.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
