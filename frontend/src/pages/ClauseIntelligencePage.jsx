import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentContext } from '../contexts/DocumentContext';
import { analyzeClause } from '../services/geminiService';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Skeleton } from '../components/ui/Skeleton';
import { Badge } from '../components/ui/Badge';
import { StatCard } from '../components/ui/StatCard';
import { UploadCloud, Search, ClipboardList, Scale, Bell, Lightbulb } from 'lucide-react';
import styles from './ClauseIntelligencePage.module.css';

// Utility: maps riskLevel string to Badge variant
const riskVariant = (level) => {
  if (!level) return 'info';
  const l = level.toLowerCase();
  if (l === 'high') return 'error';
  if (l === 'medium') return 'warning';
  return 'success';
};

// Utility: maps suggestion priority to Badge variant
const priorityVariant = (priority) => {
  if (!priority) return 'info';
  const p = priority.toLowerCase();
  if (p === 'critical' || p === 'high') return 'error';
  if (p === 'medium') return 'warning';
  return 'info';
};

const ClauseIntelligencePage = () => {
  const navigate = useNavigate();
  const { state } = useDocumentContext();
  const { extractedText, documentType } = state;

  const [isGenerating, setIsGenerating] = useState(false);
  const [clauseData, setClauseData] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyzeClause = async () => {
    if (!extractedText) return;

    setIsGenerating(true);
    setError(null);
    setClauseData(null);

    try {
      const data = await analyzeClause(extractedText, documentType);
      setClauseData(data);
    } catch (err) {
      console.error('Clause intelligence error:', err);
      const status = err.response?.status;
      let errMsg = 'Failed to analyze clauses. Please try again.';
      if (status === 400 || status === 422) errMsg = 'Invalid document text. Could not run clause analysis.';
      else if (status === 404) errMsg = 'AI Service endpoint not found.';
      else if (status === 429) errMsg = 'Rate limit exceeded. Please wait a moment and try again.';
      else if (status >= 500) errMsg = 'AI Service is currently unavailable.';
      else if (err.request) errMsg = 'Network error. Please check your connection.';
      setError(errMsg);
    } finally {
      setIsGenerating(false);
    }
  };

  // ── Empty guard ────────────────────────────────────────────
  if (!extractedText) {
    return (
      <div className={styles.container}>
        <EmptyState
          icon={<UploadCloud size={48} />}
          title="No Document Uploaded"
          description="Upload a document before analyzing clauses."
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
        title="AI Clause Intelligence"
        description="Identify important clauses and contractual obligations."
        actions={
          <Button
            onClick={handleAnalyzeClause}
            disabled={isGenerating}
            isLoading={isGenerating}
          >
            {clauseData ? 'Re-Analyze Clauses' : 'Analyze Clauses'}
          </Button>
        }
      />

      {/* ── Error ── */}
      {error && (
        <ErrorMessage
          title="Clause Analysis Error"
          message={error}
          className={styles.error}
        />
      )}

      {/* ── Loading skeletons ── */}
      {isGenerating && (
        <div className={styles.loadingContainer}>
          <div className={styles.statsGrid}>
            <Card><CardContent><Skeleton height="4rem" /></CardContent></Card>
            <Card><CardContent><Skeleton height="4rem" /></CardContent></Card>
          </div>
          {[1, 2, 3].map((i) => (
            <Card key={i} className={styles.resultCard}>
              <CardHeader><Skeleton width="35%" height="1.5rem" /></CardHeader>
              <CardContent>
                <Skeleton width="100%" height="1rem" className={styles.skeletonLine} />
                <Skeleton width="90%" height="1rem" className={styles.skeletonLine} />
                <Skeleton width="75%" height="1rem" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ── Pre-analysis idle state ── */}
      {!isGenerating && !clauseData && !error && (
        <EmptyState
          icon={<Search size={48} />}
          title="Ready for Clause Analysis"
          description="Click the button above to identify, explain, and evaluate the key legal clauses in your document."
        />
      )}

      {/* ── Results ── */}
      {!isGenerating && clauseData && (
        <div className={styles.resultsContainer}>

          {/* Stat bar */}
          <div className={styles.statsGrid}>
            <StatCard
              title="Clause Title"
              value={clauseData.title || 'Analyzed'}
              description="Identified by Gemini AI"
              icon={<ClipboardList size={24} />}
            />
            <StatCard
              title="Risk Level"
              value={(clauseData.riskLevel || 'Unknown').toUpperCase()}
              description="Determined by terms"
              icon={<Scale size={24} />}
              className={
                clauseData.riskLevel === 'High' ? styles.statHigh :
                clauseData.riskLevel === 'Medium' ? styles.statMedium : styles.statLow
              }
            />
            <StatCard
              title="Suggestions"
              value={(clauseData.suggestions || []).length}
              description={`${(clauseData.redFlags || []).length} red flag(s) found`}
              icon={<Lightbulb size={24} />}
            />
          </div>

          {/* Plain English */}
          {clauseData.plainEnglish && (
            <Card className={styles.resultCard}>
              <CardHeader className={styles.cardHeader}>
                <CardTitle>Plain English Explanation</CardTitle>
                <Badge variant={riskVariant(clauseData.riskLevel)}>{clauseData.riskLevel}</Badge>
              </CardHeader>
              <CardContent>
                <p className={styles.sectionText}>{clauseData.plainEnglish}</p>
              </CardContent>
            </Card>
          )}

          {/* Legal Meaning */}
          {clauseData.legalMeaning && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Legal Meaning</CardTitle></CardHeader>
              <CardContent>
                <p className={styles.sectionText}>{clauseData.legalMeaning}</p>
              </CardContent>
            </Card>
          )}

          {/* Business Impact */}
          {clauseData.businessImpact && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Business Impact</CardTitle></CardHeader>
              <CardContent>
                <p className={styles.sectionText}>{clauseData.businessImpact}</p>
              </CardContent>
            </Card>
          )}

          {/* Why It Matters */}
          {clauseData.whyImportant && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Why This Clause Matters</CardTitle></CardHeader>
              <CardContent>
                <p className={styles.sectionText}>{clauseData.whyImportant}</p>
              </CardContent>
            </Card>
          )}

          {/* Key Points */}
          {clauseData.importantPoints && clauseData.importantPoints.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Key Points</CardTitle></CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {clauseData.importantPoints.map((pt, idx) => (
                    <li key={idx}>{pt}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Red Flags */}
          {clauseData.redFlags && clauseData.redFlags.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader className={styles.cardHeader}>
                <CardTitle>Red Flags</CardTitle>
                <Badge variant="error">{clauseData.redFlags.length} found</Badge>
              </CardHeader>
              <CardContent>
                <ul className={styles.list}>
                  {clauseData.redFlags.map((flag, idx) => (
                    <li key={idx} className={styles.redFlagItem}>{flag}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Industry Best Practice */}
          {clauseData.industryBestPractice && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Industry Best Practice</CardTitle></CardHeader>
              <CardContent>
                <p className={styles.sectionText}>{clauseData.industryBestPractice}</p>
              </CardContent>
            </Card>
          )}

          {/* Negotiation Tip */}
          {clauseData.negotiationTip && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Negotiation Tip</CardTitle></CardHeader>
              <CardContent>
                <div className={styles.recommendation}>{clauseData.negotiationTip}</div>
              </CardContent>
            </Card>
          )}

          {/* Prioritised Suggestions */}
          {clauseData.suggestions && clauseData.suggestions.length > 0 && (
            <Card className={styles.resultCard}>
              <CardHeader className={styles.cardHeader}>
                <CardTitle>AI Recommendations</CardTitle>
                <Badge variant="info">{clauseData.suggestions.length} actions</Badge>
              </CardHeader>
              <CardContent>
                <div className={styles.suggestionList}>
                  {clauseData.suggestions.map((s, idx) => (
                    <div key={idx} className={styles.suggestionItem}>
                      <h4 className={styles.suggestionTitle}>
                        {s.title}
                        <Badge variant={priorityVariant(s.priority)}>{s.priority}</Badge>
                      </h4>
                      <p className={styles.suggestionReason}>{s.reason}</p>
                      {s.recommendedAction && (
                        <div className={styles.recommendation}>
                          <strong>Action:</strong> {s.recommendedAction}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Suggested Replacement Clause */}
          {clauseData.suggestedReplacementClause && (
            <Card className={styles.resultCard}>
              <CardHeader><CardTitle>Suggested Replacement Clause</CardTitle></CardHeader>
              <CardContent>
                <div className={styles.replacementClause}>
                  {clauseData.suggestedReplacementClause}
                </div>
              </CardContent>
            </Card>
          )}

        </div>
      )}
    </div>
  );
};

export default ClauseIntelligencePage;
