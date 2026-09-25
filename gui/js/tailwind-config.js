/**
 * Tailwind CSS configuration for ThesisForge GUI.
 * Extracted from index.html to allow a strict Content-Security-Policy
 * that omits 'unsafe-inline' from script-src.
 */
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        cobalt: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
        },
      },
    },
  },
};
