import { useState } from 'react';
import styles from './Config.module.scss';
import StatesTab from './tabs/StatesTab';
import PreamblesTab from './tabs/PreamblesTab';

type TabType = 'states' | 'preambles';

export default function Config() {
  const [activeTab, setActiveTab] = useState<TabType>('states');

  return (
    <div className={styles.config}>
      <div className={styles.header}>
        <h1>System Configuration</h1>
        <p className={styles.subtitle}>
          Manage states, legislation sources, and preambles for compliance checking
        </p>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'states' ? styles.active : ''}`}
          onClick={() => setActiveTab('states')}
        >
          States & Legislation
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'preambles' ? styles.active : ''}`}
          onClick={() => setActiveTab('preambles')}
        >
          Preambles & Versions
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === 'states' && <StatesTab />}
        {activeTab === 'preambles' && <PreamblesTab />}
      </div>
    </div>
  );
}
