# Latency Hardening Test Plan

## Overview
Test plan for latency optimizations in AssistantChat + interactive surfaces pipeline. Each section defines behavior to verify before implementation.

## 1. Adaptive Polling Controls

### 1.1 Pause on Tab Hidden
- **Spec**: When browser tab becomes hidden (visibilitychange), SWR polling should pause
- **Spec**: When tab becomes visible again, polling should resume
- **Spec**: Polling should not pause/resume if already paused for other reasons

### 1.2 Pause on Thread Inactive
- **Spec**: When thread has no activity for N seconds (e.g., 30s), polling should pause
- **Spec**: When user sends a message or interacts, polling should resume immediately
- **Spec**: Polling should resume when thread data changes externally

### 1.3 Debounce Chained Refetches
- **Spec**: Multiple rapid `mutateThread()` calls within X ms (e.g., 500ms) should coalesce to single request
- **Spec**: Debounce should not delay the first request, only subsequent rapid ones
- **Spec**: Debounce should reset timer on each new request

## 2. Surface Parsing Memoization

### 2.1 Cache by Surface ID
- **Spec**: `parseInteractiveSurfaces` should cache parsed results by `surface_id`
- **Spec**: Identical `surface_id` with same payload should return cached result
- **Spec**: Different `surface_id` should parse independently
- **Spec**: Same `surface_id` with different payload should invalidate cache and reparse

### 2.2 Shallow Equality Check
- **Spec**: Cache should use shallow equality on payload to detect changes
- **Spec**: Identical payloads (by reference or value) should reuse cache
- **Spec**: Modified payloads should trigger reparse

### 2.3 Memory Management
- **Spec**: Cache should have reasonable size limit (e.g., 100 entries)
- **Spec**: LRU eviction should work when cache exceeds limit
- **Spec**: Cache should not leak memory on component unmount

## 3. Optimistic Surfaces on Suggest Response

### 3.1 Store Surfaces Immediately
- **Spec**: When `/assistant-suggest` returns `surfaces`, store them on pending message state immediately
- **Spec**: Surfaces should appear in UI before thread refetch completes
- **Spec**: Optimistic surfaces should be marked as `optimistic: true`

### 3.2 Reconciliation After Backend Fetch
- **Spec**: When thread refetch completes, optimistic surfaces should be replaced with backend data
- **Spec**: If backend surfaces differ, use backend version
- **Spec**: If backend has no surfaces, remove optimistic ones

### 3.3 Actions Route Through Op Pipeline
- **Spec**: Actions from optimistic surfaces should still call `onInvokeSurfaceOp`
- **Spec**: Op pipeline should validate and execute actions normally
- **Spec**: No bypass of ActionSummary/validation logic

## 4. Memoized ActionSummary Short-Circuit

### 4.1 Memo by Ops Hash
- **Spec**: ActionSummary component should memoize render result by ops hash
- **Spec**: Identical ops (same applied/pending/errors) should reuse memoized component
- **Spec**: Changed ops should trigger re-render

### 4.2 Lightweight Placeholder
- **Spec**: When surfaces cover UX (e.g., triage_table_v1), ActionSummary should not render
- **Spec**: Memoization should prevent unnecessary re-computation when hidden
- **Spec**: Placeholder should be lightweight (no heavy computation)

### 4.3 Fallback Path
- **Spec**: When surfaces are removed, ActionSummary should render normally
- **Spec**: Memoization should not prevent updates when ops change
- **Spec**: Error states should always render ActionSummary

## 5. Integration & Regression

### 5.1 End-to-End Flow
- **Spec**: Full flow: send message → optimistic surfaces → backend surfaces → actions work
- **Spec**: Polling pauses/resumes correctly during flow
- **Spec**: No duplicate requests or race conditions

### 5.2 Performance Benchmarks
- **Spec**: Surface parsing should be < 5ms for typical payloads
- **Spec**: Polling pause/resume should be < 10ms
- **Spec**: Memoization should reduce re-renders by > 50% in typical usage

### 5.3 Backwards Compatibility
- **Spec**: Existing functionality (non-surface messages) should work unchanged
- **Spec**: ActionSummary should work when surfaces are not present
- **Spec**: No breaking changes to API contracts

