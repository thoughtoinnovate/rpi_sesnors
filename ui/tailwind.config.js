/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,html}",
    "./*.{html,js}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        aqi: {
          good: '#00e400',
          moderate: '#ffff00',
          'usg-sensitive': '#ff7e00',
          unhealthy: '#ff0000',
          'very-unhealthy': '#8f3f97',
          hazardous: '#7e0023'
        },
        pm25: '#ff9800',
        pm10: '#2196f3'
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        }
      },
      screens: {
        'xs': '475px'
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}