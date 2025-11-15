/**
 * 🕸️ Reactive Fabric Dashboard Page
 * 
 * Phase 1 - Passive Intelligence Collection Dashboard
 * Route: /reactive-fabric
 * 
 * @implements DOUTRINA_VERTICE - Production-ready implementation
 */

import { Metadata } from 'next';
import ReactiveFabricDashboard from '@/components/reactive-fabric/ReactiveFabricDashboard';

export const metadata: Metadata = {
  title: 'Reactive Fabric - Intelligence Collection | MAXIMUS Vértice',
  description: 'Phase 1 passive honeypot monitoring and threat intelligence fusion',
};

export default function ReactiveFabricPage() {
  return <ReactiveFabricDashboard />;
}
