// ── Health check ─────────────────────────────────────────────────────────
async function checkHealth( )
{
    try
    {
        const res = await fetch( '/health' );
        const data = await res.json( );

        const apiDot    = document.getElementById( 'apiDot' );
        const dbDot     = document.getElementById( 'dbDot' );
        const apiStatus = document.getElementById( 'apiStatus' );
        const dbStatus  = document.getElementById( 'dbStatus' );
        const tag       = document.getElementById( 'envTag' );

        apiDot.className = 'status-dot ok';
        apiStatus.textContent = 'operational';

        if ( data.database === 'ok' )
        {
            dbDot.className = 'status-dot ok';
            dbStatus.textContent = 'connected';
        }
        else
        {
            dbDot.className = 'status-dot err';
            dbStatus.textContent = 'unreachable';
        }

        if ( data.version )
        {
            document.getElementById( 'versionValue' ).textContent = `v${ data.version }`;
        }

        if ( data.uptime_seconds != null )
        {
            document.getElementById( 'uptimeValue' ).textContent = formatUptime( data.uptime_seconds );
        }

        if ( data.environment === "production" )
        {
            tag.textContent = 'production';
            tag.classList.remove( 'dev' );
            tag.classList.add( 'prod' );
            document.getElementById( 'baseUrl' ).textContent = window.location.origin;
        }
    }
    catch
    {
        document.getElementById( 'apiDot' ).className = 'status-dot err';
        document.getElementById( 'apiStatus' ).textContent = 'unreachable';
        document.getElementById( 'dbDot' ).className = 'status-dot err';
        document.getElementById( 'dbStatus' ).textContent = 'unknown';
    }
}

function formatUptime( seconds )
{
    if ( seconds < 60 ) return `${ Math.floor( seconds ) }s`;
    if ( seconds < 3600 ) return `${ Math.floor( seconds / 60 ) }m`;
    return `${ Math.floor( seconds / 3600 ) }h ${ Math.floor( ( seconds % 3600 ) / 60 ) }m`;
}

checkHealth( );

// ── Copy base URL ─────────────────────────────────────────────────────────
function copyUrl( )
{
    const url = document.getElementById( 'baseUrl' ).textContent;
    navigator.clipboard.writeText( url ).then( ( ) =>
    {
        const btn = document.querySelector( '.copy-btn' );
        btn.textContent = 'copied';
        setTimeout( ( ) => { btn.textContent = 'copy'; }, 1800 );
    } );
}

// ── Code tabs ─────────────────────────────────────────────────────────────
const snippets = {
    python: `<span class="c-kw">import</span> requests
<span class="c-kw">from</span> datetime <span class="c-kw">import</span> datetime, timezone

url     = <span class="c-str">"http://localhost:8000/ingest"</span>
headers = {<span class="c-str">"X-API-Key"</span>: <span class="c-str">"nw_live_your_key_here"</span>}

<span class="c-cm"># Send a batch of log entries - always batch, never one at a time.</span>
payload = [
    {
        <span class="c-key">"src_ip"</span>:           <span class="c-str">"192.168.1.1"</span>,
        <span class="c-key">"dst_ip"</span>:           <span class="c-str">"10.0.0.1"</span>,
        <span class="c-key">"src_port"</span>:         <span class="c-num">52341</span>,
        <span class="c-key">"dst_port"</span>:         <span class="c-num">443</span>,
        <span class="c-key">"protocol"</span>:         <span class="c-str">"TCP"</span>,
        <span class="c-key">"packet_size_bytes"</span>: <span class="c-num">128</span>,
        <span class="c-key">"captured_at"</span>:      datetime.now(timezone.utc).isoformat(),
    }
]

response = requests.<span class="c-fn">post</span>(url, json=payload, headers=headers)
<span class="c-fn">print</span>(response.json())  <span class="c-cm"># {"ingested": 1, "anomalies_detected": 0}</span>`,

    curl: `<span class="c-cm"># Send a single log entry as a JSON batch</span>
curl -X POST http://localhost:8000/ingest \\
    -H <span class="c-str">"X-API-Key: nw_live_your_key_here"</span> \\
    -H <span class="c-str">"Content-Type: application/json"</span> \\
    -d <span class="c-str">'[
        {
            "src_ip":           "192.168.1.1",
            "dst_ip":           "10.0.0.1",
            "src_port":         52341,
            "dst_port":         443,
            "protocol":         "TCP",
            "packet_size_bytes": 128,
            "captured_at":      "2026-06-15T14:32:07Z"
        }
    ]'</span>`,

    node: `<span class="c-kw">const</span> response = <span class="c-kw">await</span> <span class="c-fn">fetch</span>(<span class="c-str">"http://localhost:8000/ingest"</span>, {
    method:  <span class="c-str">"POST"</span>,
    headers: {
        <span class="c-str">"X-API-Key"</span>:     <span class="c-str">"nw_live_your_key_here"</span>,
        <span class="c-str">"Content-Type"</span>:  <span class="c-str">"application/json"</span>,
    },
    body: JSON.<span class="c-fn">stringify</span>([
        {
            src_ip:           <span class="c-str">"192.168.1.1"</span>,
            dst_ip:           <span class="c-str">"10.0.0.1"</span>,
            src_port:         <span class="c-num">52341</span>,
            dst_port:         <span class="c-num">443</span>,
            protocol:         <span class="c-str">"TCP"</span>,
            packet_size_bytes: <span class="c-num">128</span>,
            captured_at:      <span class="c-kw">new</span> <span class="c-fn">Date</span>().toISOString(),
        },
    ]),
});

<span class="c-kw">const</span> data = <span class="c-kw">await</span> response.<span class="c-fn">json</span>();
console.<span class="c-fn">log</span>(data); <span class="c-cm">// { ingested: 1, anomalies_detected: 0 }</span>`,
};

