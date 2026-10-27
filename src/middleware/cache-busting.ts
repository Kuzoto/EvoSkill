// Cache-busting middleware for API responses
export function cacheBustingMiddleware(context, next) {
  const response = next(context)

  // Add cache headers for API responses
  if (context.req.accepts('application/json')) {
    response.header('Cache-Control', 'public, max-age=3600, s-maxage=86400, immutable')
    response.header('Surrogate-Control', 'source=cdn')

    // Add cache-busting query parameter if needed
    const url = context.resolvedUrl
    const cacheBuster = new URLSearchParams({
      t: Date.now().toString()
    }).toString()
    response.header('Cache-Tags', `api-${url}${cacheBuster}`)
  }

  return response
}

export default cacheBustingMiddleware
