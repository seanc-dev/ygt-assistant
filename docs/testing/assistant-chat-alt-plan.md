# AssistantChat Alternate Testing Plan (For Approval)

1. **Component Contract Tests (Vitest + RTL)**
   - Focus: `useChatThread` (once extracted), `TokenOverlay`, `MessageList`, `ReferenceSearchPanel`
   - Verify prop contracts, callbacks, and edge cases without rendering full AssistantChat

2. **Integration Smoke (Playwright)**
   - Minimal E2E scenario: verify Hub page loads and responds
   - Handles authentication requirements gracefully
   - Attempts to find and test chat input footer when action cards are available
   - Runs nightly; ensures browser APIs behave correctly
   - Status: ✅ Implemented and passing

3. **Snapshot Baseline**
   - Lightweight screenshot of `AssistantChat` with canned data (Storybook/Chromatic or RTL snapshot)
   - Guards against structural regressions during future refactors

4. **Performance Watch**
   - Measure render time and bundle size via `vitest --run --reporter=json` + custom script
   - Fail build if render time or bundle chunk exceeds agreed threshold

## Implemented Artifacts

### Component Contract Tests ✅
- Location: `web/src/components/hub/assistantChat/__tests__`
- Tests: `TokenOverlay`, `MessageList`, `ReferenceSearchPanel`, `useChatThread`
- Run: `npm run test -- src/components/hub/assistantChat/__tests__`
- Status: All passing

### Playwright Smoke Test ✅
- Location: `web/tests/e2e/assistant-chat.smoke.spec.ts`
- Execute: `npm run test:e2e` (or `PLAYWRIGHT_BASE_URL=http://localhost:3001 npm run test:e2e`)
- Behavior:
  - Verifies server responds (handles 500 errors gracefully)
  - **Checks for console errors** - fails if runtime/build errors detected
  - Checks for authentication requirements
  - Attempts to find and expand action cards
  - Tests chat input footer visibility when available
- Status: Passing (handles server errors and auth gracefully)
- Note: Previously passed even with build errors because it only checked HTTP response. Now includes console error detection to catch runtime issues.

