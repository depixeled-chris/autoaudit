import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from '@store/index';
import { ThemeProvider } from '@contexts/ThemeContext';
import { ModalProvider } from '@contexts/ModalContext';
import { AlertProvider } from '@contexts/AlertContext';
import { AuthGate, AuthModal } from '@features/auth';
import { Layout } from '@components/layout';
import { ProjectsPage, ProjectDetailPage } from '@features/projects';
import { ConfigPage } from '@/pages/ConfigPage';
import { setAxiosStore } from '@lib/api/axios';
import '@styles/global.scss';

// Initialize axios with Redux store for token management
setAxiosStore(store);

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <ModalProvider>
          <AlertProvider>
            <AuthGate>
              <BrowserRouter>
                <Layout>
                  <Routes>
                    <Route path="/projects" element={<ProjectsPage />} />
                    <Route path="/projects/:id" element={<ProjectDetailPage />} />
                    <Route path="/config" element={<ConfigPage />} />
                    <Route path="/" element={<Navigate to="/projects" replace />} />
                    <Route path="*" element={<Navigate to="/projects" replace />} />
                  </Routes>
                </Layout>
                <AuthModal />
              </BrowserRouter>
            </AuthGate>
          </AlertProvider>
        </ModalProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
