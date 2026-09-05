import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from './auth/AuthProvider';
import { ThemeProvider } from './theme/ThemeProvider';
import { AppRoutes } from './routing/routes';

// AuthProvider must be inside Router because it uses useNavigate
export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
};

export default App;
