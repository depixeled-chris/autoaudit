import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type ModalType = 'login' | 'register' | null;

interface Modal {
  id: string;
  content: ReactNode;
  zIndex: number;
}

interface ModalContextType {
  currentModal: ModalType;
  openModal: (modal: ModalType) => void;
  closeModal: () => void;
  // New modal stack API
  modals: Modal[];
  pushModal: (content: ReactNode) => string;
  popModal: (id?: string) => void;
  clearModals: () => void;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

interface ModalProviderProps {
  children: ReactNode;
}

export function ModalProvider({ children }: ModalProviderProps) {
  const [currentModal, setCurrentModal] = useState<ModalType>(null);
  const [modals, setModals] = useState<Modal[]>([]);

  const openModal = (modal: ModalType) => {
    setCurrentModal(modal);
  };

  const closeModal = () => {
    setCurrentModal(null);
  };

  // New modal stack functions
  const pushModal = (content: ReactNode): string => {
    const id = `modal-${Date.now()}-${Math.random()}`;
    const zIndex = 1000 + modals.length * 100;
    setModals(prev => [...prev, { id, content, zIndex }]);
    return id;
  };

  const popModal = (id?: string) => {
    if (id) {
      setModals(prev => prev.filter(m => m.id !== id));
    } else {
      setModals(prev => prev.slice(0, -1));
    }
  };

  const clearModals = () => {
    setModals([]);
  };

  return (
    <ModalContext.Provider value={{
      currentModal,
      openModal,
      closeModal,
      modals,
      pushModal,
      popModal,
      clearModals
    }}>
      {children}
      {modals.map((modal) => (
        <div key={modal.id} style={{ position: 'relative', zIndex: modal.zIndex }}>
          {modal.content}
        </div>
      ))}
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
