/**
 * PHISHING CAMPAIGN FORM - Semantic Form for Campaign Creation
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with onSubmit handler
 * - All inputs properly labeled
 * - <select> with explicit label + id
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
import styles from './CampaignForm.module.css';

export const CampaignForm = ({ templates, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    name: '',
    template_id: '',
    target_emails: '',
    sender_name: '',
    sender_email: '',
    landing_page_url: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await onSubmit(formData);
    if (success) {
      setFormData({
        name: '',
        template_id: '',
        target_emails: '',
        sender_name: '',
        sender_email: '',
        landing_page_url: ''
      });
    }
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>
        <span aria-hidden="true">🎯</span> Criar Campanha de Phishing
      </h3>

      <form onSubmit={handleSubmit} className={styles.form} aria-label="Phishing campaign configuration">
        <Input
          label="Nome da Campanha"
          variant="cyber"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
          fullWidth
        />

        <div className={styles.field}>
          <label htmlFor="campaign-template" className={styles.label}>
            Template
          </label>
          <select
            id="campaign-template"
            value={formData.template_id}
            onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
            className={styles.select}
            required
            aria-required="true"
            aria-label="Select phishing template">
            <option value="">Selecione um template...</option>
            {templates.map(template => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Emails Alvo (separados por vírgula)"
          variant="cyber"
          value={formData.target_emails}
          onChange={(e) => setFormData({ ...formData, target_emails: e.target.value })}
          placeholder="email1@example.com, email2@example.com"
          required
          fullWidth
        />

        <Input
          label="Nome do Remetente"
          variant="cyber"
          value={formData.sender_name}
          onChange={(e) => setFormData({ ...formData, sender_name: e.target.value })}
          required
          fullWidth
        />

        <Input
          label="Email do Remetente"
          variant="cyber"
          type="email"
          value={formData.sender_email}
          onChange={(e) => setFormData({ ...formData, sender_email: e.target.value })}
          required
          fullWidth
        />

        <Input
          label="URL da Landing Page"
          variant="cyber"
          type="url"
          value={formData.landing_page_url}
          onChange={(e) => setFormData({ ...formData, landing_page_url: e.target.value })}
          fullWidth
        />

        <Button
          type="submit"
          variant="warning"
          loading={loading}
          fullWidth
          aria-label="Create phishing campaign">
          {loading ? 'Criando Campanha...' : 'Criar Campanha'}
        </Button>
      </form>

      {loading && (
        <div className={styles.visuallyHidden} role="status" aria-live="polite">
          Creating phishing campaign...
        </div>
      )}
    </div>
  );
};

export default CampaignForm;
