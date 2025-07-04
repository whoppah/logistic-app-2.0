// tailwind.config.js
import { type Config } from 'tailwindcss';

const config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1A1A1A',    // dark charcoal for text
        accent:  '#10B981',    // Whoppah green (emerald-500)
        muted:   '#F5F5F5',    // light gray background
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};

export default config satisfies Config;
