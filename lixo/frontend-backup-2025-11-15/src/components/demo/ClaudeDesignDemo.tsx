/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CLAUDE.AI GREEN DESIGN SYSTEM - DEMO PAGE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Página de demonstração dos componentes Claude.ai com verde
 *
 * CRITICAL: Esta página serve para VALIDAR VISUALMENTE:
 * - Cores verdes (#10b981) aplicadas corretamente
 * - Tipografia serif
 * - Shadows sutis
 * - Hover states suaves
 * - Focus rings verdes
 * - Dark mode funcionando
 *
 * Se esta página parecer com Claude.ai mas verde = SUCESSO ✅
 * Se ainda tiver laranja/vermelho = FALHOU ❌
 */

import React from "react";
import {
  Button,
  Input,
  Textarea,
  Label,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Switch,
  Checkbox,
  Alert,
  AlertTitle,
  AlertDescription,
  Spinner,
  LoadingOverlay,
  Skeleton,
  CardSkeleton,
  ListSkeleton,
} from "../ui/claude";

export function ClaudeDesignDemo() {
  return (
    <div
      className="min-h-screen p-8"
      style={{
        backgroundColor: "var(--background)",
        color: "var(--foreground)",
        fontFamily: "var(--font-primary)",
      }}
    >
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-12">
        <h1
          className="text-6xl font-bold mb-4"
          style={{
            fontFamily: "var(--font-display)",
            color: "var(--foreground)",
          }}
        >
          Claude.ai Design System
        </h1>
        <p
          className="text-xl"
          style={{
            color: "var(--muted-foreground)",
          }}
        >
          Green Variant - Clean, Calm, Focused
        </p>
        <div className="flex gap-3 mt-6">
          <Badge>VERDE Primary 💚</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="destructive">Error</Badge>
          <Badge variant="info">Info</Badge>
          <Badge variant="outline">Outline</Badge>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid gap-8">
        {/* Buttons Section */}
        <Card>
          <CardHeader>
            <CardTitle>Buttons - Claude.ai Style</CardTitle>
            <CardDescription>
              Subtle hover effects, smooth transitions, verde accent
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button>Primary (Verde) 💚</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="link">Link</Button>
            </div>

            <div className="flex flex-wrap gap-4 mt-6">
              <Button size="sm">Small</Button>
              <Button>Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </Button>
            </div>

            <div className="flex gap-4 mt-6">
              <Button disabled>Disabled</Button>
            </div>
          </CardContent>
        </Card>

        {/* Inputs Section */}
        <Card>
          <CardHeader>
            <CardTitle>Inputs - Clean & Focused</CardTitle>
            <CardDescription>
              Verde focus ring, serif typography, minimal design
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Default Input
              </label>
              <Input placeholder="Enter text..." />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <Input type="email" placeholder="email@example.com" />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Password</label>
              <Input type="password" placeholder="••••••••" />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Success State
              </label>
              <Input placeholder="Valid input" success />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Error State
              </label>
              <Input placeholder="Invalid input" error />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Disabled</label>
              <Input placeholder="Disabled" disabled />
            </div>
          </CardContent>
        </Card>

        {/* Cards Section */}
        <Card>
          <CardHeader>
            <CardTitle>Cards - Subtle Elevation</CardTitle>
            <CardDescription>Hover to see verde border accent</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Feature 1</CardTitle>
                  <CardDescription>Clean card design</CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Hover me to see the verde border accent! 💚</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Feature 2</CardTitle>
                  <CardDescription>Subtle shadows</CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Smooth transitions on hover.</p>
                </CardContent>
                <CardFooter>
                  <Button size="sm">Action</Button>
                </CardFooter>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Feature 3</CardTitle>
                  <CardDescription>Serif typography</CardDescription>
                </CardHeader>
                <CardContent>
                  <p>Claude.ai aesthetic with green.</p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>

        {/* Badges Section */}
        <Card>
          <CardHeader>
            <CardTitle>Badges - Semantic Pills</CardTitle>
            <CardDescription>
              Status indicators with clean design
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge>Default (Verde) 💚</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="destructive">Error</Badge>
              <Badge variant="info">Info</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge variant="success-subtle">Success Subtle</Badge>
              <Badge variant="warning-subtle">Warning Subtle</Badge>
              <Badge variant="danger-subtle">Danger Subtle</Badge>
              <Badge variant="info-subtle">Info Subtle</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Color Palette */}
        <Card>
          <CardHeader>
            <CardTitle>Color Palette - VERDE Primary 💚</CardTitle>
            <CardDescription>
              OKLCH color space for visual consistency
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg"
                  style={{ backgroundColor: "var(--primary)" }}
                />
                <p className="text-sm font-medium">Primary (Verde)</p>
                <p className="text-xs text-muted-foreground">#10b981</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg"
                  style={{ backgroundColor: "var(--secondary)" }}
                />
                <p className="text-sm font-medium">Secondary</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg border"
                  style={{ backgroundColor: "var(--background)" }}
                />
                <p className="text-sm font-medium">Background</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg border"
                  style={{ backgroundColor: "var(--muted)" }}
                />
                <p className="text-sm font-medium">Muted</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg"
                  style={{ backgroundColor: "var(--color-success)" }}
                />
                <p className="text-sm font-medium">Success</p>
                <p className="text-xs text-muted-foreground">#10b981</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg"
                  style={{ backgroundColor: "var(--color-warning)" }}
                />
                <p className="text-sm font-medium">Warning</p>
                <p className="text-xs text-muted-foreground">#f59e0b</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg"
                  style={{ backgroundColor: "var(--destructive)" }}
                />
                <p className="text-sm font-medium">Destructive</p>
              </div>

              <div className="space-y-2">
                <div
                  className="h-20 rounded-lg"
                  style={{ backgroundColor: "var(--color-info)" }}
                />
                <p className="text-sm font-medium">Info</p>
                <p className="text-xs text-muted-foreground">#3b82f6</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Typography */}
        <Card>
          <CardHeader>
            <CardTitle>Typography - Serif Elegance</CardTitle>
            <CardDescription>
              Claude.ai style: ui-serif for readability
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h1
                className="text-6xl font-bold mb-2"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Display Heading
              </h1>
              <p className="text-sm text-muted-foreground">text-6xl - Serif</p>
            </div>

            <div>
              <h2
                className="text-4xl font-bold mb-2"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Heading 1
              </h2>
              <p className="text-sm text-muted-foreground">text-4xl - Serif</p>
            </div>

            <div>
              <h3
                className="text-2xl font-semibold mb-2"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Heading 2
              </h3>
              <p className="text-sm text-muted-foreground">text-2xl - Serif</p>
            </div>

            <div>
              <p
                className="text-base mb-2"
                style={{ fontFamily: "var(--font-primary)" }}
              >
                Body text uses serif fonts for elegance and readability,
                matching Claude.ai's aesthetic. This creates a calm, focused
                reading experience.
              </p>
              <p className="text-sm text-muted-foreground">text-base - Serif</p>
            </div>

            <div>
              <p
                className="text-sm text-muted-foreground mb-2"
                style={{ fontFamily: "var(--font-primary)" }}
              >
                Secondary text in muted color for less important information.
              </p>
              <p className="text-sm text-muted-foreground">text-sm - Muted</p>
            </div>
          </CardContent>
        </Card>

        {/* NEW: Form Components */}
        <Card>
          <CardHeader>
            <CardTitle>Form Components - Complete Set</CardTitle>
            <CardDescription>
              All form elements with verde accents
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" placeholder="Enter your name" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="email@example.com" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="message">Message</Label>
              <Textarea
                id="message"
                placeholder="Type your message here..."
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Select>
                <SelectTrigger id="country">
                  <SelectValue placeholder="Select a country" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="us">United States 🇺🇸</SelectItem>
                  <SelectItem value="br">Brazil 🇧🇷</SelectItem>
                  <SelectItem value="uk">United Kingdom 🇬🇧</SelectItem>
                  <SelectItem value="jp">Japan 🇯🇵</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Switch id="airplane-mode" />
              <Label htmlFor="airplane-mode">Airplane Mode</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox id="terms" />
              <Label htmlFor="terms">Accept terms and conditions</Label>
            </div>
          </CardContent>
        </Card>

        {/* NEW: Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Alerts - Semantic Feedback</CardTitle>
            <CardDescription>
              Clean notifications with verde success
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="success">
              <AlertTitle>Success! 💚</AlertTitle>
              <AlertDescription>
                Your changes have been saved successfully.
              </AlertDescription>
            </Alert>

            <Alert variant="info">
              <AlertTitle>Information</AlertTitle>
              <AlertDescription>
                This is an informational message.
              </AlertDescription>
            </Alert>

            <Alert variant="warning">
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>
                Please review your inputs before continuing.
              </AlertDescription>
            </Alert>

            <Alert
              variant="destructive"
              dismissible
              onDismiss={() => console.log("Dismissed")}
            >
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Something went wrong. Please try again.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* NEW: Loading States */}
        <Card>
          <CardHeader>
            <CardTitle>Loading States - Spinners & Skeletons</CardTitle>
            <CardDescription>
              Clean loading indicators with verde accent
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="text-sm font-medium mb-3">Spinners</p>
              <div className="flex flex-wrap items-center gap-6">
                <Spinner size="sm" />
                <Spinner />
                <Spinner size="lg" />
                <Spinner label="Loading..." />
              </div>
            </div>

            <div>
              <p className="text-sm font-medium mb-3">Skeleton Loaders</p>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-4 w-[200px]" />
                </div>
                <div className="flex items-center space-x-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-[250px]" />
                    <Skeleton className="h-4 w-[200px]" />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium mb-3">Card Skeleton</p>
              <CardSkeleton />
            </div>

            <div>
              <p className="text-sm font-medium mb-3">List Skeleton</p>
              <ListSkeleton items={3} />
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <Card>
          <CardContent className="py-6">
            <div className="text-center space-y-4">
              <p
                className="text-2xl font-bold"
                style={{ fontFamily: "var(--font-display)" }}
              >
                ✅ Claude.ai Design System - GREEN Variant
              </p>
              <p className="text-muted-foreground">
                Clean, Calm, Focused - VERDE (#10b981) 💚
              </p>
              <p
                className="text-sm font-semibold"
                style={{ color: "var(--primary)" }}
              >
                12 COMPONENTES COMPLETOS | ZERO LARANJA | 100% VERDE
              </p>
              <div className="flex justify-center gap-2 flex-wrap">
                <Badge>Button ✅</Badge>
                <Badge>Input ✅</Badge>
                <Badge>Textarea ✅</Badge>
                <Badge>Label ✅</Badge>
                <Badge>Card ✅</Badge>
                <Badge>Badge ✅</Badge>
                <Badge>Select ✅</Badge>
                <Badge>Switch ✅</Badge>
                <Badge>Checkbox ✅</Badge>
                <Badge>Alert ✅</Badge>
                <Badge>Spinner ✅</Badge>
                <Badge>Skeleton ✅</Badge>
              </div>
              <p className="text-sm text-muted-foreground">SOLI DEO GLORIA</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
