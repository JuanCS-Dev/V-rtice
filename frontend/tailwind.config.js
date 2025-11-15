/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Verde primário (#10b981 - Emerald)
        primary: {
          DEFAULT: "#10b981",
          50: "#ECFDF5",
          100: "#D1FAE5",
          200: "#A7F3D0",
          300: "#6EE7B7",
          400: "#34D399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065F46",
          900: "#064E3B",
          950: "#022C22",
        },
        // Backgrounds
        background: {
          light: "#FDFDF7",
          dark: "#09090B",
        },
        foreground: {
          light: "#0E0E0E",
          dark: "#E5E7EB",
        },
        // Cards
        card: {
          light: "#FFFFFF",
          dark: "#18181B",
        },
        "card-border": {
          light: "#E5E7EB",
          dark: "#27272A",
        },
        // Text
        "text-primary": {
          light: "#0E0E0E",
          dark: "#F9FAFB",
        },
        "text-secondary": {
          light: "#6B7280",
          dark: "#9CA3AF",
        },
        "text-muted": {
          light: "#9CA3AF",
          dark: "#6B7280",
        },
        // Semantic colors
        success: "#10b981",
        warning: "#F59E0B",
        danger: "#EF4444",
        info: "#3B82F6",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "Cascadia Code",
          "Source Code Pro",
          "Menlo",
          "monospace",
        ],
      },
      fontSize: {
        xs: "0.75rem", // 12px
        sm: "0.875rem", // 14px
        base: "1rem", // 16px
        lg: "1.125rem", // 18px
        xl: "1.25rem", // 20px
        "2xl": "1.5rem", // 24px
        "3xl": "1.875rem", // 30px
        "4xl": "2.25rem", // 36px
      },
      spacing: {
        xs: "0.25rem", // 4px
        sm: "0.5rem", // 8px
        md: "1rem", // 16px
        lg: "1.5rem", // 24px
        xl: "2.5rem", // 40px
        "2xl": "4rem", // 64px
        "3xl": "6.5rem", // 104px
      },
      borderRadius: {
        sm: "0.25rem", // 4px
        md: "0.5rem", // 8px
        lg: "0.75rem", // 12px
        full: "9999px",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
        "glow-green": "0 0 20px rgba(16, 185, 129, 0.2)",
      },
      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
        slow: "350ms",
      },
      transitionTimingFunction: {
        "ease-custom": "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
};
