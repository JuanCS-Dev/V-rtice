# Optimized Components

Components optimized with React.memo, useMemo, and useCallback

## Performance Guidelines

### When to Use React.memo

✅ **DO use React.memo when:**

- Component renders often with same props
- Component has expensive render logic
- Component is in a list of items
- Component receives object/array props that don't change

❌ **DON'T use React.memo when:**

- Component rarely re-renders
- Props change frequently
- Render logic is trivial (< 1ms)
- Premature optimization without measurements

### Props Comparison

```javascript
// ❌ Bad - Objects/arrays created on every render
<MetricCard data={{ value: count }} />

// ✅ Good - Memoized objects
const data = useMemo(() => ({ value: count }), [count]);
<MetricCard data={data} />

// ✅ Better - Primitive props
<MetricCard value={count} />
```

### Custom Comparison Functions

```javascript
// For complex prop comparisons
const areEqual = (prevProps, nextProps) => {
  return prevProps.id === nextProps.id && prevProps.value === nextProps.value;
};

export const MyComponent = React.memo(Component, areEqual);
```

## Component Examples

See the following optimized components:

- `MemoizedMetricCard.jsx` - Dashboard metrics
- `MemoizedAlertItem.jsx` - Alert list items
- `MemoizedExecutionItem.jsx` - Execution list items
- `MemoizedHeader.jsx` - Dashboard headers

## Measurement

Before optimizing, measure:

```javascript
import { Profiler } from "react";

<Profiler
  id="ComponentName"
  onRender={(id, phase, actualDuration) => {
    console.log(`${id} (${phase}) took ${actualDuration}ms`);
  }}
>
  <Component />
</Profiler>;
```

## Resources

- [React.memo docs](https://react.dev/reference/react/memo)
- [useMemo docs](https://react.dev/reference/react/useMemo)
- [useCallback docs](https://react.dev/reference/react/useCallback)
