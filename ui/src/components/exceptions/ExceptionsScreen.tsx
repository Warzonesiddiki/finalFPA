import React, { useState, useEffect } from 'react';
import {
  ExceptionItem,
  ExceptionDetailResponse,
  ExceptionFilterState,
  ExceptionsRegisterSummary,
  ExceptionStatus,
} from './types';
import { ExceptionsFilterBar } from './ExceptionsFilterBar';
import { ExceptionsRegisterTable } from './ExceptionsRegisterTable';
import { ExceptionDetailDrawer } from './ExceptionDetailDrawer';
import { BulkActionBar } from './BulkActionBar';
import { RuleEffectivenessScreen } from './RuleEffectivenessScreen';
import { ExceptionParetoChart } from './ExceptionParetoChart';
import { StaleBanner } from '../common';

interface ExceptionsScreenProps {
  sessionToken: string;
}

export const ExceptionsScreen: React.FC<ExceptionsScreenProps> = ({ sessionToken }) => {
  const [filters, setFilters] = useState<ExceptionFilterState>({
    period: 'FY26-P09',
    severity: 'All',
    status: 'All',
    owner: 'All',
    ruleId: 'All',
    agingBucket: 'all',
    search: '',
  });

  const [items, setItems] = useState<ExceptionItem[]>([]);
  const [summary, setSummary] = useState<ExceptionsRegisterSummary>({
    total: 0,
    open: 0,
    overdue: 0,
    high: 0,
  });

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [subTab, setSubTab] = useState<'register' | 'pareto' | 'effectiveness'>('register');
  const [activeDetail, setActiveDetail] = useState<ExceptionDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRunningRules, setIsRunningRules] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchExceptions = () => {
    setIsLoading(true);
    setErrorMessage(null);

    const params = new URLSearchParams();
    if (filters.period) params.append('period', filters.period);
    if (filters.severity !== 'All') params.append('severity', filters.severity);
    if (filters.status !== 'All') params.append('status', filters.status);
    if (filters.owner !== 'All') params.append('owner', filters.owner);
    if (filters.ruleId !== 'All') params.append('rule_id', filters.ruleId);
    if (filters.agingBucket !== 'all') params.append('aging_bucket', filters.agingBucket);
    if (filters.search) params.append('q', filters.search);

    fetch(`/api/v1/exceptions?${params.toString()}`, {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok' && data.data) {
          setItems(data.data.items || []);
          if (data.data.summary) {
            setSummary(data.data.summary);
          }
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to load exceptions: ' + String(err));
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchExceptions();
  }, [filters, sessionToken]);

  const handleRunRules = () => {
    setIsRunningRules(true);
    setErrorMessage(null);

    fetch('/api/v1/exceptions/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        period: filters.period,
        asOfDate: '2026-11-12',
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.userMessage || data.error?.userMessage || data.detail || `HTTP ${res.status}`);
        }
        return data;
      })
      .then((data) => {
        if (data.status === 'ok') {
          const failed: Array<{ rule: string; message?: string }> = data.data?.failedRules ?? [];
          const disabled: Array<{ rule: string; notice?: string }> = data.data?.disabledRules ?? [];
          const notices = [
            ...failed.map((entry) => `${entry.rule} failed${entry.message ? `: ${entry.message}` : ''}`),
            ...disabled.map((entry) => `${entry.rule} disabled${entry.notice ? `: ${entry.notice}` : ''}`),
          ];
          fetchExceptions();
          if (notices.length) {
            setErrorMessage(`Rule run completed with ${failed.length} failed and ${disabled.length} disabled rule(s): ${notices.join('; ')}`);
          }
        } else {
          setErrorMessage('Rule evaluation returned unexpected status: ' + JSON.stringify(data));
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to execute rules: ' + String(err));
      })
      .finally(() => {
        setIsRunningRules(false);
      });
  };

  const handleRowClick = (item: ExceptionItem) => {
    fetch(`/api/v1/exceptions/${item.exception_id}`, {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok' && data.data) {
          setActiveDetail(data.data);
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to fetch exception detail: ' + String(err));
      });
  };

  const handleUpdateStatus = (newStatus: ExceptionStatus, note?: string) => {
    if (!activeDetail) return;
    setIsSaving(true);

    fetch(`/api/v1/exceptions/${activeDetail.exception.exception_id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        status: newStatus,
        note: note,
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.userMessage || data.error?.userMessage || data.detail || `HTTP ${res.status}`);
        }
        return data;
      })
      .then((data) => {
        if (data.status === 'ok' && data.data) {
          setActiveDetail(data.data);
          fetchExceptions();
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to update status: ' + String(err));
      })
      .finally(() => {
        setIsSaving(false);
      });
  };

  const handleUpdateOwner = (newOwner: string) => {
    if (!activeDetail) return;
    setIsSaving(true);

    fetch(`/api/v1/exceptions/${activeDetail.exception.exception_id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        owner: newOwner,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok' && data.data) {
          setActiveDetail(data.data);
          fetchExceptions();
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to update owner: ' + String(err));
      })
      .finally(() => {
        setIsSaving(false);
      });
  };

  const handleAddNote = (noteText: string) => {
    if (!activeDetail) return;
    setIsSaving(true);

    fetch(`/api/v1/exceptions/${activeDetail.exception.exception_id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        note: noteText,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok' && data.data) {
          setActiveDetail(data.data);
          fetchExceptions();
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to add note: ' + String(err));
      })
      .finally(() => {
        setIsSaving(false);
      });
  };

  const handleBulkUpdate = (status?: ExceptionStatus, owner?: string, note?: string) => {
    if (selectedIds.length === 0) return;
    setIsSaving(true);

    fetch('/api/v1/exceptions/bulk', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        ids: selectedIds,
        status: status,
        owner: owner,
        note: note,
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.userMessage || data.error?.userMessage || data.detail || `HTTP ${res.status}`);
        }
        return data;
      })
      .then((data) => {
        if (data.status === 'ok') {
          const skipped = data.data?.skipped ?? [];
          setSelectedIds([]);
          fetchExceptions();
          if (skipped.length) {
            const affected = skipped
              .map((item: { exceptionId: number; reason: string }) => `${item.exceptionId}: ${item.reason}`)
              .join('; ');
            setErrorMessage(`${data.data.updated} updated; ${skipped.length} skipped (${affected}).`);
          }
        }
      })
      .catch((err) => {
        setErrorMessage('Failed to apply bulk update: ' + String(err));
      })
      .finally(() => {
        setIsSaving(false);
      });
  };

  const handleCopyOwnerSummary = () => {
    // Generate copyable plain text summary per FR-EXC-017
    const ownerCounts: Record<string, { total: number; high: number; med: number; low: number; topItems: string[] }> = {};

    items.forEach((it) => {
      const o = it.owner_name || 'Unassigned';
      if (!ownerCounts[o]) {
        ownerCounts[o] = { total: 0, high: 0, med: 0, low: 0, topItems: [] };
      }
      ownerCounts[o].total += 1;
      if (it.severity.toLowerCase() === 'high') ownerCounts[o].high += 1;
      else if (it.severity.toLowerCase() === 'low') ownerCounts[o].low += 1;
      else ownerCounts[o].med += 1;

      if (ownerCounts[o].topItems.length < 3) {
        ownerCounts[o].topItems.push(`${it.rule_id} (${it.subject_display}) - ₹${parseFloat(it.amount_at_risk).toLocaleString('en-IN')}`);
      }
    });

    let text = `Exceptions Register Summary · ${filters.period}\n`;
    text += `Total Exceptions: ${summary.total} | Open: ${summary.open} | Overdue: ${summary.overdue}\n\n`;
    text += `OWNER-WISE DISTRIBUTION (FR-EXC-017):\n`;

    Object.entries(ownerCounts).forEach(([owner, c]) => {
      text += `• ${owner}: ${c.total} items (High: ${c.high}, Med: ${c.med}, Low: ${c.low})\n`;
      c.topItems.forEach((top) => {
        text += `   - ${top}\n`;
      });
    });

    text += `\nDisclaimer: "Potential exception — requires accounting review." (Leads, not verdicts)`;

    navigator.clipboard.writeText(text);
    alert('Owner summary copied to clipboard! Ready to paste into Teams or email.');
  };

  const handleExport = () => {
    // Generate CSV per FR-EXC-018
    const headers = [
      'RuleID',
      'RuleName',
      'Severity',
      'Status',
      'Owner',
      'Period',
      'SubjectKey',
      'SubjectDisplay',
      'AmountAtRisk',
      'DaysOpen',
      'AgingBucket',
      'IsOverdue',
      'FlaggedAgain',
      'EffectiveThreshold',
      'IdentityHash',
    ];

    const csvRows = [headers.join(',')];

    items.forEach((it) => {
      csvRows.push([
        `"${it.rule_id}"`,
        `"${it.rule_name.replace(/"/g, '""')}"`,
        `"${it.severity}"`,
        `"${it.status}"`,
        `"${it.owner_name}"`,
        `"${it.period_code}"`,
        `"${it.subject_key.replace(/"/g, '""')}"`,
        `"${it.subject_display.replace(/"/g, '""')}"`,
        `"${it.amount_at_risk}"`,
        it.days_open,
        `"${it.aging_bucket}"`,
        it.is_overdue ? 'TRUE' : 'FALSE',
        it.flagged_again ? 'TRUE' : 'FALSE',
        `"${it.effective_threshold.replace(/"/g, '""')}"`,
        `"${it.identity_hash}"`,
      ].join(','));
    });

    const blob = new Blob([csvRows.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `exceptions_register_${filters.period}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <StaleBanner sessionToken={sessionToken} onRerunComplete={fetchExceptions} />
      {errorMessage && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#fee2e2',
            color: '#991b1b',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '13px',
          }}
        >
          {errorMessage}
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
        <button
          onClick={() => setSubTab('register')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: subTab === 'register' ? '#0284c7' : '#f1f5f9', color: subTab === 'register' ? '#fff' : '#475569', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
        >
          📋 Exceptions Register
        </button>
        <button
          onClick={() => setSubTab('pareto')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: subTab === 'pareto' ? '#0284c7' : '#f1f5f9', color: subTab === 'pareto' ? '#fff' : '#475569', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
        >
          📈 CHT-007 Exception Pareto
        </button>
        <button
          onClick={() => setSubTab('effectiveness')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: subTab === 'effectiveness' ? '#0284c7' : '#f1f5f9', color: subTab === 'effectiveness' ? '#fff' : '#475569', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
        >
          📊 Rule Effectiveness & Tuning Dashboard (Doc 06 §9)
        </button>
      </div>

      {subTab === 'effectiveness' ? (
        <RuleEffectivenessScreen />
      ) : subTab === 'pareto' ? (
        <ExceptionParetoChart
          items={items.map(it => ({
            ruleId: it.rule_id,
            ruleName: it.rule_name || it.rule_id,
            count: 1,
          })).reduce((acc: any[], curr) => {
            const found = acc.find(x => x.ruleId === curr.ruleId)
            if (found) found.count += 1
            else acc.push(curr)
            return acc
          }, [])}
          onBarClick={ruleId => {
            setFilters(prev => ({ ...prev, ruleId }))
            setSubTab('register')
          }}
          onResetFilter={() => setFilters(prev => ({ ...prev, ruleId: 'All' }))}
        />
      ) : (
        <>
          {/* Filter and Top Action Bar */}
          <ExceptionsFilterBar
            filters={filters}
            summary={summary}
            onFilterChange={setFilters}
            onRunRules={handleRunRules}
            isRunningRules={isRunningRules}
            onExport={handleExport}
            onCopyOwnerSummary={handleCopyOwnerSummary}
          />

          {/* Exceptions Register Table */}
          {isLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
              Loading exceptions register...
            </div>
          ) : (
            <ExceptionsRegisterTable
              items={items}
              selectedIds={selectedIds}
              onSelectRow={(id, sel) => {
                if (sel) setSelectedIds([...selectedIds, id]);
                else setSelectedIds(selectedIds.filter((x) => x !== id));
              }}
              onSelectAll={(sel) => {
                if (sel) setSelectedIds(items.map((x) => x.exception_id));
                else setSelectedIds([]);
              }}
              onRowClick={handleRowClick}
            />
          )}

          {/* Bulk Action Bar per FR-EXC-010 */}
          <BulkActionBar
            selectedCount={selectedIds.length}
            onClearSelection={() => setSelectedIds([])}
            onBulkUpdate={handleBulkUpdate}
            isSaving={isSaving}
          />

          {/* Detail Drawer per SCR-024 */}
          <ExceptionDetailDrawer
            detail={activeDetail}
            onClose={() => setActiveDetail(null)}
            onUpdateStatus={handleUpdateStatus}
            onUpdateOwner={handleUpdateOwner}
            onAddNote={handleAddNote}
            isSaving={isSaving}
          />
        </>
      )}
    </div>
  );
};
