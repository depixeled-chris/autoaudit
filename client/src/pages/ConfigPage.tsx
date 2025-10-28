import React, { useState } from 'react';
import { PageTypesTable } from '@features/config/components/PageTypesTable';
import StatesTab from './Config/tabs/StatesTab';
import PreamblesTab from './Config/tabs/PreamblesTab';
import RulesTab from './Config/tabs/RulesTab';
import OtherTab from './Config/tabs/OtherTab';
import { LLMTab } from './Config/tabs/LLMTab';
import styles from './ConfigPage.module.scss';

type TabType = 'page-types' | 'states' | 'preambles' | 'rules' | 'other' | 'llm';

export const ConfigPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('page-types');

  return (
    <div className={styles.config}>
      <div className={styles.header}>
        <div>
          <h1>Configuration</h1>
          <p>Manage system settings, states, legislation, rules, and preambles</p>
        </div>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'page-types' ? styles.active : ''}`}
          onClick={() => setActiveTab('page-types')}
        >
          Page Types
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'states' ? styles.active : ''}`}
          onClick={() => setActiveTab('states')}
        >
          States & Legislation
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'rules' ? styles.active : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          Rules
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'preambles' ? styles.active : ''}`}
          onClick={() => setActiveTab('preambles')}
        >
          Preambles & Versions
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'other' ? styles.active : ''}`}
          onClick={() => setActiveTab('other')}
        >
          Other
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'llm' ? styles.active : ''}`}
          onClick={() => setActiveTab('llm')}
        >
          LLM Usage
        </button>
      </div>

      <div className={styles.tabContent}>
        {activeTab === 'page-types' && (
          <div className={styles.section}>
            <h2>Page Types</h2>
            <p>Configure page types for compliance checking</p>
            <PageTypesTable />
          </div>
        )}
        {activeTab === 'states' && <StatesTab />}
        {activeTab === 'rules' && <RulesTab />}
        {activeTab === 'preambles' && <PreamblesTab />}
        {activeTab === 'other' && <OtherTab />}
        {activeTab === 'llm' && <LLMTab />}
      </div>
    </div>
  );
};
