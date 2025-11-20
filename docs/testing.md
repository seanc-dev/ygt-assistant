# Testing Guidelines

## Memory Considerations for Large Components

### Known Issue: AssistantChat Component

The `AssistantChat` component (3368 lines) can cause Vitest to exhaust memory during test collection/transformation. This is a known limitation when testing very large React components.

**Status**: Partially mitigated. Memory leaks in component code have been fixed, but the component size itself causes Vitest transformation overhead.

### Root Causes Identified

1. **Component Size**: 3368 lines creates a large AST during Vitest transformation
2. **Memory Leaks Fixed**:
   - `markActivity` callback was recreating on every render, causing listener re-registration loops
   - `threadData` effect was running unnecessarily due to reference changes
   - Missing cleanup for timers, listeners, and caches

### Mitigations Applied

1. **Stable Callbacks**: Converted `markActivity` to use `useRef` to prevent listener re-registration loops
2. **Effect Guards**: Added `previousThreadDataRef` to prevent expensive message merge operations from running unnecessarily
3. **Cleanup Hooks**: Added `afterEach` hooks to clean up timers, listeners, and caches
4. **Surface Cache Clearing**: Clear parsing caches between tests via `clearSurfaceCache()`
5. **Browser API Guards**: Guard browser-only APIs (requestAnimationFrame, window, document) for test environments
6. **Stable Mock References**: Use stable object references in SWR mocks to prevent reference changes
7. **Vitest Configuration**: Configured fork pool with single fork and disabled isolation

### Code Changes Made

#### Component Fixes (`AssistantChat.tsx`)

- `markActivity` now uses `useRef` instead of `useCallback` to maintain stable reference
- Added `previousThreadDataRef` guard to prevent unnecessary message merge operations
- Added guards for `window` and `document` APIs in effects
- Added fallbacks for `requestAnimationFrame` in test environments

#### Test Fixes (`AssistantChat.test.tsx`)

- Added `afterEach` cleanup hooks
- Mock `requestAnimationFrame` to prevent accumulation
- Clear surface cache between tests
- Use stable mock data references
- Added missing `workroomApi` method mocks

### Recommendations

1. **Split Large Components** (High Priority): Split `AssistantChat` into smaller, focused components:
   - Message rendering logic → `MessageList` component
   - Input handling → `ChatInput` component  
   - Token management → `TokenInput` component
   - Reference search → Already separate `ReferenceSearchPanel`
   - This will reduce Vitest transformation overhead significantly

2. **Test Isolation**: Test smaller units (hooks, utilities) separately from the full component

3. **Mock Aggressively**: Mock heavy dependencies and child components in integration tests

4. **Use Shallow Rendering**: For very large components, consider shallow rendering or snapshot tests

### Test Configuration

Vitest is configured to use fork pool with single fork to reduce memory pressure:

```javascript
test: {
  pool: "forks",
  poolOptions: {
    forks: {
      singleFork: true,
    },
  },
  isolate: false, // Disable isolation to reduce memory overhead
}
```

### Memory Leak Prevention Checklist

When writing tests for components with many effects:

- [x] Mock all external APIs (SWR, fetch, etc.)
- [x] Use stable mock references (avoid creating new objects on each call)
- [x] Clean up timers in `afterEach` hooks
- [x] Clean up event listeners
- [x] Clear caches between tests
- [x] Guard browser-only APIs
- [x] Use `cleanup()` from React Testing Library
- [x] Mock `requestAnimationFrame` in test environments

### Next Steps

1. **Component Refactoring**: Split `AssistantChat` into smaller components (recommended approach)
2. **Alternative Testing Strategy**: Consider testing the component in a real browser environment (Playwright/Cypress) instead of jsdom
3. **Incremental Testing**: Test individual features/hooks in isolation before integration tests

