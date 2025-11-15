/**
 * Zod Schema Usage Examples
 *
 * DOUTRINA VÉRTICE - GAP #4 (P1)
 * Examples of using Zod schemas with react-hook-form
 *
 * Following Boris Cherny's principle: "Good examples are documentation"
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  IPOrDomainSchema,
  PortRangeSchema,
  createSelectSchema,
  NmapArgsSchema,
} from './index';

// ============================================================================
// EXAMPLE 1: Network Scan Form
// ============================================================================

/**
 * Network scan form schema
 *
 * Replaces manual validation in scan forms
 */
const ScanFormSchema = z.object({
  target: IPOrDomainSchema,
  ports: PortRangeSchema.optional(),
  scanType: createSelectSchema(['quick', 'full', 'custom'], 'Invalid scan type'),
  nmapArgs: NmapArgsSchema.optional(),
  options: z.object({
    aggressive: z.boolean().default(false),
    timeout: z.number().int().min(1).max(3600).default(300),
    threads: z.number().int().min(1).max(100).default(10),
  }).optional(),
});

type ScanFormData = z.infer<typeof ScanFormSchema>;

/**
 * Example scan form component
 */
export function ScanFormExample() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ScanFormData>({
    resolver: zodResolver(ScanFormSchema),
    defaultValues: {
      scanType: 'quick',
      options: {
        aggressive: false,
        timeout: 300,
        threads: 10,
      },
    },
  });

  const onSubmit = (data: ScanFormData) => {
    console.log('Validated scan data:', data);
    // Type-safe data, no manual validation needed!
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Target input */}
      <div>
        <label htmlFor="target">Target (IP or Domain)</label>
        <input {...register('target')} placeholder="192.168.1.1 or example.com" />
        {errors.target && <span className="error">{errors.target.message}</span>}
      </div>

      {/* Port range input */}
      <div>
        <label htmlFor="ports">Ports (optional)</label>
        <input {...register('ports')} placeholder="80,443 or 1-1000" />
        {errors.ports && <span className="error">{errors.ports.message}</span>}
      </div>

      {/* Scan type select */}
      <div>
        <label htmlFor="scanType">Scan Type</label>
        <select {...register('scanType')}>
          <option value="quick">Quick</option>
          <option value="full">Full</option>
          <option value="custom">Custom</option>
        </select>
        {errors.scanType && <span className="error">{errors.scanType.message}</span>}
      </div>

      {/* Nmap args (optional, validated for command injection) */}
      <div>
        <label htmlFor="nmapArgs">Custom Nmap Args (optional)</label>
        <input {...register('nmapArgs')} placeholder="-sV -O" />
        {errors.nmapArgs && <span className="error">{errors.nmapArgs.message}</span>}
      </div>

      <button type="submit">Start Scan</button>
    </form>
  );
}

// ============================================================================
// EXAMPLE 2: Login Form
// ============================================================================

import { EmailSchema, PasswordSchema } from './index';

const LoginFormSchema = z.object({
  email: EmailSchema,
  password: PasswordSchema,
  rememberMe: z.boolean().default(false),
});

type LoginFormData = z.infer<typeof LoginFormSchema>;

export function LoginFormExample() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(LoginFormSchema),
  });

  const onSubmit = (data: LoginFormData) => {
    console.log('Login data:', data);
    // Email and password are fully validated!
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input type="email" {...register('email')} placeholder="Email" />
        {errors.email && <span>{errors.email.message}</span>}
      </div>

      <div>
        <input type="password" {...register('password')} placeholder="Password" />
        {errors.password && <span>{errors.password.message}</span>}
      </div>

      <div>
        <label>
          <input type="checkbox" {...register('rememberMe')} />
          Remember me
        </label>
      </div>

      <button type="submit">Login</button>
    </form>
  );
}

// ============================================================================
// EXAMPLE 3: Dynamic Field Validation
// ============================================================================

import { z as zod } from 'zod';

/**
 * Example of conditional validation
 *
 * If scanType is 'custom', nmapArgs is required
 */
const ConditionalScanSchema = z.object({
  target: IPOrDomainSchema,
  scanType: createSelectSchema(['quick', 'full', 'custom']),
  nmapArgs: z.string().optional(),
}).refine(
  (data) => {
    // If custom scan, nmap args are required
    if (data.scanType === 'custom') {
      return !!data.nmapArgs;
    }
    return true;
  },
  {
    message: 'Custom scans require Nmap arguments',
    path: ['nmapArgs'], // Show error on nmapArgs field
  }
);

// ============================================================================
// EXAMPLE 4: API Request Validation
// ============================================================================

/**
 * Validate API request before sending
 */
import { IPSchema } from './index';

async function startScan(target: unknown, ports: unknown) {
  // Validate inputs before API call
  const validated = ScanFormSchema.parse({ target, ports, scanType: 'quick' });

  // validated is now type-safe!
  const response = await fetch('/api/v1/scan/start', {
    method: 'POST',
    body: JSON.stringify(validated),
  });

  return response.json();
}

// ============================================================================
// EXAMPLE 5: Safe Parse for User Inputs
// ============================================================================

/**
 * Safe parse with error handling
 */
function validateUserInput(input: string) {
  const result = IPOrDomainSchema.safeParse(input);

  if (!result.success) {
    // Access validation errors
    console.error('Validation failed:', result.error.errors);
    return null;
  }

  // Access validated data
  console.log('Valid input:', result.data);
  return result.data;
}

// ============================================================================
// EXAMPLE 6: Form with Array Fields
// ============================================================================

import { EmailListSchema } from './index';

const BulkEmailSchema = z.object({
  subject: z.string().min(1, 'Subject is required').max(200),
  recipients: EmailListSchema,
  message: z.string().min(1, 'Message is required').max(5000),
});

type BulkEmailData = z.infer<typeof BulkEmailSchema>;

export function BulkEmailFormExample() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BulkEmailData>({
    resolver: zodResolver(BulkEmailSchema),
  });

  const onSubmit = (data: BulkEmailData) => {
    // data.recipients is an array of validated emails!
    console.log('Sending to:', data.recipients);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input {...register('subject')} placeholder="Subject" />
        {errors.subject && <span>{errors.subject.message}</span>}
      </div>

      <div>
        <input
          {...register('recipients')}
          placeholder="email1@example.com, email2@example.com"
        />
        {errors.recipients && <span>{errors.recipients.message}</span>}
      </div>

      <div>
        <textarea {...register('message')} placeholder="Message" />
        {errors.message && <span>{errors.message.message}</span>}
      </div>

      <button type="submit">Send</button>
    </form>
  );
}
