import React from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

const ChatPage = () => {
  return (
    <div>
      <PageHeader 
        title="AI Contract Assistant" 
        description="Ask natural language questions about your uploaded document." 
      />
      <EmptyState 
        icon="🤖" 
        title="Contract Assistant Coming Soon" 
        description="This module will allow you to query your documents conversationally." 
      />
    </div>
  );
};

export default ChatPage;
