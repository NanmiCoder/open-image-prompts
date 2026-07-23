const BASE_URL = import.meta.env.BASE_URL || '/'

export function assetUrl(localPath) {
  if (!localPath) return null
  if (/^https?:\/\//i.test(localPath)) return localPath

  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`
  const cleanPath = String(localPath).replace(/^\/+/, '')
  return `${cleanBase}${cleanPath}`
}

export function isImageLikeUrl(url) {
  return Boolean(url && /\.(jpe?g|png|webp|gif|avif)(\?|$)/i.test(url))
}

function uniqueSources(...sources) {
  return [...new Set(sources.filter(Boolean))]
}

export function imageSources(image) {
  return uniqueSources(assetUrl(image?.local), image?.url)
}

export function firstImageSources(item) {
  const first = item.images?.[0]
  if (first) return imageSources(first)

  const videoThumb = item.videos?.find((video) => isImageLikeUrl(video.url))
  return uniqueSources(videoThumb?.url)
}

export function mediaItems(item) {
  return [
    ...(item.images || []).map((image) => ({
      type: 'image',
      sources: imageSources(image),
      sourceUrl: image.url,
      label: `图片 ${image.index}`,
    })),
    ...(item.videos || []).map((video) => ({
      type: 'video-link',
      url: video.tweet_url || item.tweet_url,
      sources: isImageLikeUrl(video.url) ? uniqueSources(video.url) : [],
      label: `视频 ${video.index}`,
    })),
  ]
}
