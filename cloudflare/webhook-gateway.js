/**
 * Cloudflare Worker for GitHub PR Webhook Gateway
 * Receives GitHub webhook events and routes them to the integrated system
 */

// Configuration
const CONFIG = {
  GITHUB_WEBHOOK_SECRET: 'your-webhook-secret', // Set in worker environment variables
  ALLOWED_EVENTS: [
    'pull_request',
    'pull_request_review',
    'push',
    'issues',
    'issue_comment'
  ],
  RATE_LIMIT: {
    MAX_REQUESTS: 100,
    WINDOW_MS: 60000 // 1 minute
  }
};

// Rate limiting using Durable Objects (simplified version)
class RateLimiter {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const key = `rate_limit:${ip}`;
    
    const current = await this.state.storage.get(key) || 0;
    
    if (current >= CONFIG.RATE_LIMIT.MAX_REQUESTS) {
      return new Response('Rate limit exceeded', { status: 429 });
    }
    
    await this.state.storage.put(key, current + 1, {
      expirationTtl: CONFIG.RATE_LIMIT.WINDOW_MS / 1000
    });
    
    return new Response('OK');
  }
}

/**
 * Verify GitHub webhook signature
 */
async function verifyGitHubSignature(request, body, secret) {
  const signature = request.headers.get('X-Hub-Signature-256');
  
  if (!signature) {
    return false;
  }
  
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const mac = await crypto.subtle.sign('HMAC', key, encoder.encode(body));
  const expectedSignature = 'sha256=' + Array.from(new Uint8Array(mac))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  
  return signature === expectedSignature;
}

/**
 * Process GitHub webhook event
 */
async function processGitHubEvent(eventType, payload) {
  const processedEvent = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    source: 'github',
    event_type: eventType,
    processed: false,
    metadata: {
      delivery_id: payload.headers?.['X-GitHub-Delivery'],
      hook_id: payload.headers?.['X-GitHub-Hook-ID']
    }
  };

  // Extract relevant information based on event type
  switch (eventType) {
    case 'pull_request':
      processedEvent.data = {
        action: payload.action,
        repository: {
          name: payload.repository.name,
          full_name: payload.repository.full_name,
          owner: payload.repository.owner.login,
          clone_url: payload.repository.clone_url,
          default_branch: payload.repository.default_branch
        },
        pull_request: {
          number: payload.pull_request.number,
          title: payload.pull_request.title,
          body: payload.pull_request.body,
          state: payload.pull_request.state,
          head: {
            ref: payload.pull_request.head.ref,
            sha: payload.pull_request.head.sha,
            repo: payload.pull_request.head.repo?.full_name
          },
          base: {
            ref: payload.pull_request.base.ref,
            sha: payload.pull_request.base.sha,
            repo: payload.pull_request.base.repo.full_name
          },
          user: {
            login: payload.pull_request.user.login,
            id: payload.pull_request.user.id
          },
          created_at: payload.pull_request.created_at,
          updated_at: payload.pull_request.updated_at,
          mergeable: payload.pull_request.mergeable,
          changed_files: payload.pull_request.changed_files,
          additions: payload.pull_request.additions,
          deletions: payload.pull_request.deletions
        }
      };
      break;

    case 'pull_request_review':
      processedEvent.data = {
        action: payload.action,
        repository: {
          name: payload.repository.name,
          full_name: payload.repository.full_name,
          owner: payload.repository.owner.login
        },
        pull_request: {
          number: payload.pull_request.number,
          title: payload.pull_request.title
        },
        review: {
          id: payload.review.id,
          state: payload.review.state,
          body: payload.review.body,
          user: {
            login: payload.review.user.login,
            id: payload.review.user.id
          },
          submitted_at: payload.review.submitted_at
        }
      };
      break;

    case 'push':
      processedEvent.data = {
        repository: {
          name: payload.repository.name,
          full_name: payload.repository.full_name,
          owner: payload.repository.owner.login
        },
        ref: payload.ref,
        before: payload.before,
        after: payload.after,
        commits: payload.commits.map(commit => ({
          id: commit.id,
          message: commit.message,
          author: commit.author,
          added: commit.added,
          removed: commit.removed,
          modified: commit.modified
        })),
        pusher: {
          name: payload.pusher.name,
          email: payload.pusher.email
        },
        head_commit: payload.head_commit
      };
      break;

    default:
      processedEvent.data = {
        action: payload.action,
        repository: payload.repository ? {
          name: payload.repository.name,
          full_name: payload.repository.full_name,
          owner: payload.repository.owner.login
        } : null,
        raw_payload: payload
      };
  }

  return processedEvent;
}

/**
 * Determine if event should trigger workflow
 */
function shouldTriggerWorkflow(eventType, eventData) {
  switch (eventType) {
    case 'pull_request':
      // Trigger on opened, synchronize, reopened, ready_for_review
      return ['opened', 'synchronize', 'reopened', 'ready_for_review'].includes(eventData.action);
    
    case 'pull_request_review':
      // Trigger on submitted reviews
      return eventData.action === 'submitted';
    
    case 'push':
      // Trigger on pushes to main/master branches or PR branches
      const ref = eventData.ref;
      return ref === 'refs/heads/main' || 
             ref === 'refs/heads/master' || 
             ref.startsWith('refs/heads/');
    
    default:
      return false;
  }
}

/**
 * Route event to appropriate handler
 */