const plainSnippets = {
    python: `import requests\nfrom datetime import datetime, timezone\n\nurl     = "http://localhost:8000/ingest"\nheaders = {"X-API-Key": "nw_live_your_key_here"}\n\npayload = [\n    {\n        "src_ip":           "192.168.1.1",\n        "dst_ip":           "10.0.0.1",\n        "src_port":         52341,\n        "dst_port":         443,\n        "protocol":         "TCP",\n        "packet_size_bytes": 128,\n        "captured_at":      datetime.now(timezone.utc).isoformat(),\n    }\n]\n\nresponse = requests.post(url, json=payload, headers=headers)`,
    curl: `curl -X POST http://localhost:8000/ingest \\\n  -H "X-API-Key: nw_live_your_key_here" \\\n  -H "Content-Type: application/json" \\\n  -d '[{"src_ip":"192.168.1.1","dst_ip":"10.0.0.1","src_port":52341,"dst_port":443,"protocol":"TCP","packet_size_bytes":128,"captured_at":"2026-06-15T14:32:07Z"}]'`,
    node: `const response = await fetch("http://localhost:8000/ingest", {\n  method: "POST",\n  headers: { "X-API-Key": "nw_live_your_key_here", "Content-Type": "application/json" },\n  body: JSON.stringify([{ src_ip: "192.168.1.1", dst_ip: "10.0.0.1", src_port: 52341, dst_port: 443, protocol: "TCP", packet_size_bytes: 128, captured_at: new Date().toISOString() }]),\n});`,
};

let activeTab = 'python';

function setTab( lang, el )
{
    activeTab = lang;
    document.getElementById( 'codeBlock' ).innerHTML = snippets[ lang ];
    document.querySelectorAll( '.code-tab' ).forEach( t => t.classList.remove( 'active' ));
    el.classList.add( 'active' );
    document.getElementById( 'copyCodeBtn' ).textContent = 'copy';
}

function copyCode( )
{
    navigator.clipboard.writeText( plainSnippets[ activeTab ] ).then( ( ) =>
    {
        const btn = document.getElementById( 'copyCodeBtn' );
        btn.textContent = 'copied';
        setTimeout( ( ) => { btn.textContent = 'copy'; }, 1800 );
    } );
}

function initLandingPage( )
{
    const copyBtn = document.querySelector( ".copy-btn" );
    copyBtn.addEventListener( "click", copyUrl );

    const tabBtns = document.querySelectorAll( ".code-tab" );
    tabBtns.forEach( btn =>
    {
        btn.addEventListener( "click", function( )
        {
            setTab( btn.dataset.type, btn );
        } );
    } )

    const copyCodeBtn = document.getElementById( "copyCodeBtn" );
    copyCodeBtn.addEventListener( "click", copyCode );
}

window.addEventListener( "DOMContentLoaded", initLandingPage );