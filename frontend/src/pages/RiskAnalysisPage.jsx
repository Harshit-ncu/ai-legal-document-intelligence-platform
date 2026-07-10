import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentContext } from '../contexts/DocumentContext';
import { analyzeRisk } from '../services/geminiService';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Skeleton } from '../components/ui/Skeleton';
import { Badge } from '../components/ui/Badge';
import { StatCard } from '../components/ui/StatCard';
import { UploadCloud, Flag, AlertTriangle, AlertCircle, CheckCircle, Search } from 'lucide-react';
import styles from './RiskAnalysisPage.module.css';

const RiskAnalysisPage = () => {
  const navigate = useNavigate();
  const { state } = useDocumentContext();
  const { extractedText, documentType } = state;

  const [isGenerating, setIsGenerating] = useState(false);
  const [riskData, setRiskData] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyzeRisk = async () => {
    if (!extractedText) return;

    setIsGenerating(true);
    setError(null);
    setRiskData(null);

    try {
      const data = await analyzeRisk(extractedText, documentType);
      setRiskData(data);
    } catch (err) {
      console.error("Risk analysis error:", err);
      const status = err.response?.status;
      let errMsg = "Failed to analyze risks. Please try again.";
      if (status === 400 || status === 422) errMsg = "Invalid document text. Could not run analysis.";
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
          icon={<UploadCloud size={48} />} 
          title="No Document Uploaded" 
          description="Upload a document before running risk analysis." 
          action={
            <Button onClick={() => navigate('/upload')} variant="primary">
              Go to Upload
            </Button>
          }
        />
      </div>
    );
  }

  // Group risks by severity for display
  const highRisks = riskData?.risks?.filter(r => r.severity === 'High') || [];
  const mediumRisks = riskData?.risks?.filter(r => r.severity === 'Medium') || [];
  const lowRisks = riskData?.risks?.filter(r => r.severity === 'Low') || [];

  return (
    <div className={styles.container}>
      <PageHeader 
        title="AI Risk Analysis" 
        description="Analyze legal risks and potential issues within the uploaded document." 
        actions={
          <Button 
            onClick={handleAnalyzeRisk} 
            disabled={isGenerating}
            isLoading={isGenerating}
            variant="danger"
          >
            {riskData ? 'Re-Analyze Risks' : 'Analyze Risks'}
          </Button>
        }
      />

      {error && (
        <ErrorMessage 
          title="Analysis Error" 
          message={error} 
          className={styles.error}
        />
      )}

      {isGenerating && (
        <div className={styles.loadingContainer}>
          <div className={styles.statsGrid}>
             <Card className={styles.statsCard}><CardContent><Skeleton height="4rem" /></CardContent></Card>
          </div>
          <Card className={styles.resultCard}>
            <CardHeader><Skeleton width="30%" height="1.5rem" /></CardHeader>
            <CardContent>
              <Skeleton width="100%" height="3rem" className={styles.skeletonLine} />
              <Skeleton width="100%" height="3rem" className={styles.skeletonLine} />
            </CardContent>
          </Card>
        </div>
      )}

      {!isGenerating && !riskData && !error && (
        <EmptyState 
          icon={<Flag size={48} />} 
          title="Ready for Analysis" 
          description="Click the button above to scan your document for legal risks, missing clauses, and obligations." 
        />
      )}

      {!isGenerating && riskData && (
        <div className={styles.resultsContainer}>
          
          <div className={styles.statsGrid}>
            <StatCard 
              title="Overall Risk" 
              value={riskData.overallRisk || "N/A"} 
              description={`Score: ${riskData.overallScore || 0}/100`}
              icon={
                riskData.overallRisk === 'High' ? <AlertTriangle size={24} /> :
                riskData.overallRisk === 'Medium' ? <AlertCircle size={24} /> : <CheckCircle size={24} />
              }
              className={
                riskData.overallRisk === 'High' ? styles.statHigh :
                riskData.overallRisk === 'Medium' ? styles.statMedium : styles.statLow
              }
            />
            <StatCard 
              title="Total Identified Risks" 
              value={(riskData.risks || []).length} 
              description={`${highRisks.length} High, ${mediumRisks.length} Medium, ${lowRisks.length} Low`}
              icon={<Search size={24} />}
            />
          </div>

          {highRisks.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader className={styles.headerHigh}>
                <CardTitle>High Risk Items</CardTitle>
                <Badge variant="error">{highRisks.length} found</Badge>
              </CardHeader>
              <CardContent>
                <div className={styles.riskList}>
                  {highRisks.map((risk, idx) => (
                    <div key={idx} className={styles.riskItem}>
                      <h4 className={styles.riskTitle}>{risk.title}</h4>
                      <p className={styles.riskDesc}>{risk.description}</p>
                      {risk.recommendation && (
                        <div className={styles.recommendation}>
                          <strong>Recommendation:</strong> {risk.recommendation}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {mediumRisks.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader className={styles.headerMedium}>
                <CardTitle>Medium Risk Items</CardTitle>
                <Badge variant="warning">{mediumRisks.length} found</Badge>
              </CardHeader>
              <CardContent>
                <div className={styles.riskList}>
                  {mediumRisks.map((risk, idx) => (
                    <div key={idx} className={styles.riskItem}>
                      <h4 className={styles.riskTitle}>{risk.title}</h4>
                      <p className={styles.riskDesc}>{risk.description}</p>
                      {risk.recommendation && (
                        <div className={styles.recommendation}>
                          <strong>Recommendation:</strong> {risk.recommendation}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {lowRisks.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader className={styles.headerLow}>
                <CardTitle>Low Risk Items</CardTitle>
                <Badge variant="info">{lowRisks.length} found</Badge>
              </CardHeader>
              <CardContent>
                <div className={styles.riskList}>
                  {lowRisks.map((risk, idx) => (
                    <div key={idx} className={styles.riskItem}>
                      <h4 className={styles.riskTitle}>{risk.title}</h4>
                      <p className={styles.riskDesc}>{risk.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {riskData.missingClauses && riskData.missingClauses.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader>
                <CardTitle>Missing Clauses & Potential Legal Concerns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={styles.riskList}>
                  {riskData.missingClauses.map((clause, idx) => (
                    <div key={idx} className={styles.riskItem}>
                      <h4 className={styles.riskTitle}>{clause.name} <Badge variant={clause.importance === 'High' ? 'error' : 'warning'}>{clause.importance}</Badge></h4>
                      <p className={styles.riskDesc}>{clause.reason}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {riskData.recommendations && riskData.recommendations.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader>
                <CardTitle>General Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {riskData.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
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

export default RiskAnalysisPage;
