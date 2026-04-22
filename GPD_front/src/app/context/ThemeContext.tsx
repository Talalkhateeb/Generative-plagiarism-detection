import { createContext, useContext, useEffect, useState } from 'react'
type Theme = 'dark' | 'light'
const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({ theme: 'dark', toggleTheme: () => {} })
export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('GPD_theme') as Theme) || 'dark')
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('GPD_theme', theme)
  }, [theme])
  return <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme(t => t === 'dark' ? 'light' : 'dark') }}>{children}</ThemeContext.Provider>
}
export const useTheme = () => useContext(ThemeContext)
