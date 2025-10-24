/**
 * VirtualList Component
 * =====================
 *
 * High-performance virtualized list component for rendering large datasets
 * Uses react-window for efficient rendering of only visible items
 *
 * Performance Benefits:
 * - Only renders visible items (10-20 items instead of 1000+)
 * - Constant memory usage regardless of list size
 * - Smooth scrolling even with massive datasets
 *
 * Governed by: Constituição Vértice v2.5 - Phase 3 Optimizations
 *
 * @example
 * <VirtualList
 *   items={alerts}
 *   itemHeight={80}
 *   height={600}
 *   renderItem={({ item, index, style }) => (
 *     <div style={style}>
 *       <AlertCard alert={item} />
 *     </div>
 *   )}
 * />
 */

import React, { useMemo } from 'react';
import { List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import PropTypes from 'prop-types';
import styles from './VirtualList.module.css';

/**
 * VirtualList component with auto-sizing
 *
 * @param {Object} props - Component props
 * @param {Array} props.items - Array of items to render
 * @param {Function} props.renderItem - Render function for each item
 * @param {number} props.itemHeight - Height of each item in pixels
 * @param {number} props.height - Container height (optional, uses AutoSizer if not provided)
 * @param {number} props.width - Container width (optional, uses AutoSizer if not provided)
 * @param {number} props.overscanCount - Number of items to render outside viewport (default: 5)
 * @param {string} props.className - Additional CSS class
 * @param {Object} props.style - Additional inline styles
 * @param {string} props.emptyMessage - Message to show when list is empty
 */
export const VirtualList = ({
  items = [],
  renderItem,
  itemHeight = 80,
  height,
  width,
  overscanCount = 5,
  className = '',
  style = {},
  emptyMessage = 'No items to display',
}) => {
  // Memoize items count to avoid recalculation
  const itemCount = items.length;

  // Row renderer for react-window
  const Row = useMemo(
    () =>
      ({ index, style: rowStyle }) => {
        const item = items[index];
        return renderItem({ item, index, style: rowStyle });
      },
    [items, renderItem]
  );

  // Empty state
  if (itemCount === 0) {
    return (
      <div className={`${styles.emptyState} ${className}`} style={style}>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  // If height and width are provided, use them directly
  if (height && width) {
    return (
      <div className={className} style={style}>
        <List
          height={height}
          width={width}
          itemCount={itemCount}
          itemSize={itemHeight}
          overscanCount={overscanCount}
          className={styles.list}
        >
          {Row}
        </List>
      </div>
    );
  }

  // Otherwise, use AutoSizer to fill container
  return (
    <div className={`${styles.container} ${className}`} style={style}>
      <AutoSizer>
        {({ height: autoHeight, width: autoWidth }) => (
          <List
            height={autoHeight}
            width={autoWidth}
            itemCount={itemCount}
            itemSize={itemHeight}
            overscanCount={overscanCount}
            className={styles.list}
          >
            {Row}
          </List>
        )}
      </AutoSizer>
    </div>
  );
};

VirtualList.propTypes = {
  items: PropTypes.array.isRequired,
  renderItem: PropTypes.func.isRequired,
  itemHeight: PropTypes.number,
  height: PropTypes.number,
  width: PropTypes.number,
  overscanCount: PropTypes.number,
  className: PropTypes.string,
  style: PropTypes.object,
  emptyMessage: PropTypes.string,
};

export default VirtualList;
