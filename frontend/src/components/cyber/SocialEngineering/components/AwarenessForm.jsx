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
      <h3 className={styles.title}>🎓 Criar Treinamento de Awareness</h3>

      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="Título do Treinamento"
          variant="cyber"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          required
          fullWidth
        />

        <div className={styles.field}>
          <label htmlFor="textarea-descri-o-1ytty" className={styles.label}>Descrição</label>
<textarea id="textarea-descri-o-1ytty"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className={styles.textarea}
            rows={4}
            required
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="select-grupo-alvo-otmlo" className={styles.label}>Grupo Alvo</label>
<select id="select-grupo-alvo-otmlo"
            value={formData.target_group}
            onChange={(e) => setFormData({ ...formData, target_group: e.target.value })}
            className={styles.select}
          >
            <option value="all">Todos</option>
            <option value="developers">Desenvolvedores</option>
            <option value="management">Gestão</option>
            <option value="support">Suporte</option>
          </select>
        </div>

        <div className={styles.field}>
          <label htmlFor="select-n-vel-de-dificuldade-ch0xx" className={styles.label}>Nível de Dificuldade</label>
<select id="select-n-vel-de-dificuldade-ch0xx"
            value={formData.difficulty_level}
            onChange={(e) => setFormData({ ...formData, difficulty_level: e.target.value })}
            className={styles.select}
          >
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
        >
          {loading ? 'Criando Treinamento...' : 'Criar Treinamento'}
        </Button>
      </form>
    </div>
  );
};

export default AwarenessForm;
