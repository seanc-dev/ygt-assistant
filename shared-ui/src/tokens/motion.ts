/**
 * LucidWork Design System - Motion Tokens
 * 
 * Core principle: Animations should feel "barely faster than calm"
 * - Slowest possible while still feeling responsive
 * 
 * Motion curves: ease-in-out
 * UI navigation: 150-200ms
 * Inline interactions: 180-240ms
 */

export const motion = {
  duration: {
    fast: "150ms", // UI navigation
    normal: "180ms", // Inline interactions
    slow: "200ms", // UI navigation
    slower: "220ms", // Context panel transitions
    slowest: "240ms", // Inline interactions
  },
  easing: {
    default: "ease-in-out",
    calm: "cubic-bezier(0.4, 0, 0.2, 1)", // Smooth, calm transition
  },
  // Specific animation patterns
  animations: {
    queueCardTransition: {
      duration: "180ms",
      easing: "ease-in-out",
      properties: ["opacity", "transform"],
      transform: "translateY(-8px)", // 8px slide up
    },
    cardExpansion: {
      duration: "200ms",
      easing: "ease-in-out",
      scale: "scale(1, 1.02)", // Scale 1 → 1.02
      fadeIn: "200ms",
    },
    contextPanel: {
      duration: "220ms",
      easing: "ease-in-out",
      properties: ["opacity", "width"],
    },
    cardHover: {
      duration: "150ms",
      easing: "ease-in-out",
      transform: "translateY(-2px)", // Subtle elevation
    },
    modalFade: {
      duration: "200ms",
      easing: "ease-in-out",
      blur: "6px", // Background blur
    },
    notificationSlide: {
      duration: "200ms",
      easing: "ease-in-out",
      autoDismiss: "5000ms", // 5 seconds
    },
  },
} as const;

export type MotionToken = typeof motion;