async function routeEvent(processedEvent, env) {
  const routingDecisions = [];
  
  // Determine routing based on event characteristics
  if (processedEvent.event_type === 'pull_request') {
    const prData = processedEvent.data.pull_request;
    
    // Route to web-eval-agent if PR contains frontend changes
    if (prData.changed_files > 0) {
      routingDecisions.push({
        service: 'web-eval-agent',
        priority: 'high',
        reason: 'PR contains file changes requiring UI validation'
      });
    }
    
    // Route to graph-sitter for code analysis
    routingDecisions.push({
      service: 'graph-sitter',
      priority: 'high',
      reason: 'Code analysis required for PR'
    });
    
    // Route to grainchain for sandbox testing
    if (prData.additions > 10 || prData.deletions > 10) {
      routingDecisions.push({
        service: 'grainchain',
        priority: 'medium',
        reason: 'Significant code changes require sandbox testing'
      });
    }
    
    // Route to codegen for intelligent analysis
    routingDecisions.push({
      service: 'codegen',
      priority: 'medium',
      reason: 'AI analysis of PR changes'
    });
  }
  
  // Store event and routing decisions
  const eventRecord = {
    ...processedEvent,
    routing_decisions: routingDecisions,
    workflow_triggered: shouldTriggerWorkflow(processedEvent.event_type, processedEvent.data)
  };
  
  // Store in KV for processing by the main system
  await env.WEBHOOK_EVENTS.put(
    `event:${processedEvent.id}`,
    JSON.stringify(eventRecord),
    { expirationTtl: 86400 } // 24 hours
  );
  
  return eventRecord;
}

/**
 * Main request handler
 */
async function handleRequest(request, env, ctx) {
  const url = new URL(request.url);
  
  // Health check endpoint
  if (url.pathname === '/health') {
    return new Response(JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Webhook endpoint
  if (url.pathname === '/webhook' && request.method === 'POST') {
    try {
      // Rate limiting check
      const rateLimitResult = await env.RATE_LIMITER.fetch(request);
      if (rateLimitResult.status === 429) {
        return new Response('Rate limit exceeded', { status: 429 });
      }
      
      // Get request body
      const body = await request.text();
      const eventType = request.headers.get('X-GitHub-Event');
      
      // Verify GitHub signature if secret is configured
      if (env.GITHUB_WEBHOOK_SECRET) {
        const isValid = await verifyGitHubSignature(request, body, env.GITHUB_WEBHOOK_SECRET);
        if (!isValid) {
          return new Response('Invalid signature', { status: 401 });
        }
      }
      
      // Check if event type is allowed
      if (!CONFIG.ALLOWED_EVENTS.includes(eventType)) {
        return new Response(`Event type ${eventType} not supported`, { status: 400 });
      }
      
      // Parse payload
      let payload;
      try {
        payload = JSON.parse(body);
        payload.headers = Object.fromEntries(request.headers.entries());
      } catch (e) {
        return new Response('Invalid JSON payload', { status: 400 });
      }
      
      // Process the event
      const processedEvent = await processGitHubEvent(eventType, payload);
      
      // Route the event
      const eventRecord = await routeEvent(processedEvent, env);
      
      // Log the event
      console.log(`Processed GitHub event: ${eventType}`, {
        event_id: processedEvent.id,
        repository: eventRecord.data.repository?.full_name,
        workflow_triggered: eventRecord.workflow_triggered,
        routing_decisions: eventRecord.routing_decisions.length
      });
      
      // Return success response
      return new Response(JSON.stringify({
        success: true,
        event_id: processedEvent.id,
        event_type: eventType,
        workflow_triggered: eventRecord.workflow_triggered,
        routing_decisions: eventRecord.routing_decisions.length,
        timestamp: processedEvent.timestamp
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
      
    } catch (error) {
      console.error('Error processing webhook:', error);
      return new Response(JSON.stringify({
        success: false,
        error: 'Internal server error',
        timestamp: new Date().toISOString()
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
  
  // Events API endpoint for retrieving processed events
  if (url.pathname === '/events' && request.method === 'GET') {
    try {
      const limit = parseInt(url.searchParams.get('limit') || '10');
      const eventType = url.searchParams.get('type');
      const repository = url.searchParams.get('repository');
      
      // This is a simplified implementation
      // In production, you'd want proper pagination and filtering
      const events = [];
      const listResult = await env.WEBHOOK_EVENTS.list({ limit });
      
      for (const key of listResult.keys) {
        const eventData = await env.WEBHOOK_EVENTS.get(key.name);
        if (eventData) {
          const event = JSON.parse(eventData);
          
          // Apply filters
          if (eventType && event.event_type !== eventType) continue;
          if (repository && event.data.repository?.full_name !== repository) continue;
          
          events.push(event);
        }
      }
      
      return new Response(JSON.stringify({
        events,
        total: events.length,
        timestamp: new Date().toISOString()
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
      
    } catch (error) {
      console.error('Error retrieving events:', error);
      return new Response(JSON.stringify({
        success: false,
        error: 'Failed to retrieve events'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
  
  // Default response
  return new Response('Webhook Gateway - GitHub Integration', { status: 200 });
}

// Export the worker
export default {
  async fetch(request, env, ctx) {
    return handleRequest(request, env, ctx);
  }
};

// Export Durable Object for rate limiting
export { RateLimiter };
