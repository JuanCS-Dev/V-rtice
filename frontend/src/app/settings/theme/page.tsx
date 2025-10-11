"use client"

import React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { useTheme } from "@/contexts/ThemeContext"
import { 
  Monitor, 
  Moon, 
  Palette, 
  Check,
  Sparkles,
  Building2,
  Eye,
  Zap,
  Globe
} from "lucide-react"

export default function ThemeSettings() {
  const { toast } = useToast()
  const { 
    theme, 
    setTheme, 
    enableAnimations, 
    setEnableAnimations,
    enableGlassEffects,
    setEnableGlassEffects,
    highContrast,
    setHighContrast,
    reducedMotion,
    setReducedMotion
  } = useTheme()

  const themes = [
    {
      id: "hacker",
      name: "Hacker Dream",
      description: "Terminal verde neon, vibes cyberpunk",
      icon: Zap,
      gradient: "from-green-500 via-emerald-500 to-teal-500",
      preview: "bg-black border-green-500/50"
    },
    {
      id: "enterprise",
      name: "Enterprise",
      description: "Clean, profissional, confiável",
      icon: Building2,
      gradient: "from-blue-500 via-indigo-500 to-purple-500",
      preview: "bg-slate-50 border-blue-500/50"
    },
    {
      id: "consciousness",
      name: "Consciousness",
      description: "Neural networks, emergência quântica",
      icon: Sparkles,
      gradient: "from-purple-500 via-pink-500 to-rose-500",
      preview: "bg-purple-950 border-purple-500/50"
    },
    {
      id: "nature",
      name: "Nature",
      description: "Orgânico, vivo, respirando",
      icon: Globe,
      gradient: "from-emerald-500 via-green-500 to-lime-500",
      preview: "bg-green-50 border-green-500/50"
    }
  ]

  const handleThemeChange = (themeId: string) => {
    setTheme(themeId as any)
    toast({
      title: "Tema alterado",
      description: `Você está usando o tema ${themes.find(t => t.id === themeId)?.name}`,
    })
  }

  return (
    <div className="space-y-6">
      {/* Theme Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Escolher Tema
          </CardTitle>
          <CardDescription>
            Personalize a interface do MAXIMUS para seu contexto
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {themes.map((themeOption) => {
              const Icon = themeOption.icon
              const isActive = theme === themeOption.id
              
              return (
                <button
                  key={themeOption.id}
                  onClick={() => handleThemeChange(themeOption.id)}
                  className={`
                    relative group text-left p-4 rounded-lg border-2 transition-all
                    ${isActive 
                      ? 'border-primary bg-primary/5' 
                      : 'border-border hover:border-primary/50 hover:bg-accent/50'
                    }
                  `}
                >
                  {/* Preview Bar */}
                  <div className={`
                    absolute top-0 left-0 right-0 h-1 rounded-t-lg
                    bg-gradient-to-r ${themeOption.gradient}
                  `} />
                  
                  {/* Active Indicator */}
                  {isActive && (
                    <div className="absolute top-3 right-3">
                      <Check className="h-5 w-5 text-primary" />
                    </div>
                  )}
                  
                  <div className="flex items-start gap-3 mt-2">
                    <div className={`
                      p-2 rounded-lg bg-gradient-to-br ${themeOption.gradient}
                    `}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold flex items-center gap-2">
                        {themeOption.name}
                        {isActive && (
                          <Badge variant="secondary" className="text-xs">
                            Ativo
                          </Badge>
                        )}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        {themeOption.description}
                      </p>
                    </div>
                  </div>
                  
                  {/* Theme Preview */}
                  <div className={`
                    mt-3 h-12 rounded border-2 ${themeOption.preview}
                    transition-transform group-hover:scale-[1.02]
                  `} />
                </button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Visual Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Preferências Visuais
          </CardTitle>
          <CardDescription>
            Ajuste efeitos e acessibilidade
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Animations */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="animations" className="text-base">
                Animações
              </Label>
              <p className="text-sm text-muted-foreground">
                Transições suaves e efeitos de movimento
              </p>
            </div>
            <Switch
              id="animations"
              checked={enableAnimations}
              onCheckedChange={setEnableAnimations}
            />
          </div>

          {/* Glass Effects */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="glass" className="text-base">
                Efeitos de Vidro
              </Label>
              <p className="text-sm text-muted-foreground">
                Glassmorphism e blur nos elementos
              </p>
            </div>
            <Switch
              id="glass"
              checked={enableGlassEffects}
              onCheckedChange={setEnableGlassEffects}
            />
          </div>

          {/* High Contrast */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="contrast" className="text-base">
                Alto Contraste
              </Label>
              <p className="text-sm text-muted-foreground">
                Melhora legibilidade com contraste aumentado
              </p>
            </div>
            <Switch
              id="contrast"
              checked={highContrast}
              onCheckedChange={setHighContrast}
            />
          </div>

          {/* Reduced Motion */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="motion" className="text-base">
                Reduzir Movimento
              </Label>
              <p className="text-sm text-muted-foreground">
                Minimiza animações para acessibilidade
              </p>
            </div>
            <Switch
              id="motion"
              checked={reducedMotion}
              onCheckedChange={setReducedMotion}
            />
          </div>
        </CardContent>
      </Card>

      {/* System Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Preferências do Sistema
          </CardTitle>
          <CardDescription>
            Sincronizar com configurações do dispositivo
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            onClick={() => {
              const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
              toast({
                title: "Tema do sistema",
                description: `Seu sistema está usando modo ${isDark ? 'escuro' : 'claro'}`,
              })
            }}
            className="w-full"
          >
            <Monitor className="mr-2 h-4 w-4" />
            Detectar Preferência do Sistema
          </Button>
        </CardContent>
      </Card>

      {/* Preview Info */}
      <Card className="border-dashed">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Sparkles className="h-5 w-5 text-primary mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium">
                Temas Adaptativos
              </p>
              <p className="text-sm text-muted-foreground">
                Cada tema ajusta cores, tipografia e espaçamento para criar experiências 
                únicas. As configurações são salvas automaticamente e sincronizam entre dispositivos.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
