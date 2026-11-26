const RUNPOD_ROUTE = '/api/runpod';
const RUNPOD_STATUS_PREFIX = '/api/runpod/status/';
const RUNPOD_CANCEL_PREFIX = '/api/runpod/cancel/';
const RUNPOD_AUDIO_ROUTE = '/api/runpod/audio';
const RUNPOD_STORED_AUDIO_PREFIX = '/api/runpod/stored-audio/';
// Must match RUNPOD_AUDIO_UPLOAD_PREFIX on the RunPod worker (tts/runpod.py).
const DEFAULT_AUDIO_UPLOAD_PREFIX = 'tts-audio';
const JOB_ID_PATTERN = /^[A-Za-z0-9._-]{1,128}$/;
// RunPod's endpoint default is 10 minutes, too short for long texts. Override with RUNPOD_EXECUTION_TIMEOUT_MS.
const DEFAULT_EXECUTION_TIMEOUT_MS = 30 * 60 * 1000;

const readExecutionTimeoutMs = (env) => {
  const value = Number(env.RUNPOD_EXECUTION_TIMEOUT_MS);
  return Number.isFinite(value) && value > 0 ? Math.floor(value) : DEFAULT_EXECUTION_TIMEOUT_MS;
};

const parseAllowedOrigins = (value) =>
  String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const isOriginAllowed = (origin, allowedOrigins) =>
  !origin || allowedOrigins.length === 0 || allowedOrigins.includes(origin);

const buildCorsHeaders = (origin, allowedOrigins) => {
  const allowOrigin = origin && allowedOrigins.length > 0
    ? origin
    : allowedOrigins[0] || '*';

  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
};

const jsonResponse = (payload, status, corsHeaders) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
    },
  });

const parseJsonSafe = async (response) => {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return { error: await response.text() };
};

const extractStatusJobId = (pathname) => {
  if (!pathname.startsWith(RUNPOD_STATUS_PREFIX)) return null;
  const rawId = pathname.slice(RUNPOD_STATUS_PREFIX.length);
  if (!rawId) return null;
  try {
    return decodeURIComponent(rawId);
  } catch {
    return null;
  }
};

const extractCancelJobId = (pathname) => {
  if (!pathname.startsWith(RUNPOD_CANCEL_PREFIX)) return null;
  const rawId = pathname.slice(RUNPOD_CANCEL_PREFIX.length);
  if (!rawId) return null;
  try {
    return decodeURIComponent(rawId);
  } catch {
    return null;
  }
};

const extractStoredAudioJobId = (pathname) => {
  if (!pathname.startsWith(RUNPOD_STORED_AUDIO_PREFIX)) return null;
  const rawId = pathname.slice(RUNPOD_STORED_AUDIO_PREFIX.length);
  return JOB_ID_PATTERN.test(rawId) ? rawId : null;
};

const STORED_AUDIO_SUFFIX_PATTERN = /^[0-9a-f]{8}\.wav$/;

// The RunPod worker uploads results over 6.5 MB as <prefix>/<job id>-<8 hex>.wav.
// RunPod forgets finished jobs after a while; this finds the upload by job ID.
const findStoredAudio = async (bucket, prefix, jobId) => {
  const keyPrefix = `${prefix}/${jobId}-`;
  const listing = await bucket.list({ prefix: keyPrefix });
  const matches = listing.objects
    .filter((object) => STORED_AUDIO_SUFFIX_PATTERN.test(object.key.slice(keyPrefix.length)))
    .sort((a, b) => b.uploaded - a.uploaded);
  return matches[0] ? bucket.get(matches[0].key) : null;
};

