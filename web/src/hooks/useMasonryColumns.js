import { useEffect, useMemo, useState } from 'react'

function columnCountForViewport() {
  if (typeof window === 'undefined') return 1
  if (window.matchMedia('(min-width: 1280px)').matches) return 5
  if (window.matchMedia('(min-width: 1024px)').matches) return 4
  if (window.matchMedia('(min-width: 640px)').matches) return 3
  if (window.matchMedia('(min-width: 400px)').matches) return 2
  return 1
}

export function useMasonryColumnCount() {
  const [columnCount, setColumnCount] = useState(columnCountForViewport)

  useEffect(() => {
    const mediaQueries = [
      window.matchMedia('(min-width: 1280px)'),
      window.matchMedia('(min-width: 1024px)'),
      window.matchMedia('(min-width: 640px)'),
      window.matchMedia('(min-width: 400px)'),
    ]
    const updateColumnCount = () => setColumnCount(columnCountForViewport())

    mediaQueries.forEach((query) => query.addEventListener('change', updateColumnCount))
    return () => {
      mediaQueries.forEach((query) => query.removeEventListener('change', updateColumnCount))
    }
  }, [])

  return columnCount
}

export function useMasonryColumns(items, columnCount) {
  return useMemo(() => {
    const columns = Array.from({ length: columnCount }, () => [])
    const estimatedHeights = Array(columnCount).fill(0)

    items.forEach((item, index) => {
      const shortestColumn = estimatedHeights.indexOf(Math.min(...estimatedHeights))
      columns[shortestColumn].push({ item, index })
      // Normalize each card to column width = 1; height ≈ 1 / aspectRatio.
      // Fall back to a middling ratio when dims are missing.
      const ratio = item._ratio && item._ratio > 0.2 && item._ratio < 5 ? item._ratio : 1
      estimatedHeights[shortestColumn] += 1 / ratio
    })

    return columns
  }, [columnCount, items])
}
