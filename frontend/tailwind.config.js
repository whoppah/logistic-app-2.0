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
        primary: '#0f172a',  
        secondary: '#1e293b',
        accent: '#4f46e5',
      },
      spacing: {
        'sidebar-collapsed': '4rem',
        'sidebar-expanded': '16rem',
      },
      borderRadius: {
        xl: '1rem',
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
