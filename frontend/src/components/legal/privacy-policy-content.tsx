export function PrivacyPolicyContent( )
{
	return (
		<article className='prose-legal max-w-3xl'>
			<p className='text-sm text-text-secondary'>Last updated: 19th August, 2026</p>

			<p>
				This Privacy Policy explains how NetLogAnalyser
				('we', 'us', 'our') collects, uses, and protects information when
				you use NetLogAnalyser (the 'Service').
			</p>

			<h2>1. Who we are</h2>
			<ul>
				<li><strong>Data controller:</strong> NetLogAnalyser</li>
				<li><strong>Contact:</strong> support@netloganalyser.com</li>
				<li>
					Our infrastructure runs on servers located in Germany
					(application) and the United Kingdom (database).
				</li>
			</ul>

			<h2>2. What data we collect</h2>

			<h3>2.1 Account data</h3>
			<p>
				When you register, we collect your email address, a display name,
				and a password, stored only as an Argon2id hash - we never store
				or can recover your plaintext password.
			</p>

			<h3>2.2 Authentication & session data</h3>
			<p>
				A refresh token (stored only as a SHA-256 hash) set in an httpOnly
				cookie, plus the IP address and user-agent of the device used to
				log in, kept for security auditing.
			</p>

			<h3>2.3 API keys</h3>
			<p>
				We store a SHA-256 hash of each API key and a short display
				prefix. The full key is shown once and never stored in
				recoverable form.
			</p>

			<h3>2.4 Network log data you submit</h3>
			<p>
				The Service ingests network packet metadata that you submit via
				the API - source/destination IPs, ports, protocol, packet size,
				TCP flags, and any custom payload fields. We enrich this with a
				derived country code (via a local MaxMind GeoLite2 database) and
				an automatically computed anomaly score.
			</p>
			<p>
				<strong>Important:</strong> if the traffic you submit includes IP
				addresses belonging to other people, that data may itself be
				personal data. You are responsible for having a lawful basis to
				capture and submit it - see our Terms & Conditions.
			</p>

			<h3>2.5 Cookies</h3>
			<p>
				We use one cookie: the httpOnly refresh-token cookie described
				above. It is strictly necessary for keeping you logged in and is
				not used for tracking, advertising, or analytics.
			</p>

			<h2>3. Why we process this data</h2>
			<ul>
				<li>Account data - providing the Service (contract)</li>
				<li>Session data - security and staying logged in (contract / legitimate interest)</li>
				<li>API keys - authenticating ingest requests (contract)</li>
				<li>Submitted logs - providing the analytics/dashboard you asked for (contract)</li>
			</ul>

			<h2>4. Where your data is stored</h2>
			<ul>
				<li>Application servers: Hetzner, Germany</li>
				<li>Database: Neon (Postgres), United Kingdom</li>
				<li>Email delivery: Resend (verification & password-reset emails only)</li>
				<li>Edge/tunneling: Cloudflare</li>
			</ul>
			<p>
				If you are outside the EU/UK, your data will be transferred to
				and processed in the EU/UK.
			</p>

			<h2>5. How long we keep data</h2>
			<p>
				Networks logs are deleted every 30 days. Upon account deletion,
                all account data is deleted immediately, including logs and exports.
            </p>

			<h2>6. Your rights</h2>
			<p>
				If you are in the EEA, UK, or a similar jurisdiction, you can
				request access, correction, deletion, restriction, portability, or
				object to processing, and lodge a complaint with your local data
				protection authority. Contact support@netloganalyser.com to exercise these
				rights.
			</p>

			<h2>7. Security</h2>
			<p>
				Argon2id password hashing, SHA-256 hashed tokens/keys, HTTPS/TLS
				throughout, and security headers (CSP, HSTS, X-Frame-Options)
				on every response. No system is 100% secure.
			</p>

			<h2>8. Children's privacy</h2>
			<p>
				The Service is not directed at, and we do not knowingly collect
				data from, anyone under 16.
			</p>

			<h2>9. Changes to this policy</h2>
			<p>
				We may update this policy from time to time. Continued use after
				changes take effect constitutes acceptance.
			</p>

			<h2>10. Contact</h2>
			<p>Questions about this policy: support@netloganalyser.com.</p>
		</article>
	);
}