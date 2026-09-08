import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import type { TraceFilters } from "../../../shared/api/types";
import {
  EMPTY_TRACE_FILTERS,
  filtersAreEmpty,
  parseFiltersFromSearchParams,
  writeFiltersToSearchParams,
} from "../utils/filters";

export function useDashboardFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(
    () => parseFiltersFromSearchParams(searchParams),
    [searchParams],
  );

  const setFilters = useCallback(
    (next: TraceFilters) => {
      const params = writeFiltersToSearchParams(next);
      setSearchParams(params, { replace: true });
    },
    [setSearchParams],
  );

  const resetFilters = useCallback(() => {
    setFilters(EMPTY_TRACE_FILTERS);
  }, [setFilters]);

  const filterSessionIds = useCallback(
    (sessionIds: string[]) => {
      setFilters({ ...filters, sessionIds });
    },
    [filters, setFilters],
  );

  return {
    filters,
    setFilters,
    resetFilters,
    filterSessionIds,
    hasActiveFilters: !filtersAreEmpty(filters),
  };
}
