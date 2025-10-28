/**
 * AWARENESS TRAINING FORM - Semantic Form for Training Creation
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with onSubmit handler
 * - All inputs properly labeled
 * - <textarea> with explicit label + id
 * - <select> elements with proper labels
 * - aria-live for loading status
 * - Emojis isolated in aria-hidden span
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Required fields marked
 * - Loading status announced
 * - Keyboard accessible
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React, { useState } from 'react';
import { Input, Button } from '../../../shared';
import styles from './AwarenessForm.module.css';

export const AwarenessForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    target_group: 'all',
    difficulty_level: 'medium'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await onSubmit(formData);
    if (success) {
      setFormData({
        title: '',
        description: '',
        target_group: 'all',
        difficulty_level: 'medium'
      });
    }
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>
        <span aria-hidden="true">🎓</span> Criar Treinamento de Awareness
      </h3>

      <form onSubmit={handleSubmit} className={styles.form} aria-label="Awareness training configuration">
        <Input
          label="Título do Treinamento"
          variant="cyber"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          required
          fullWidth
          aria-required="true"
        />

        <div className={styles.field}>
          <label htmlFor="awareness-description" className={styles.label}>
            Descrição
          </label>
          <textarea
            id="awareness-description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className={styles.textarea}
            rows={4}
            required
            aria-required="true"
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="awareness-target-group" className={styles.label}>
            Grupo Alvo
          </label>
          <select
            id="awareness-target-group"
            value={formData.target_group}
            onChange={(e) => setFormData({ ...formData, target_group: e.target.value })}
            className={styles.select}
            aria-label="Select target group">
            <option value="all">Todos</option>
            <option value="developers">Desenvolvedores</option>
            <option value="management">Gestão</option>
            <option value="support">Suporte</option>
          </select>
        </div>

        <div className={styles.field}>
          <label htmlFor="awareness-difficulty" className={styles.label}>
            Nível de Dificuldade
          </label>
          <select
            id="awareness-difficulty"
            value={formData.difficulty_level}
            onChange={(e) => setFormData({ ...formData, difficulty_level: e.target.value })}
            className={styles.select}
            aria-label="Select difficulty level">
            <option value="easy">Fácil</option>
            <option value="medium">Médio</option>
            <option value="hard">Difícil</option>
          </select>
        </div>

        <Button
          type="submit"
          variant="success"
          loading={loading}
          fullWidth
          aria-label="Create awareness training">
          {loading ? 'Criando Treinamento...' : 'Criar Treinamento'}
        </Button>
      </form>

      {loading && (
        <div className={styles.visuallyHidden} role="status" aria-live="polite">
          Creating awareness training...
        </div>
      )}
    </div>
  );
};

export default AwarenessForm;
