# Zod Validation Schemas

## 🎯 Purpose

Type-safe validation schemas using Zod, replacing manual validation functions. All schemas provide:
- Compile-time type safety
- Runtime validation
- Automatic error messages
- Security-first design (XSS, SQL injection, command injection prevention)

## 📦 Installation

```bash
npm install zod @hookform/resolvers/zod
```

## 📚 Available Schemas

### Network Schemas (`schemas/network.ts`)

| Schema | Type | Description |
|--------|------|-------------|
| `IPv4Schema` | `string` | IPv4 addresses (e.g., 192.168.1.1) |
| `IPv6Schema` | `string` | IPv6 addresses |
| `IPSchema` | `string` | IPv4 or IPv6 addresses |
| `PortSchema` | `number` | Single port (1-65535) |
| `PortRangeSchema` | `string` | Port ranges (e.g., "80,443" or "1-1000") |
| `DomainSchema` | `string` | Domain names (e.g., example.com) |
| `URLSchema` | `string` | HTTP/HTTPS URLs only (prevents javascript:, data:, file://) |
| `IPOrDomainSchema` | `string` | IP address or domain name |

### Security Schemas (`schemas/security.ts`)

| Schema | Type | Description |
|--------|------|-------------|
| `CVESchema` | `string` | CVE identifiers (e.g., CVE-2021-44228) |
| `NmapArgsSchema` | `string` | Nmap arguments (command injection prevention) |
| `PasswordSchema` | `string` | Strong passwords (8+ chars, upper, lower, number, special) |
| `APIKeySchema` | `string` | API keys (32-256 chars, alphanumeric) |
| `JWTSchema` | `string` | JWT tokens (header.payload.signature) |

### Common Schemas (`schemas/common.ts`)

| Schema | Type | Description |
|--------|------|-------------|
| `EmailSchema` | `string` | Email addresses (SQL injection prevention) |
| `EmailListSchema` | `string[]` | Comma-separated emails |
| `PhoneSchema` | `string` | Phone numbers |
| `UsernameSchema` | `string` | Usernames (3-100 chars, alphanumeric + _-.) |
| `ShortTextSchema` | `string` | Short text (max 100 chars) |
| `MediumTextSchema` | `string` | Medium text (max 500 chars) |
| `LongTextSchema` | `string` | Long text (max 1000 chars) |
| `VeryLongTextSchema` | `string` | Very long text (max 5000 chars) |
| `NumericCSVSchema` | `string` | Numeric CSV data |
| `SearchQuerySchema` | `string` | Search queries (min 2 chars) |
| `UUIDSchema` | `string` | UUID v4 format |
| `IDSchema` | `number` | Positive integer IDs |

## 🚀 Usage Examples

### Basic Validation

```typescript
import { IPSchema, EmailSchema } from '@/schemas';

// Validate with parse (throws on error)
const ip = IPSchema.parse('192.168.1.1'); // ✅ '192.168.1.1'
const invalidIP = IPSchema.parse('invalid'); // ❌ Throws ZodError

// Validate with safeParse (returns result object)
const result = EmailSchema.safeParse('user@example.com');

if (result.success) {
  console.log('Valid email:', result.data);
} else {
  console.error('Errors:', result.error.errors);
}
```

### With React Hook Form

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { IPOrDomainSchema, PortRangeSchema } from '@/schemas';

// Define form schema
const ScanFormSchema = z.object({
  target: IPOrDomainSchema,
  ports: PortRangeSchema.optional(),
  scanType: z.enum(['quick', 'full', 'custom']),
});

type ScanFormData = z.infer<typeof ScanFormSchema>;

function ScanForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ScanFormData>({
    resolver: zodResolver(ScanFormSchema),
  });

  const onSubmit = (data: ScanFormData) => {
    // data is type-safe and validated!
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('target')} />
      {errors.target && <span>{errors.target.message}</span>}

      <input {...register('ports')} />
      {errors.ports && <span>{errors.ports.message}</span>}

      <select {...register('scanType')}>
        <option value="quick">Quick</option>
        <option value="full">Full</option>
        <option value="custom">Custom</option>
      </select>

      <button type="submit">Scan</button>
    </form>
  );
}
```

### Custom Schemas

```typescript
import { z } from 'zod';
import { createSelectSchema } from '@/schemas';

