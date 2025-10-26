import React from 'react';
import { PageTypesTable } from '@features/config/components/PageTypesTable';
import styles from './ConfigPage.module.scss';

export const ConfigPage: React.FC = () => {
  return (
    <div className={styles.config}>
      <div className={styles.header}>
        <div>
          <h1>Configuration</h1>
          <p>Manage application settings and preferences</p>
        </div>
      </div>

      <div className={styles.section}>
        <h2>Page Types</h2>
        <p>Configure page types for compliance checking</p>
        <PageTypesTable />
      </div>
    </div>
  );
};
