import React from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

const RiskAnalysisPage = () => {
  return (
    <div>
      <PageHeader 
        title="Risk Analysis" 
        description="Identify and assess potential risks in contracts." 
      />
      <EmptyState 
        icon="🚩" 
        title="Risk Analysis Coming Soon" 
        description="This module will highlight potentially unfavorable or unusual terms." 
      />
    </div>
  );
};

export default RiskAnalysisPage;
