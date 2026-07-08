import React from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

const ClauseIntelligencePage = () => {
  return (
    <div>
      <PageHeader 
        title="Clause Intelligence" 
        description="Detailed breakdown and recommendations for key legal clauses." 
      />
      <EmptyState 
        icon="🔍" 
        title="Clause Intelligence Coming Soon" 
        description="This module will identify, categorize, and explain key legal clauses automatically." 
      />
    </div>
  );
};

export default ClauseIntelligencePage;
