/**
 * Favicon Utility - Dynamically load favicons from backend
 */

/**
 * Get the backend base URL from environment
 */
function getBackendUrl() {
  return import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
}

/**
 * Initialize favicons by adding link tags to document head
 * Favicons are served from backend /assets/favicons/ directory
 */
export function initializeFavicons() {
  const backendUrl = getBackendUrl()
  const faviconBase = `${backendUrl}/assets/favicons`

  const head = document.head

  // Apple Touch Icons
  const appleSizes = [57, 60, 72, 76, 114, 120, 144, 152, 180]
  appleSizes.forEach((size) => {
    const link = document.createElement('link')
    link.rel = 'apple-touch-icon'
    link.sizes = `${size}x${size}`
    link.href = `${faviconBase}/apple-icon-${size}x${size}.png`
    head.appendChild(link)
  })

  // Standard Favicons
  const faviconSizes = [
    { size: 192, name: 'android-icon-192x192.png' },
    { size: 32, name: 'favicon-32x32.png' },
    { size: 96, name: 'favicon-96x96.png' },
    { size: 16, name: 'favicon-16x16.png' },
  ]

  faviconSizes.forEach(({ size, name }) => {
    const link = document.createElement('link')
    link.rel = 'icon'
    link.type = 'image/png'
    link.sizes = `${size}x${size}`
    link.href = `${faviconBase}/${name}`
    head.appendChild(link)
  })

  // ICO Favicon (for older browsers)
  const icoLink = document.createElement('link')
  icoLink.rel = 'shortcut icon'
  icoLink.href = `${faviconBase}/favicon.ico`
  head.appendChild(icoLink)

  // Web App Manifest
  const manifestLink = document.createElement('link')
  manifestLink.rel = 'manifest'
  manifestLink.href = `${faviconBase}/manifest.json`
  head.appendChild(manifestLink)

  // Microsoft Tile Meta Tags
  const tileColorMeta = document.createElement('meta')
  tileColorMeta.name = 'msapplication-TileColor'
  tileColorMeta.content = '#ffffff'
  head.appendChild(tileColorMeta)

  const tileImageMeta = document.createElement('meta')
  tileImageMeta.name = 'msapplication-TileImage'
  tileImageMeta.content = `${faviconBase}/ms-icon-144x144.png`
  head.appendChild(tileImageMeta)

  // Theme Color
  const themeColorMeta = document.createElement('meta')
  themeColorMeta.name = 'theme-color'
  themeColorMeta.content = '#ffffff'
  head.appendChild(themeColorMeta)
}
