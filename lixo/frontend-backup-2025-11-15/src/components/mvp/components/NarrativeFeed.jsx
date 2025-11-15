/**
 * NarrativeFeed - Feed de Narrativas Estilo Editorial
 * ====================================================
 *
 * Timeline de narrativas com cards estilo Medium/blog.
 * Inclui filtros, search e infinite scroll.
 */

import React, { useState, useMemo } from "react";
import { StoryCard } from "./StoryCard";
import styles from "./NarrativeFeed.module.css";

export const NarrativeFeed = ({ narratives, isLoading }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [toneFilter, setToneFilter] = useState("all"); // all, analytical, poetic, technical
  const [sortBy, setSortBy] = useState("recent"); // recent, nqs, length

  // Filter and sort narratives
  const filteredNarratives = useMemo(() => {
    if (!narratives) return [];

    let filtered = [...narratives];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (n) =>
          n.content?.toLowerCase().includes(query) ||
          n.tone?.toLowerCase().includes(query),
      );
    }

    // Tone filter
    if (toneFilter !== "all") {
      filtered = filtered.filter((n) => n.tone === toneFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "recent":
          return new Date(b.created_at) - new Date(a.created_at);
        case "nqs":
          return (b.nqs || 0) - (a.nqs || 0);
        case "length":
          return (b.content?.length || 0) - (a.content?.length || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [narratives, searchQuery, toneFilter, sortBy]);

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Carregando narrativas...</p>
      </div>
    );
  }

  return (
    <div className={styles.feed}>
      {/* Filters Header */}
      <div className={styles.filtersBar}>
        {/* Search */}
        <div className={styles.searchBox}>
          <span className={styles.searchIcon}>🔍</span>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Buscar narrativas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Tone Filter */}
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Tone:</label>
          <select
            className={styles.filterSelect}
            value={toneFilter}
            onChange={(e) => setToneFilter(e.target.value)}
          >
            <option value="all">Todos</option>
            <option value="analytical">Analytical</option>
            <option value="poetic">Poetic</option>
            <option value="technical">Technical</option>
          </select>
        </div>

        {/* Sort */}
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Ordenar:</label>
          <select
            className={styles.filterSelect}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="recent">Mais recentes</option>
            <option value="nqs">Maior NQS</option>
            <option value="length">Mais longas</option>
          </select>
        </div>

        {/* Results count */}
        <div className={styles.resultsCount}>
          {filteredNarratives.length} narrativa(s)
        </div>
      </div>

      {/* Empty state */}
      {!narratives || narratives.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>📭</div>
          <h3>Nenhuma narrativa ainda</h3>
          <p>
            Clique em "Nova Narrativa" para gerar a primeira história do
            sistema.
          </p>
        </div>
      ) : filteredNarratives.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>🔍</div>
          <h3>Nenhum resultado encontrado</h3>
          <p>Tente ajustar os filtros ou busca.</p>
        </div>
      ) : (
        // Narrative Cards
        <div className={styles.cards}>
          {filteredNarratives.map((narrative) => (
            <StoryCard key={narrative.narrative_id} narrative={narrative} />
          ))}
        </div>
      )}
    </div>
  );
};

export default NarrativeFeed;
