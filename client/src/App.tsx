import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from '@store/index';
import { ThemeProvider } from '@contexts/ThemeContext';
import { ModalProvider } from '@contexts/ModalContext';
import { AuthGate, AuthModal } from '@features/auth';
import { Layout } from '@components/layout';
import { ProjectsPage } from '@features/projects';
import '@styles/global.scss';

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <ModalProvider>
          <AuthGate>
            <BrowserRouter>
              <Layout>
                <Routes>
                  <Route path="/projects" element={<ProjectsPage />} />
                  <Route path="/" element={<Navigate to="/projects" replace />} />
                  <Route path="*" element={<Navigate to="/projects" replace />} />
                </Routes>
              </Layout>
              <AuthModal />
            </BrowserRouter>
          </AuthGate>
        </ModalProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
