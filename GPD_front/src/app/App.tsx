import { RouterProvider } from 'react-router-dom'
import { router } from './routes'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider } from './context/AuthContext'
import { WorkspaceProvider } from './context/WorkspaceContext'

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <WorkspaceProvider>
          <RouterProvider router={router}/>
        </WorkspaceProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
