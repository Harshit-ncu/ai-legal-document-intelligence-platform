import React from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

const SummaryPage = () => {
  return (
    <div>
      <PageHeader 
        title="Executive Summary" 
        description="AI-generated summaries of your legal documents." 
      />
      <EmptyState 
        icon="📝" 
        title="Executive Summary Coming Soon" 
        description="This module will integrate with Gemini to provide structured document summaries." 
      />
    </div>
  );
};

export default SummaryPage;
