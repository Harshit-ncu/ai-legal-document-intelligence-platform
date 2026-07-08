import React from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

const DashboardPage = () => {
  return (
    <div>
      <PageHeader 
        title="Dashboard" 
        description="Overview of your uploaded documents and analyses." 
      />
      <EmptyState 
        icon="📊" 
        title="Dashboard Coming Soon" 
        description="Aggregate statistics and recent documents will appear here." 
      />
    </div>
  );
};

export default DashboardPage;
