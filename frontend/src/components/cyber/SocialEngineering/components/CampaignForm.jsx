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
      <h3 className={styles.title}>🎯 Criar Campanha de Phishing</h3>

      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="Nome da Campanha"
          variant="cyber"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
          fullWidth
        />

        <div className={styles.field}>
          <label htmlFor="select-template-cdc3b" className={styles.label}>Template</label>
<select id="select-template-cdc3b"
            value={formData.template_id}
            onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
            className={styles.select}
            required
          >
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
        >
          {loading ? 'Criando Campanha...' : 'Criar Campanha'}
        </Button>
      </form>
    </div>
  );
};

export default CampaignForm;
