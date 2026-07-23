import { ImageBroken } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useLang } from '../../i18n'

export default function SmartImage({ sources, alt, className = '', eager = false, fit = 'cover' }) {
  const { t } = useLang()
  const availableSources = useMemo(() => [...new Set((sources || []).filter(Boolean))], [sources])
  const sourceKey = availableSources.join('|')
  const [sourceIndex, setSourceIndex] = useState(0)
  const [loaded, setLoaded] = useState(false)
  const imgRef = useRef(null)

  useEffect(() => {
    setSourceIndex(0)
    setLoaded(false)
  }, [sourceKey])

  const source = availableSources[sourceIndex]

  useEffect(() => {
    // Cache hits can finish loading before the onLoad listener attaches,
    // which would leave the image stuck at opacity-0.
    if (imgRef.current?.complete && imgRef.current.naturalWidth > 0) {
      setLoaded(true)
    }
  }, [source])

  if (!source) {
    return (
      <div className={`grid place-items-center bg-surface text-faint ${className}`} role="img" aria-label={alt}>
        <div className="flex flex-col items-center gap-2 text-xs">
          <ImageBroken size={24} />
          <span>{t('image.unavailable')}</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative overflow-hidden ${fit === 'contain' ? '' : 'bg-surface'} ${className}`}>
      {!loaded && <div className="skeleton-shimmer absolute inset-0" aria-hidden="true" />}
      <img
        key={source}
        ref={imgRef}
        src={source}
        alt={alt}
        loading={eager ? 'eager' : 'lazy'}
        decoding="async"
        referrerPolicy="no-referrer"
        onLoad={() => setLoaded(true)}
        onError={() => {
          if (sourceIndex < availableSources.length - 1) {
            setSourceIndex((index) => index + 1)
            setLoaded(false)
          } else {
            setSourceIndex(availableSources.length)
          }
        }}
        className={`h-full w-full ${fit === 'contain' ? 'object-contain' : 'object-cover'} transition-opacity duration-500 ${
          loaded ? 'opacity-100' : 'opacity-0'
        }`}
      />
    </div>
  )
}
