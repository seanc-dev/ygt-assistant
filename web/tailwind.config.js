/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
    "./src/lib/**/*.{js,ts,jsx,tsx}",
    "../components/ui/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // LucidWork Design System Colors
        primary: {
          DEFAULT: "var(--lw-primary)",
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        secondary: {
          DEFAULT: "var(--lw-secondary)",
        },
        base: {
          DEFAULT: "var(--lw-base)",
        },
        surface: {
          DEFAULT: "var(--lw-surface)",
        },
        text: {
          primary: "var(--lw-neutral-text)",
          muted: "var(--lw-neutral-muted)",
        },
        success: {
          DEFAULT: "var(--lw-success)",
        },
        warning: {
          DEFAULT: "var(--lw-warning)",
        },
        error: {
          DEFAULT: "var(--lw-error)",
        },
        border: {
          DEFAULT: "var(--lw-border)",
        },
      },
      fontFamily: {
        body: ["var(--lw-font-body)", "system-ui", "sans-serif"],
        heading: ["var(--lw-font-heading)", "var(--lw-font-body)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "var(--lw-radius-sm)", // 4px
        md: "var(--lw-radius-md)", // 6px
      },
      spacing: {
        xs: "var(--lw-spacing-xs)", // 8px
        md: "var(--lw-spacing-md)", // 16px
        lg: "var(--lw-spacing-lg)", // 24px
        xl: "var(--lw-spacing-xl)", // 32px
      },
      boxShadow: {
        sm: "var(--lw-shadow-sm)",
      },
      transitionDuration: {
        fast: "var(--lw-duration-fast)", // 150ms
        normal: "var(--lw-duration-normal)", // 180ms
        slow: "var(--lw-duration-slow)", // 200ms
      },
      transitionTimingFunction: {
        calm: "var(--lw-easing)",
      },
    },
  },
  plugins: [],
};
