/**
 * First-Run Guided Tour Component (FR-ONB-001)
 *
 * Functional Requirements quoted from docs/02_FUNCTIONAL_SPEC.md & docs/22_END_USER_GUIDE.md:
 * - FR-ONB-001 (First-Run Guided Tour): A 6-step overlay tour guiding first-time users through the pre-loaded fictional sample project, explaining Home, Import, Check, Analyse, Exceptions, and Forecast screens.
 * - Skippable & Resumable: Users can skip the tour at any time or resume it from the Help/About menu without blocking any app workflows.
 */

import { useState, useEffect } from 'react'

interface GuidedTourProps {
  onComplete?: () => void
}

const TOUR_STEPS = [
  {
    title: 'Welcome to FP&A Month-End Copilot',
    description: 'You are viewing the pre-loaded sample project. This 6-step quick tour will show you how to navigate your monthly close cycle in minutes.',
    targetTab: 'home',
  },
  {
    title: '1. Home & Period Status',
    description: 'The Home screen displays your active period (e.g. FY26-P09), status, key metrics, and quick jump links for the monthly workflow.',
    targetTab: 'home',
  },
  {
    title: '2. Import & Wizard',
    description: 'Import trial balance, GL actuals, bank ledgers, and budget files in 6 structured steps with live validation and error checking.',
    targetTab: 'import',
  },
  {
    title: '3. Check & Quality',
    description: 'Review data health, balance checks, and validation scores before proceeding to analysis.',
    targetTab: 'check',
  },
  {
    title: '4. Analyse & Variance',
    description: 'Explore Budget vs Actual matrices, variance waterfalls, and drill down into transaction-level evidence with one click.',
    targetTab: 'analyze',
  },
  {
    title: '5. Exceptions & Forecast',
    description: 'Resolve automated exception rules (EXC-001..024), refresh scenario forecasts (Base, Best, Worst), issue reports, and audit packs.',
    targetTab: 'exceptions',
  },
]

export function GuidedTour({ onComplete }: GuidedTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    const hasSeen = localStorage.getItem('fpa_tour_completed')
    if (hasSeen === 'true') {
      setDismissed(true)
    }
  }, [])

  if (dismissed) return null

  const step = TOUR_STEPS[currentStep]

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      localStorage.setItem('fpa_tour_completed', 'true')
      setDismissed(true)
      if (onComplete) onComplete()
    }
  }

  const handleSkip = () => {
    localStorage.setItem('fpa_tour_completed', 'true')
    setDismissed(true)
    if (onComplete) onComplete()
  }

  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', width: '380px', backgroundColor: '#0f172a', color: '#fff', borderRadius: '12px', padding: '20px', boxShadow: '0 10px 25px rgba(0,0,0,0.3)', zIndex: 9999, border: '1px solid #334155' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#38bdf8', fontWeight: 700 }}>
          Guided Tour (Step {currentStep + 1} of {TOUR_STEPS.length})
        </span>
        <button
          onClick={handleSkip}
          style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '12px', cursor: 'pointer' }}
        >
          Skip Tour
        </button>
      </div>

      <h3 style={{ margin: '0 0 8px', fontSize: '16px', color: '#f8fafc' }}>{step.title}</h3>
      <p style={{ margin: '0 0 16px', fontSize: '13px', color: '#94a3b8', lineHeight: '1.5' }}>{step.description}</p>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          {TOUR_STEPS.map((_, idx) => (
            <div
              key={idx}
              style={{ width: idx === currentStep ? '16px' : '6px', height: '6px', borderRadius: '3px', backgroundColor: idx === currentStep ? '#38bdf8' : '#334155', transition: 'all 0.2s' }}
            />
          ))}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {currentStep > 0 && (
            <button
              onClick={() => setCurrentStep(prev => prev - 1)}
              style={{ backgroundColor: '#1e293b', color: '#cbd5e1', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}
            >
              Back
            </button>
          )}
          <button
            onClick={handleNext}
            style={{ backgroundColor: '#0284c7', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
          >
            {currentStep === TOUR_STEPS.length - 1 ? 'Finish Tour' : 'Next →'}
          </button>
        </div>
      </div>
    </div>
  )
}