const parseHttpUrl = (value) => {
  const candidate = String(value || '').trim();
  if (!candidate) return null;
  try {
    const parsed = new URL(candidate);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
      ? parsed.toString()
      : null;
  } catch {
    return null;
  }
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const allowedOrigins = parseAllowedOrigins(env.ALLOWED_ORIGIN);

    if (!isOriginAllowed(origin, allowedOrigins)) {
      return new Response('Forbidden', { status: 403 });
    }

    const corsHeaders = buildCorsHeaders(origin, allowedOrigins);

    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders,
      });
    }

    const storedAudioJobId = extractStoredAudioJobId(url.pathname);
    if (request.method === 'GET' && storedAudioJobId) {
      if (!env.AUDIO_BUCKET) {
        return jsonResponse({ error: 'Audio bucket is not bound' }, 501, corsHeaders);
      }
      try {
        const prefix = String(env.RUNPOD_AUDIO_UPLOAD_PREFIX || DEFAULT_AUDIO_UPLOAD_PREFIX).replace(/\/+$/, '');
        const object = await findStoredAudio(env.AUDIO_BUCKET, prefix, storedAudioJobId);
        if (!object) {
          return jsonResponse({ error: 'Stored audio not found' }, 404, corsHeaders);
        }
        return new Response(object.body, {
          status: 200,
          headers: {
            ...corsHeaders,
            'Content-Type': 'audio/wav',
            'Content-Length': String(object.size),
            'Cache-Control': 'no-store',
          },
        });
      } catch (error) {
        return jsonResponse(
          { error: 'Stored audio lookup failed', details: String(error) },
          500,
          corsHeaders
        );
      }
    }

    const statusJobId = extractStatusJobId(url.pathname);
    const cancelJobId = extractCancelJobId(url.pathname);
    if (request.method === 'GET' && statusJobId) {
      try {
        const runpodResponse = await fetch(
          `https://api.runpod.ai/v2/${env.RUNPOD_ENDPOINT_ID}/status/${encodeURIComponent(statusJobId)}`,
          {
            method: 'GET',
            headers: {
              Authorization: `Bearer ${env.RUNPOD_API_KEY}`,
            },
          }
        );

        const responseBody = await parseJsonSafe(runpodResponse);
        return jsonResponse(responseBody, runpodResponse.status, corsHeaders);
      } catch (error) {
        return jsonResponse(
          { error: 'Status request failed', details: String(error) },
          500,
          corsHeaders
        );
      }
    }

    if (request.method === 'POST' && cancelJobId) {
      try {
        const runpodResponse = await fetch(
          `https://api.runpod.ai/v2/${env.RUNPOD_ENDPOINT_ID}/cancel/${encodeURIComponent(cancelJobId)}`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${env.RUNPOD_API_KEY}`,
            },
          }
        );

        const responseBody = await parseJsonSafe(runpodResponse);
        return jsonResponse(responseBody, runpodResponse.status, corsHeaders);
      } catch (error) {
        return jsonResponse(
          { error: 'Cancel request failed', details: String(error) },
          500,
          corsHeaders
        );
      }
    }

    if (request.method === 'GET' && url.pathname === RUNPOD_AUDIO_ROUTE) {
      const audioUrl = parseHttpUrl(url.searchParams.get('url'));
      if (!audioUrl) {
        return jsonResponse({ error: 'Invalid audio URL' }, 400, corsHeaders);
      }

      try {
        const upstreamResponse = await fetch(audioUrl, { method: 'GET' });
        if (!upstreamResponse.ok) {
          const details = await upstreamResponse.text().catch(() => '');
          return jsonResponse(
            {
              error: 'Audio fetch failed',
              status: upstreamResponse.status,
              details: details ? details.slice(0, 500) : undefined,
            },
            502,
            corsHeaders
          );
        }

        const responseHeaders = {
          ...corsHeaders,
          'Content-Type': upstreamResponse.headers.get('Content-Type') || 'application/octet-stream',
          'Cache-Control': 'no-store',
        };
        const contentLength = upstreamResponse.headers.get('Content-Length');
        if (contentLength) {
          responseHeaders['Content-Length'] = contentLength;
        }

        return new Response(upstreamResponse.body, {
          status: 200,
          headers: responseHeaders,
        });
      } catch (error) {
        return jsonResponse(
          { error: 'Audio proxy fetch failed', details: String(error) },
          500,
          corsHeaders
        );
      }
    }

    if (request.method === 'POST' && url.pathname === RUNPOD_ROUTE) {
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResponse({ error: 'Invalid JSON body' }, 400, corsHeaders);
      }

      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        return jsonResponse({ error: 'JSON body must be an object' }, 400, corsHeaders);
      }

      try {
        const runpodResponse = await fetch(
          `https://api.runpod.ai/v2/${env.RUNPOD_ENDPOINT_ID}/run`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${env.RUNPOD_API_KEY}`,
            },
            // The Worker sets the policy so browsers cannot request longer GPU time.
            body: JSON.stringify({
              ...body,
              policy: { executionTimeout: readExecutionTimeoutMs(env) },
            }),
          }
        );

        const responseBody = await parseJsonSafe(runpodResponse);
        return jsonResponse(responseBody, runpodResponse.status, corsHeaders);
      } catch (error) {
        return jsonResponse(
          { error: 'RunPod submit failed', details: String(error) },
          500,
          corsHeaders
        );
      }
    }

    return new Response('Not Found', { status: 404, headers: corsHeaders });
  },
};
