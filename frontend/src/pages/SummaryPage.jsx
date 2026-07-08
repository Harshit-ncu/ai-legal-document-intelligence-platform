import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentContext } from '../contexts/DocumentContext';
import { summarizeDocument } from '../services/geminiService';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Skeleton } from '../components/ui/Skeleton';
import styles from './SummaryPage.module.css';

const SummaryPage = () => {
  const navigate = useNavigate();
  const { state } = useDocumentContext();
  const { extractedText, documentType } = state;

  const [isGenerating, setIsGenerating] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerateSummary = async () => {
    if (!extractedText) return;

    setIsGenerating(true);
    setError(null);
    setSummaryData(null);

    try {
      const data = await summarizeDocument(extractedText, documentType);
      setSummaryData(data);
    } catch (err) {
      console.error("Summarization error:", err);
      const status = err.response?.status;
      let errMsg = "Failed to generate summary. Please try again.";
      if (status === 400 || status === 422) errMsg = "Invalid document text. Could not generate summary.";
      else if (status === 404) errMsg = "AI Service endpoint not found.";
      else if (status === 429) errMsg = "Rate limit exceeded. Please wait a moment and try again.";
      else if (status >= 500) errMsg = "AI Service is currently unavailable.";
      else if (err.request) errMsg = "Network error. Please check your connection.";
      
      setError(errMsg);
    } finally {
      setIsGenerating(false);
    }
  };

  if (!extractedText) {
    return (
      <div className={styles.container}>
        <EmptyState 
          icon="📤" 
          title="No Document Uploaded" 
          description="Upload a document before generating a summary." 
          action={
            <Button onClick={() => navigate('/upload')} variant="primary">
              Go to Upload
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <PageHeader 
        title="AI Document Summary" 
        description="Generate an intelligent executive summary for the uploaded legal document." 
        actions={
          <Button 
            onClick={handleGenerateSummary} 
            disabled={isGenerating}
            isLoading={isGenerating}
          >
            {summaryData ? 'Regenerate Summary' : 'Generate Summary'}
          </Button>
        }
      />

      {error && (
        <ErrorMessage 
          title="Summarization Error" 
          message={error} 
          className={styles.error}
        />
      )}

      {isGenerating && (
        <div className={styles.loadingContainer}>
          <Card className={styles.summaryCard}>
            <CardHeader><Skeleton width="40%" height="1.5rem" /></CardHeader>
            <CardContent>
              <Skeleton width="100%" height="1rem" className={styles.skeletonLine} />
              <Skeleton width="100%" height="1rem" className={styles.skeletonLine} />
              <Skeleton width="80%" height="1rem" className={styles.skeletonLine} />
            </CardContent>
          </Card>
          <Card className={styles.summaryCard}>
            <CardHeader><Skeleton width="30%" height="1.5rem" /></CardHeader>
            <CardContent>
              <Skeleton width="100%" height="1rem" className={styles.skeletonLine} />
              <Skeleton width="60%" height="1rem" className={styles.skeletonLine} />
            </CardContent>
          </Card>
        </div>
      )}

      {!isGenerating && !summaryData && !error && (
        <EmptyState 
          icon="✨" 
          title="Ready to Summarize" 
          description="Click the button above to analyze your document and generate a structured summary." 
        />
      )}

      {!isGenerating && summaryData && (
        <div className={styles.resultsContainer}>
          {summaryData.executiveSummary && (
            <Card className={styles.summaryCard}>
              <CardHeader>
                <CardTitle>Executive Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className={styles.summaryText}>{summaryData.executiveSummary}</p>
              </CardContent>
            </Card>
          )}

          {summaryData.keyPoints && summaryData.keyPoints.length > 0 && (
            <Card className={styles.summaryCard}>
              <CardHeader>
                <CardTitle>Key Highlights</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {summaryData.keyPoints.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {summaryData.importantClauses && summaryData.importantClauses.length > 0 && (
            <Card className={styles.summaryCard}>
              <CardHeader>
                <CardTitle>Important Clauses</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {summaryData.importantClauses.map((clause, idx) => (
                    <li key={idx}>{clause}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {summaryData.obligations && summaryData.obligations.length > 0 && (
            <Card className={styles.summaryCard}>
              <CardHeader>
                <CardTitle>Important Obligations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {summaryData.obligations.map((obligation, idx) => (
                    <li key={idx}>{obligation}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {summaryData.risks && summaryData.risks.length > 0 && (
            <Card className={styles.summaryCard}>
              <CardHeader>
                <CardTitle>Risks</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {summaryData.risks.map((risk, idx) => (
                    <li key={idx} className={styles.riskItem}>{risk}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {summaryData.suggestedActions && summaryData.suggestedActions.length > 0 && (
            <Card className={styles.summaryCard}>
              <CardHeader>
                <CardTitle>Suggested Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {summaryData.suggestedActions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default SummaryPage;
