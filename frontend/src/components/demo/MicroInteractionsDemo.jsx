/**
 * Demo Component - Micro-interactions Showcase
 * MAXIMUS Vértice - Frontend Phase 3
 * 
 * Purpose: Demonstrate all animation capabilities
 * Can be removed after integration validation
 */

import React, { useState } from 'react';
import { useToast } from '../shared/Toast';
import { 
  Spinner, 
  SkeletonCard, 
  SkeletonList, 
  ProgressBar,
  PulseLoader,
  LoadingOverlay
} from '../shared/LoadingStates';
import styles from './MicroInteractionsDemo.module.css';

export const MicroInteractionsDemo = () => {
  const toast = useToast();
  const [progress, setProgress] = useState(45);
  const [isLoading, setIsLoading] = useState(false);

  const handleSuccess = () => {
    toast.success('✨ Operation completed successfully!', {
      duration: 3000
    });
  };

  const handleError = () => {
    toast.error('❌ Something went wrong. Please try again.', {
      duration: 4000,
      action: {
        label: 'Retry',
        onClick: () => console.log('Retry clicked')
      }
    });
  };

  const handleWarning = () => {
    toast.warning('⚠️ This action requires confirmation', {
      duration: 5000
    });
  };

  const handleInfo = () => {
    toast.info('ℹ️ System update available', {
      duration: 4000
    });
  };

  const simulateProgress = () => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  return (
    <div className={styles.demo}>
      <div className={styles.header}>
        <h1 className={styles.title}>Micro-interactions Demo</h1>
        <p className={styles.subtitle}>Phase 3: Animation & Soul</p>
      </div>

      <div className={styles.grid}>
        {/* Buttons Section */}
        <section className={styles.section}>
          <h2>Interactive Buttons</h2>
          <div className={styles.buttonGroup}>
            <button className={styles.btnPrimary} onClick={handleSuccess}>
              Success Toast
            </button>
            <button className={styles.btnError} onClick={handleError}>
              Error Toast
            </button>
            <button className={styles.btnWarning} onClick={handleWarning}>
              Warning Toast
            </button>
            <button className={styles.btnInfo} onClick={handleInfo}>
              Info Toast
            </button>
          </div>
        </section>

        {/* Cards Section */}
        <section className={styles.section}>
          <h2>Hover Cards</h2>
          <div className={styles.cardGrid}>
            <div className={styles.card}>
              <h3>Card 1</h3>
              <p>Hover to see elevation effect</p>
            </div>
            <div className={styles.card}>
              <h3>Card 2</h3>
              <p>Smooth shadow transition</p>
            </div>
            <div className={styles.card}>
              <h3>Card 3</h3>
              <p>GPU-accelerated transform</p>
            </div>
          </div>
        </section>

        {/* Loading States */}
        <section className={styles.section}>
          <h2>Loading States</h2>
          <div className={styles.loadingGrid}>
            <div>
              <h4>Spinners</h4>
              <div className={styles.spinnerRow}>
                <Spinner size="sm" />
                <Spinner size="md" />
                <Spinner size="lg" />
                <Spinner size="xl" />
              </div>
            </div>
            <div>
              <h4>Pulse Loader</h4>
              <PulseLoader />
            </div>
          </div>
        </section>

        {/* Progress Bar */}
        <section className={styles.section}>
          <h2>Progress Bars</h2>
          <ProgressBar 
            progress={progress} 
            label="Upload Progress"
            variant="primary"
          />
          <button className={styles.btnSecondary} onClick={simulateProgress}>
            Simulate Progress
          </button>
        </section>

        {/* Skeleton Loading */}
        <section className={styles.section}>
          <h2>Skeleton Screens</h2>
          <div className={styles.skeletonGrid}>
            <SkeletonCard lines={3} hasImage />
            <SkeletonList items={3} />
          </div>
        </section>

        {/* Form Elements */}
        <section className={styles.section}>
          <h2>Form Elements</h2>
          <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
            <div className={styles.formGroup}>
              <label htmlFor="demo-input">Input with focus animation</label>
              <input 
                id="demo-input"
                type="text" 
                placeholder="Type something..." 
                className={styles.input}
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="demo-error">Error state input</label>
              <input 
                id="demo-error"
                type="text" 
                placeholder="Trigger error..." 
                className={`${styles.input} ${styles.inputError}`}
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="demo-success">Success state input</label>
              <input 
                id="demo-success"
                type="text" 
                placeholder="Success..." 
                className={`${styles.input} ${styles.inputSuccess}`}
              />
            </div>
          </form>
        </section>

        {/* Loading Overlay */}
        <section className={styles.section}>
          <h2>Loading Overlay</h2>
          <button 
            className={styles.btnSecondary} 
            onClick={() => setIsLoading(!isLoading)}
          >
            Toggle Loading
          </button>
          <LoadingOverlay isLoading={isLoading}>
            <div className={styles.overlayContent}>
              <p>This content can be overlaid with a loading state.</p>
              <p>Notice the blur effect when loading is active.</p>
            </div>
          </LoadingOverlay>
        </section>

        {/* Staggered List */}
        <section className={styles.section}>
          <h2>Staggered Animations</h2>
          <ul className={styles.staggeredList}>
            {['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5'].map((item, i) => (
              <li key={i} className={`${styles.listItem} stagger-${i + 1}`}>
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
};

export default MicroInteractionsDemo;
