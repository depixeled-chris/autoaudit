import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type ModalType = 'login' | 'register' | null;

interface ModalContextType {
  currentModal: ModalType;
  openModal: (modal: ModalType) => void;
  closeModal: () => void;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

interface ModalProviderProps {
  children: ReactNode;
}

export function ModalProvider({ children }: ModalProviderProps) {
  const [currentModal, setCurrentModal] = useState<ModalType>(null);

  const openModal = (modal: ModalType) => {
    setCurrentModal(modal);
  };

  const closeModal = () => {
    setCurrentModal(null);
  };

  return (
    <ModalContext.Provider value={{ currentModal, openModal, closeModal }}>
      {children}
    </ModalContext.Provider>
  );
}

export function useModal() {
  const context = useContext(ModalContext);
  if (context === undefined) {
    throw new Error('useModal must be used within a ModalProvider');
  }
  return context;
}
