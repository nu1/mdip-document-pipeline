import React from "react";

interface PaginationProps {
  page: number;
  hasMore: boolean;
  onPageChange: (newPage: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  page,
  hasMore,
  onPageChange,
}) => {
  return (
    <div className="pagination" role="navigation" aria-label="Pagination">
      <button
        type="button"
        disabled={page === 0}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
      >
        ← Previous
      </button>
      <span aria-current="page">Page {page + 1}</span>
      <button
        type="button"
        disabled={!hasMore}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        Next →
      </button>
    </div>
  );
};