// Create custom select schema
const PrioritySchema = createSelectSchema(
  ['low', 'medium', 'high', 'critical'],
  'Invalid priority level'
);

// Create complex nested schema
const TaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(1000).optional(),
  priority: PrioritySchema,
  assignee: EmailSchema,
  dueDate: z.string().datetime(),
  tags: z.array(z.string()).max(10),
});

type Task = z.infer<typeof TaskSchema>;
```

### Conditional Validation

```typescript
import { z } from 'zod';

const ConditionalSchema = z.object({
  scanType: z.enum(['quick', 'custom']),
  nmapArgs: z.string().optional(),
}).refine(
  (data) => {
    // If custom, nmap args required
    if (data.scanType === 'custom') {
      return !!data.nmapArgs;
    }
    return true;
  },
  {
    message: 'Custom scans require Nmap arguments',
    path: ['nmapArgs'],
  }
);
```

### API Request Validation

```typescript
import { ScanFormSchema } from './schemas';

async function startScan(formData: unknown) {
  // Validate before sending
  const validated = ScanFormSchema.parse(formData);

  const response = await fetch('/api/v1/scan/start', {
    method: 'POST',
    body: JSON.stringify(validated),
  });

  return response.json();
}
```

## 🔒 Security Features

All schemas include protection against:
- **Command Injection**: Blocks `&&`, `||`, `;`, `$()`, backticks, pipes
- **XSS**: Validates URL schemes, blocks javascript:, data:, file://
- **SQL Injection**: Blocks common SQL injection patterns in text inputs
- **Null Bytes**: Rejects strings containing null bytes (`\0`)
- **Unicode Attacks**: Blocks right-to-left override characters

## 📝 Migration from Manual Validation

### Before (Manual Validation)

```javascript
import { validateIP, validatePorts } from '@/utils/validation';

const errors = {};

const ipResult = validateIP(formData.target);
if (!ipResult.valid) {
  errors.target = ipResult.error;
}

const portsResult = validatePorts(formData.ports);
if (!portsResult.valid) {
  errors.ports = portsResult.error;
}

if (Object.keys(errors).length > 0) {
  // Handle errors
  return;
}

// Continue with validated data
```

### After (Zod)

```typescript
import { z } from 'zod';
import { IPSchema, PortRangeSchema } from '@/schemas';

const FormSchema = z.object({
  target: IPSchema,
  ports: PortRangeSchema,
});

try {
  const validated = FormSchema.parse(formData);
  // Continue with type-safe data
} catch (error) {
  // Zod provides detailed error messages
  console.error(error.errors);
}
```

## 🎯 Best Practices

1. **Define schemas at module level**
   ```typescript
   const MyFormSchema = z.object({ /* ... */ });
   type MyFormData = z.infer<typeof MyFormSchema>;
   ```

2. **Use safeParse for user inputs**
   ```typescript
   const result = MySchema.safeParse(untrustedInput);
   if (result.success) { /* use result.data */ }
   ```

3. **Combine schemas with composition**
   ```typescript
   const BaseSchema = z.object({ id: z.number() });
   const ExtendedSchema = BaseSchema.extend({ name: z.string() });
   ```

4. **Provide clear error messages**
   ```typescript
   z.string().min(3, 'Username must be at least 3 characters');
   ```

5. **Use transforms for data normalization**
   ```typescript
   z.string().toLowerCase().trim();
   ```

## 📚 Resources

- [Zod Documentation](https://zod.dev)
- [React Hook Form + Zod](https://react-hook-form.com/get-started#SchemaValidation)
- [Type-safe Forms Guide](https://react-hook-form.com/ts)

## 🔗 Related Files

- `utils/validation.js` - Legacy manual validation (deprecated, use Zod instead)
- `schemas/examples.tsx` - Full working examples
- `schemas/index.ts` - All schema exports

---

**DOUTRINA VÉRTICE - GAP #4 (P1)**
**Following Boris Cherny's Principle: "If it doesn't have types, it's not production"**

**Soli Deo Gloria** 🙏
