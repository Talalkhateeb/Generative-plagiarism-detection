import { createContext, useContext, useEffect, useState } from 'react'
type Theme = 'dark' | 'light'
const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({ theme: 'dark', toggleTheme: () => {} })
const THEME_KEY = 'GPDetect_theme'
const LEGACY_THEME_KEY = 'GPD_theme'
export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(() => (
    (localStorage.getItem(THEME_KEY) || localStorage.getItem(LEGACY_THEME_KEY)) as Theme
  ) || 'dark')
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem(THEME_KEY, theme)
    localStorage.removeItem(LEGACY_THEME_KEY)
  }, [theme])
  return <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme(t => t === 'dark' ? 'light' : 'dark') }}>{children}</ThemeContext.Provider>
}
export const useTheme = () => useContext(ThemeContext)
