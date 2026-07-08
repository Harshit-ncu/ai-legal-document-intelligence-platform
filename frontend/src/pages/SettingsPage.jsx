import React from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

const SettingsPage = () => {
  return (
    <div>
      <PageHeader 
        title="Settings" 
        description="Manage your application preferences." 
      />
      <EmptyState 
        icon="⚙️" 
        title="Settings Coming Soon" 
        description="User preferences and API key configurations will be managed here." 
      />
    </div>
  );
};

export default SettingsPage;
