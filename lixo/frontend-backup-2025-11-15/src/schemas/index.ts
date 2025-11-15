/**
 * Zod validation schemas
 *
 * DOUTRINA VÉRTICE - GAP #4 (P1)
 * Type-safe validation using Zod
 *
 * Following Boris Cherny's principle: "If it doesn't have types, it's not production"
 *
 * Usage:
 * ```typescript
 * import { IPSchema, EmailSchema } from '@/schemas';
 * import { zodResolver } from '@hookform/resolvers/zod';
 * import { useForm } from 'react-hook-form';
 *
 * const { register, handleSubmit, formState: { errors } } = useForm({
 *   resolver: zodResolver(MyFormSchema),
 * });
 * ```
 */

// Network schemas
export {
  IPv4Schema,
  IPv6Schema,
  IPSchema,
  PortSchema,
  PortRangeSchema,
  DomainSchema,
  URLSchema,
  IPOrDomainSchema,
  type IPAddress,
  type PortRange,
  type Domain,
  type URL,
  type IPOrDomain,
} from "./network";

// Security schemas
export {
  CVESchema,
  NmapArgsSchema,
  PasswordSchema,
  APIKeySchema,
  JWTSchema,
  type CVE,
  type NmapArgs,
  type Password,
  type APIKey,
  type JWT,
} from "./security";

// Common schemas
export {
  EmailSchema,
  EmailListSchema,
  PhoneSchema,
  UsernameSchema,
  ShortTextSchema,
  MediumTextSchema,
  LongTextSchema,
  VeryLongTextSchema,
  NumericCSVSchema,
  SearchQuerySchema,
  UUIDSchema,
  IDSchema,
  createSelectSchema,
  type Email,
  type EmailList,
  type Phone,
  type Username,
  type ShortText,
  type MediumText,
  type LongText,
  type VeryLongText,
  type NumericCSV,
  type SearchQuery,
  type UUID,
  type ID,
} from "./common";

// Re-export zod for convenience
export { z } from "zod";
